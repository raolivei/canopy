"""Shared dedup helpers for CSV importers.

Two hash flavours live here:

* :func:`source_event_hash` - per-source fingerprint. Each importer passes
  whatever fields make a row unique within its own source (e.g. Wealthsimple
  ``raw_code`` + description). Catches *re-uploads of the same file*.

* :func:`canonical_event_hash` - source-agnostic fingerprint of the
  real-world transaction. Inputs are the Canopy ``entity_key`` the event
  pertains to (``asset:N`` or ``liability:N``), the transaction date, and
  the signed amount. Catches *the same transaction imported from two
  different sources* (Wealthsimple + Monarch, etc.).

Neither hash is a cryptographic signature - they are content fingerprints.
"""

from __future__ import annotations

import hashlib
from datetime import date
from decimal import Decimal


def entity_key_for_asset(asset_id: int) -> str:
    """Return the cross-source key for a Canopy ``Asset``."""
    return f"asset:{asset_id}"


def entity_key_for_liability(liability_id: int) -> str:
    """Return the cross-source key for a Canopy ``Liability``."""
    return f"liability:{liability_id}"


def canonical_event_hash(entity_key: str, occurred_on: date, amount: Decimal) -> str:
    """Compute the source-agnostic fingerprint for a transaction.

    Two importers that resolve the same real-world account to the same
    Canopy entity will produce identical canonical hashes for the same
    ``(date, amount)`` pair, enabling cross-source dedup.

    The amount is quantised to two decimal places so trivial formatting
    differences (``'5.00'`` vs ``'5'``) don't produce distinct hashes.
    """
    q = amount.quantize(Decimal("0.01"))
    payload = f"{entity_key}|{occurred_on.isoformat()}|{q}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def source_event_hash(source: str, *parts: object) -> str:
    """Compute a per-source fingerprint.

    ``parts`` are stringified and joined with ``|``. Callers pass
    whichever fields make a row unique inside their own source.
    """
    payload = "|".join([source, *[str(p) for p in parts]])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
