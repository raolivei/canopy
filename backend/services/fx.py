"""Foreign exchange service for Canopy (CAD + USD only).

Canopy is a Canadian investment tracker scoped to CAD and USD. The sole
FX pair we care about is ``USDCAD`` (how many CAD per 1 USD), which the
Bank of Canada publishes daily as the ``FXUSDCAD`` series via the free
Valet API:

    https://www.bankofcanada.ca/valet/observations/FXUSDCAD/json

Design notes
------------

* **No API key**. BoC Valet is a public government endpoint.
* **Daily granularity**. That's all BoC publishes (no intraday), which
  is exactly what Questrade uses for combined statements too.
* **Historical rate-of-day**. Timeline aggregations convert each
  ``AccountBalanceHistory`` point at the rate for that date. When the
  exact date isn't in the table (weekends / holidays / stale cache), we
  fall back to the most-recent prior observation.
* **Fail-safe**. All network code degrades gracefully: a failed BoC
  fetch does not raise; callers check ``is_stale`` and surface a banner
  to the user.

The service exposes a narrow public surface:

* :func:`ensure_latest_rate_cached` — lazy-warms today's rate.
* :func:`get_latest_rate` — single-row lookup of newest cached rate.
* :func:`get_rate_on` — rate for a given date, with prior-close fallback.
* :func:`convert` — arithmetic helper around CAD <-> USD.
* :func:`backfill_rates` — one-shot bulk fetch for historical range.

There is no global cache: callers pass a live session and reads are
straight SQL. The service is safe to call from many request handlers
concurrently; UPSERTs are gated by the ``uq_fx_rates_pair_date``
constraint.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from typing import Iterable, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.db.models.fx_rate import FxRate

logger = logging.getLogger(__name__)

# The BoC Valet series code for "US dollar, noon rate, Canadian dollars
# per US dollar". (FXUSDCAD is the successor to FXUSDCAD_NOON; both are
# the same value going forward.)
BOC_SERIES = "FXUSDCAD"
BOC_BASE = f"https://www.bankofcanada.ca/valet/observations/{BOC_SERIES}/json"
BOC_SOURCE = "bank_of_canada"
DEFAULT_PAIR = "USDCAD"
# How old "latest" can be before the frontend shows a stale banner.
# BoC doesn't publish on weekends / Canadian holidays, so 3 days is a
# safe threshold (Fri close is readable through Monday morning).
STALE_AFTER_DAYS = 3


# ---------------------------------------------------------------------------
# Lookup
# ---------------------------------------------------------------------------


def get_latest_rate(db: Session, pair: str = DEFAULT_PAIR) -> Optional[FxRate]:
    """Return the most-recently observed row for ``pair``, or ``None``."""
    return (
        db.execute(
            select(FxRate)
            .where(FxRate.pair == pair)
            .order_by(FxRate.as_of_date.desc())
            .limit(1)
        )
        .scalars()
        .first()
    )


def get_rate_on(
    db: Session, on_date: date, pair: str = DEFAULT_PAIR
) -> Optional[Decimal]:
    """Return the rate for ``pair`` on ``on_date``.

    If there is no exact match (weekends / holidays / gaps), return the
    most-recent prior observation. Returns ``None`` when the table has
    nothing <= ``on_date``.
    """
    row = (
        db.execute(
            select(FxRate)
            .where(FxRate.pair == pair, FxRate.as_of_date <= on_date)
            .order_by(FxRate.as_of_date.desc())
            .limit(1)
        )
        .scalars()
        .first()
    )
    return row.rate if row is not None else None


def is_stale(rate_row: Optional[FxRate], today: Optional[date] = None) -> bool:
    """Return True if ``rate_row`` is older than :data:`STALE_AFTER_DAYS`.

    A missing row is considered stale. ``today`` is injectable for
    tests; production callers should pass ``date.today()`` or omit.
    """
    today = today or date.today()
    if rate_row is None:
        return True
    return (today - rate_row.as_of_date).days > STALE_AFTER_DAYS


# ---------------------------------------------------------------------------
# Conversion
# ---------------------------------------------------------------------------


def convert(
    amount: Decimal,
    *,
    from_ccy: str,
    to_ccy: str,
    usd_cad_rate: Decimal,
) -> Decimal:
    """Convert ``amount`` between CAD and USD using a known USD/CAD rate.

    ``usd_cad_rate`` is "1 USD in CAD" — the way BoC publishes it. So:

    * CAD -> USD:  amount / rate
    * USD -> CAD:  amount * rate
    * Same-currency: passthrough.

    Raises ``ValueError`` for any currency outside {CAD, USD}.
    """
    from_ccy = (from_ccy or "").upper()
    to_ccy = (to_ccy or "").upper()
    if from_ccy not in {"CAD", "USD"} or to_ccy not in {"CAD", "USD"}:
        raise ValueError(
            f"convert() only supports CAD + USD; got from={from_ccy} to={to_ccy}"
        )
    if from_ccy == to_ccy:
        return amount
    if usd_cad_rate is None or usd_cad_rate == 0:
        raise ValueError("usd_cad_rate is required for cross-currency conversion")
    if from_ccy == "USD" and to_ccy == "CAD":
        return amount * usd_cad_rate
    # CAD -> USD
    return amount / usd_cad_rate


# ---------------------------------------------------------------------------
# Warm / refresh from Bank of Canada
# ---------------------------------------------------------------------------


def ensure_latest_rate_cached(
    db: Session,
    *,
    http_get=None,
    pair: str = DEFAULT_PAIR,
) -> Optional[FxRate]:
    """Return the latest cached rate, fetching from BoC if it's stale.

    ``http_get`` is injected for tests; it takes a URL and returns the
    decoded JSON dict. If the BoC fetch fails for any reason, we fall
    back to whatever is cached (possibly stale, possibly nothing).
    """
    latest = get_latest_rate(db, pair=pair)
    if latest is not None and not is_stale(latest):
        return latest

    fetched = _fetch_boc_observations(n_recent=5, http_get=http_get)
    if fetched:
        _upsert_rates(db, fetched, pair=pair)
        db.flush()
        latest = get_latest_rate(db, pair=pair)
    return latest


def backfill_rates(
    db: Session,
    *,
    start_date: date,
    end_date: Optional[date] = None,
    http_get=None,
    pair: str = DEFAULT_PAIR,
) -> int:
    """Bulk-fetch a BoC date range and UPSERT it.

    Returns the number of observations written (new + updated).
    """
    end_date = end_date or date.today()
    fetched = _fetch_boc_observations(
        start_date=start_date, end_date=end_date, http_get=http_get
    )
    if not fetched:
        return 0
    _upsert_rates(db, fetched, pair=pair)
    db.flush()
    return len(fetched)


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


def _fetch_boc_observations(
    *,
    n_recent: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    http_get=None,
) -> list[tuple[date, Decimal]]:
    """Return a list of ``(date, rate)`` tuples fetched from BoC.

    Exactly one of ``n_recent`` or ``start_date`` must be provided.
    Returns an empty list on any error; the caller should not treat a
    missed fetch as fatal.
    """
    if n_recent is not None:
        url = f"{BOC_BASE}?recent={int(n_recent)}"
    elif start_date is not None:
        url = f"{BOC_BASE}?start_date={start_date.isoformat()}"
        if end_date is not None:
            url += f"&end_date={end_date.isoformat()}"
    else:
        raise ValueError("Must pass either n_recent or start_date")

    fetcher = http_get or _default_http_get
    try:
        payload = fetcher(url)
    except Exception as exc:  # noqa: BLE001 - any network error is non-fatal
        logger.warning("FX fetch from Bank of Canada failed: %s", exc)
        return []

    return list(_parse_boc_payload(payload))


def _parse_boc_payload(payload: dict) -> Iterable[tuple[date, Decimal]]:
    """Yield ``(date, rate)`` tuples from a BoC Valet JSON response."""
    observations = payload.get("observations") if payload else None
    if not observations:
        return
    for obs in observations:
        d_str = obs.get("d")
        if not d_str:
            continue
        try:
            parsed_date = date.fromisoformat(d_str)
        except ValueError:
            logger.debug("Skipping BoC observation with bad date: %r", d_str)
            continue
        series = obs.get(BOC_SERIES) or {}
        value_str = series.get("v")
        if not value_str:
            continue
        try:
            rate = Decimal(str(value_str))
        except (InvalidOperation, TypeError):
            logger.debug("Skipping BoC observation with bad value: %r", value_str)
            continue
        yield parsed_date, rate


def _default_http_get(url: str) -> dict:
    """Fetch ``url`` and JSON-decode it (stdlib only).

    Kept small and dependency-free so the FX service stays lightweight.
    Wrapped in :func:`_fetch_boc_observations` which catches any
    exception this raises.
    """
    with urllib.request.urlopen(url, timeout=10) as resp:  # noqa: S310 - trusted gov URL
        body = resp.read().decode("utf-8")
    return json.loads(body)


def _upsert_rates(
    db: Session,
    observations: list[tuple[date, Decimal]],
    *,
    pair: str,
) -> None:
    """Insert or update FX observations, one row per (pair, date)."""
    if not observations:
        return
    dates = [d for d, _ in observations]
    existing = {
        (r.pair, r.as_of_date): r
        for r in db.execute(
            select(FxRate).where(
                FxRate.pair == pair,
                FxRate.as_of_date.in_(dates),
            )
        ).scalars()
    }
    for observed_on, rate in observations:
        key = (pair, observed_on)
        row = existing.get(key)
        if row is None:
            db.add(
                FxRate(
                    pair=pair,
                    as_of_date=observed_on,
                    rate=rate,
                    source=BOC_SOURCE,
                )
            )
        else:
            # Update rate + source if BoC ever corrects an observation.
            row.rate = rate
            row.source = BOC_SOURCE


# ---------------------------------------------------------------------------
# Helpers for view conversion (used by accounts / networth aggregators)
# ---------------------------------------------------------------------------


def usd_amount_to_cad(amount: Decimal, usd_cad_rate: Optional[Decimal]) -> Decimal:
    """Convert USD -> CAD with a guarded fallback.

    When ``usd_cad_rate`` is ``None`` (no FX known at all), returns
    ``Decimal("0")`` so aggregations don't explode. Callers should have
    surfaced a banner already in that case.
    """
    if usd_cad_rate is None or usd_cad_rate == 0:
        return Decimal("0")
    return amount * usd_cad_rate


def cad_amount_to_usd(amount: Decimal, usd_cad_rate: Optional[Decimal]) -> Decimal:
    """Convert CAD -> USD with a guarded fallback (see :func:`usd_amount_to_cad`)."""
    if usd_cad_rate is None or usd_cad_rate == 0:
        return Decimal("0")
    return amount / usd_cad_rate
