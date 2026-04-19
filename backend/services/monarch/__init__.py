"""Monarch Money CSV importer package.

Pipeline mirrors the Wealthsimple one:

:mod:`parser`    - tokenises a Monarch CSV export into :class:`MonarchRow`
                   objects, classifies accounts into :class:`AccountClass`,
                   infers currency from the account label, and filters
                   pseudo-accounts (``Transfer`` / ``Income`` /
                   ``Uncategorized``).

:mod:`accounts`  - resolves a Monarch account label to a Canopy
                   :class:`Asset` or :class:`Liability`, autocreating
                   when needed.

:mod:`importer`  - writes rows into the Canopy schema with two layers of
                   dedup: per-account cutover against earlier
                   Wealthsimple imports, and a canonical ``(entity, date,
                   amount)`` fingerprint that catches cross-source
                   duplicates.
"""

from backend.services.monarch.parser import (
    AccountClass,
    MonarchRow,
    ParseResult,
    is_monarch_filename,
    parse_monarch_csv,
)

__all__ = [
    "AccountClass",
    "MonarchRow",
    "ParseResult",
    "parse_monarch_csv",
    "is_monarch_filename",
]
