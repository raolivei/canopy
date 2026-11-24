"""Currency exchange ledger: CRUD plus per-pair stats.

Exchanges are a standalone log (no ``Transaction`` rows). CAD<->USD rows are
benchmarked against the cached Bank of Canada USDCAD rate; other pairs get no
benchmark and never a fallback rate (see docs/CALCULATION_CONTRACT.md).
"""

from __future__ import annotations

import bisect
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from backend.db.models.asset import Asset
from backend.db.models.exchange import Exchange
from backend.db.models.fx_rate import FxRate
from backend.models.exchange import ExchangeCreate, ExchangeUpdate
from backend.services import fx
from backend.services.calculation.money import FxQuote, quantize
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

ZERO = Decimal("0")
BENCHMARK_LOOKBACK = timedelta(days=10)


class ExchangeNotFound(LookupError):
    pass


class InvalidExchange(ValueError):
    pass


@dataclass(frozen=True)
class Filters:
    date_from: date | None = None
    date_to: date | None = None
    provider: str | None = None
    currency: str | None = None


def _check_assets(db: Session, *asset_ids: int | None) -> None:
    for asset_id in asset_ids:
        if asset_id is not None and db.get(Asset, asset_id) is None:
            raise InvalidExchange(f"Unknown asset id {asset_id}")


def _check_record(exchange: Exchange) -> None:
    if exchange.from_currency == exchange.to_currency:
        raise InvalidExchange("from_currency and to_currency must differ")
    if exchange.fee_amount is not None and exchange.fee_currency is None:
        # A fee with no currency is almost always charged in the source currency.
        exchange.fee_currency = exchange.from_currency
    if exchange.fee_amount is None:
        exchange.fee_currency = None


class BenchmarkRates:
    """In-memory USDCAD lookup for a date range (one query, no N+1)."""

    def __init__(self, db: Session, start: date, end: date, pair: str = fx.DEFAULT_PAIR) -> None:
        rows = db.execute(
            select(FxRate)
            .where(FxRate.pair == pair, FxRate.as_of_date >= start - BENCHMARK_LOOKBACK, FxRate.as_of_date <= end)
            .order_by(FxRate.as_of_date)
        ).scalars()
        self._rows = list(rows)
        self._dates = [r.as_of_date for r in self._rows]

    def on(self, day: date) -> FxQuote | None:
        idx = bisect.bisect_right(self._dates, day) - 1
        if idx < 0 or day - self._dates[idx] > BENCHMARK_LOOKBACK:
            return None
        row = self._rows[idx]
        return FxQuote(pair=row.pair, rate=Decimal(str(row.rate)), as_of=row.as_of_date, source=row.source)


def benchmark_rate(exchange: Exchange, rates: BenchmarkRates) -> FxQuote | None:
    """Reference rate expressed as 1 from_currency in to_currency, or ``None``."""
    pair = {exchange.from_currency, exchange.to_currency}
    if pair != {"CAD", "USD"}:
        return None
    quote = rates.on(exchange.date)
    if quote is None or quote.rate <= 0:
        return None
    rate = quote.rate if exchange.from_currency == "USD" else Decimal(1) / quote.rate
    return FxQuote(pair=quote.pair, rate=rate, as_of=quote.as_of, source=quote.source)


def spread_pct(effective: Decimal, reference: Decimal) -> float:
    """Positive when the effective rate was worse than the reference."""
    return float(((reference - effective) / reference * 100).quantize(Decimal("0.0001")))


class ExchangeService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # -- CRUD -------------------------------------------------------------
    def list(self, filters: Filters = Filters()) -> list[Exchange]:
        stmt = select(Exchange)
        if filters.date_from:
            stmt = stmt.where(Exchange.date >= filters.date_from)
        if filters.date_to:
            stmt = stmt.where(Exchange.date <= filters.date_to)
        if filters.provider:
            stmt = stmt.where(Exchange.provider == filters.provider)
        if filters.currency:
            code = filters.currency.upper()
            stmt = stmt.where(or_(Exchange.from_currency == code, Exchange.to_currency == code))
        return list(self.db.execute(stmt.order_by(Exchange.date.desc(), Exchange.id.desc())).scalars())

    def get(self, exchange_id: int) -> Exchange:
        exchange = self.db.get(Exchange, exchange_id)
        if exchange is None:
            raise ExchangeNotFound(f"Exchange {exchange_id} not found")
        return exchange

    def create(self, data: ExchangeCreate) -> Exchange:
        _check_assets(self.db, data.from_asset_id, data.to_asset_id)
        exchange = Exchange(**data.model_dump())
        _check_record(exchange)
        self.db.add(exchange)
        self.db.commit()
        self.db.refresh(exchange)
        return exchange

    def update(self, exchange_id: int, data: ExchangeUpdate) -> Exchange:
        exchange = self.get(exchange_id)
        changes = data.model_dump(exclude_unset=True)
        _check_assets(self.db, changes.get("from_asset_id"), changes.get("to_asset_id"))
        for key, value in changes.items():
            setattr(exchange, key, value)
        try:
            _check_record(exchange)
        except InvalidExchange:
            self.db.rollback()
            raise
        self.db.commit()
        self.db.refresh(exchange)
        return exchange

    def delete(self, exchange_id: int) -> None:
        self.db.delete(self.get(exchange_id))
        self.db.commit()

    # -- Benchmarks and stats ---------------------------------------------
    def benchmark_rates(self, exchanges: list[Exchange]) -> BenchmarkRates | None:
        days = [e.date for e in exchanges if {e.from_currency, e.to_currency} == {"CAD", "USD"}]
        if not days:
            return None
        return BenchmarkRates(self.db, min(days), max(days))

    def summary(self, filters: Filters = Filters()) -> dict:
        exchanges = self.list(filters)
        rates = self.benchmark_rates(exchanges)
        groups: dict[tuple[str, str], list[Exchange]] = defaultdict(list)
        for exchange in exchanges:
            groups[(exchange.from_currency, exchange.to_currency)].append(exchange)

        pairs = []
        for (from_ccy, to_ccy), rows in sorted(groups.items()):
            total_from = sum((Decimal(str(r.from_amount)) for r in rows), ZERO)
            total_to = sum((Decimal(str(r.to_amount)) for r in rows), ZERO)
            fees: dict[str, Decimal] = defaultdict(lambda: ZERO)
            for r in rows:
                if r.fee_amount is not None and r.fee_currency:
                    fees[r.fee_currency] += Decimal(str(r.fee_amount))

            covered, reference_to, covered_to = 0, ZERO, ZERO
            if rates is not None:
                for r in rows:
                    quote = benchmark_rate(r, rates)
                    if quote is None:
                        continue
                    covered += 1
                    reference_to += Decimal(str(r.from_amount)) * quote.rate
                    covered_to += Decimal(str(r.to_amount))

            pairs.append(
                {
                    "from_currency": from_ccy,
                    "to_currency": to_ccy,
                    "count": len(rows),
                    "total_from": total_from,
                    "total_to": total_to,
                    "average_rate": (total_to / total_from).quantize(Decimal("0.00000001")),
                    "fees": dict(fees),
                    "benchmark_coverage": covered,
                    "spread_cost": quantize(reference_to - covered_to) if covered else None,
                    "spread_pct": spread_pct(covered_to, reference_to) if covered else None,
                }
            )
        return {"count": len(exchanges), "pairs": pairs}
