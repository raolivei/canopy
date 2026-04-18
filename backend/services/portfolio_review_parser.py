"""Parse Canadian portfolio review exports (Canada section only, CAD only).

Supports tab- or comma-separated rows (Google Sheets / Excel often emit **comma**
with quoted thousands like ``"47,226"``). Delimiter is chosen per line so
section title lines without tabs still work next to TSV data rows.

Skips plan rows where both local value and pct are empty (e.g. Questrade
``VTI (QT)`` targets with ``—``).

Only the Canada section is consumed; any other sections (legacy Brazil / Crypto)
are ignored so CSVs exported from the original multi-region spreadsheet still
parse cleanly but contribute only the Canadian holdings.
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

# Section markers (first cell may include emoji + text).
# We only recognize the Canada section; other sections are treated as
# "inactive" (rows under them are ignored).
_SECTION_CA = re.compile(r"Canada\s+Portfolio", re.I)
_SECTION_OTHER = re.compile(
    r"(Brazil|BR|Crypto|CRYPTO|International|Emerging)\s+Portfolio",
    re.I,
)

_DATE_RE = re.compile(
    r"(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})",
    re.I,
)
_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _empty_cell(s: str) -> bool:
    t = (s or "").strip()
    if not t:
        return True
    if t in ("—", "-", "–", "―"):
        return True
    return False


def _parse_decimal(s: str) -> Optional[Decimal]:
    if _empty_cell(s):
        return None
    s = s.strip().replace(",", "").replace("~", "")
    s = re.sub(r"[*†]$", "", s).strip()
    if s.endswith("%"):
        s = s[:-1].strip()
    if _empty_cell(s):
        return None
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return None


def _parse_percent_decimal(s: str) -> Optional[Decimal]:
    """Store e.g. 33.5 for 33.50% (chart code can scale if needed)."""
    return _parse_decimal(s)


def _parse_int(s: str) -> Optional[int]:
    if _empty_cell(s):
        return None
    try:
        return int(s.strip())
    except ValueError:
        return None


def _delimiter_for_line(line: str) -> str:
    """Prefer tab when the row is clearly TSV; otherwise comma."""
    tabs = line.count("\t")
    commas = line.count(",")
    if tabs >= 2 and tabs >= commas:
        return "\t"
    if commas >= 2 and commas > tabs:
        return ","
    if "\t" in line:
        return "\t"
    return ","


def _parse_date_line(line: str) -> Optional[date]:
    m = _DATE_RE.search(line)
    if not m:
        return None
    d, mon, y = m.groups()
    mi = _MONTHS.get(mon[:3].lower())
    if not mi:
        return None
    try:
        return date(int(y), mi, int(d))
    except ValueError:
        return None


@dataclass
class ParsedLine:
    investment: str
    platform: str
    value_cad: Optional[Decimal]
    pct_global: Optional[Decimal]
    return_pct: Optional[Decimal]
    div_per_year: Optional[Decimal]
    yield_pct: Optional[Decimal]
    target_pct: Optional[str]
    delta: Optional[str]
    conviction: Optional[int]
    action: Optional[str]
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedPortfolioReview:
    as_of_date: date
    lines: list[ParsedLine]
    label: Optional[str] = None


def _normalize_header_cell(h: str) -> str:
    return (h or "").strip().lower().replace("\ufeff", "")


def _header_to_key(h: str) -> str:
    """Map spreadsheet header to stable dict keys.

    CAD-only: any ``Value (CAD)`` / ``Value CAD`` column is treated as the
    primary value; ``USD`` / ``% Canada`` / legacy columns are ignored so the
    parser is resilient to old spreadsheet exports.
    """
    x = _normalize_header_cell(h)
    if x == "investment":
        return "investment"
    if x == "platform":
        return "platform"
    if "value" in x and "cad" in x:
        return "value_cad"
    if "global" in x and "%" in x:
        return "pct_global"
    if x == "% global":
        return "pct_global"
    if x == "return":
        return "return"
    if "div" in x and "yr" in x:
        return "div_yr"
    if x == "yield":
        return "yield"
    if "target" in x:
        return "target_pct"
    if x == "delta":
        return "delta"
    if x == "conviction":
        return "conviction"
    if x == "action":
        return "action"
    slug = re.sub(r"[^a-z0-9]+", "_", x).strip("_")
    return slug or x


def _is_header_row(cells: list[str]) -> bool:
    if not cells:
        return False
    return _normalize_header_cell(cells[0]) == "investment"


def _row_to_dict(headers: list[str], cells: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for i, h in enumerate(headers):
        key = _header_to_key(h)
        val = cells[i] if i < len(cells) else ""
        out[key] = val
    return out


def _is_section_canada(first_cell: str, line: str) -> bool:
    return bool(_SECTION_CA.search(line)) or "🇨🇦" in first_cell


def _is_section_other(first_cell: str, line: str) -> bool:
    """Brazil / Crypto / Emerging / International — anything not Canada."""
    if _is_section_canada(first_cell, line):
        return False
    if _SECTION_OTHER.search(line):
        return True
    # Non-Canada flag emojis
    return any(flag in first_cell for flag in ("🇧🇷", "₿", "🪙", "🇺🇸", "🌐"))


def _extract_line_from_row(
    row: dict[str, str],
    raw_list: list[str],
) -> Optional[ParsedLine]:
    inv = (row.get("investment") or "").strip()
    if not inv:
        return None

    val_cad = _parse_decimal(row.get("value_cad", ""))
    if val_cad is None:
        return None

    return ParsedLine(
        investment=inv,
        platform=(row.get("platform") or "").strip(),
        value_cad=val_cad,
        pct_global=_parse_percent_decimal(row.get("pct_global", "")),
        return_pct=_parse_percent_decimal(row.get("return", "")),
        div_per_year=_parse_decimal(row.get("div_yr", "")),
        yield_pct=_parse_percent_decimal(row.get("yield", "")),
        target_pct=(row.get("target_pct", "") or "").strip() or None,
        delta=(row.get("delta", "") or "").strip() or None,
        conviction=_parse_int(row.get("conviction", "")),
        action=(row.get("action", "") or "").strip() or None,
        raw={"cells": raw_list},
    )


def parse_portfolio_review_text(content: str) -> ParsedPortfolioReview:
    """Parse full file content (UTF-8). Only the Canada section is consumed."""
    lines_out: list[ParsedLine] = []
    as_of: Optional[date] = None
    in_canada_section = False
    headers: list[str] = []

    text = content.lstrip("\ufeff")
    raw_lines = text.splitlines()

    for line in raw_lines:
        if not line.strip():
            continue

        delim = _delimiter_for_line(line)
        split_for_first = line.split("\t") if "\t" in line else line.split(",")
        first_cell = split_for_first[0] if split_for_first else line

        if _is_section_canada(first_cell, line):
            in_canada_section = True
            headers = []
            continue
        if _is_section_other(first_cell, line):
            in_canada_section = False
            headers = []
            continue

        # Global as-of date line (appears at top of each section)
        d = _parse_date_line(line)
        if d:
            if as_of is None:
                as_of = d
            else:
                as_of = d  # last date wins if repeated per section

        if not in_canada_section:
            continue

        try:
            cells = next(csv.reader(io.StringIO(line), delimiter=delim))
        except StopIteration:
            continue

        if _is_header_row(cells):
            headers = [c.strip() for c in cells]
            continue

        if not headers:
            continue

        row = _row_to_dict(headers, cells)
        pl = _extract_line_from_row(row, cells)
        if pl:
            lines_out.append(pl)

    if as_of is None:
        as_of = date.today()

    return ParsedPortfolioReview(as_of_date=as_of, lines=lines_out)


def total_cad(lines: list[ParsedLine]) -> Decimal:
    s = Decimal("0")
    for ln in lines:
        if ln.value_cad is not None:
            s += ln.value_cad
    return s
