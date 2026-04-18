"""Wealthsimple CSV auto-importer package.

Parses Wealthsimple monthly-statement CSV exports (all account classes),
classifies them into investments / cash / debt, and writes the normalized
rows into the existing Canopy schema (Asset / Lot / Dividend / Transaction
/ AccountBalanceHistory / Liability / LiabilityBalanceHistory).

Public entry point: :class:`WealthsimpleImporter` (see ``importer``).
"""

from backend.services.wealthsimple.filename_parser import (
    AccountClass,
    WsAccountKind,
    WsFileMeta,
    parse_filename,
)

__all__ = [
    "AccountClass",
    "WsAccountKind",
    "WsFileMeta",
    "parse_filename",
]
