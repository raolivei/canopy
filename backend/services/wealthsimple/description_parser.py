"""Micro-parser for the ``description`` column of Wealthsimple CSV rows.

Wealthsimple description strings are already structured. Five patterns
recur across every account class:

- BUY:  ``<TICKER> - <Name>: Bought <shares> shares at $<price> per share
        (executed at <YYYY-MM-DD>)[, FX Rate: <fx>]``
- SELL: identical, with ``Sold`` instead of ``Bought``.
- DIV:  ``<TICKER> - <Name>: Cash dividend distribution, received on <YYYY-MM-DD>,
        record date of <YYYY-MM-DD>[, FX Rate: <fx>]``
- SHARE_TRANSFER: ``<TICKER> - <Name>: Tax-free transfer of <shares> shares
                  out of the account (executed at <YYYY-MM-DD>)``
- DIRECT_DEPOSIT: ``Direct deposit from <EMPLOYER>``

Ticker names may contain back-ticked apostrophes (``Lowe`s Cos.``).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Optional

_TICKER = r"[A-Z][A-Z0-9\.\-]*"
_NUM = r"[-+]?\d+(?:\.\d+)?"

_BUY_RE = re.compile(
    rf"^(?P<ticker>{_TICKER})\s*-\s*(?P<name>.+?):\s*Bought\s+(?P<shares>{_NUM})\s+shares?\s+at\s+\$(?P<price>{_NUM})\s+per\s+share\s*\(executed at (?P<exec>\d{{4}}-\d{{2}}-\d{{2}})\)(?:,\s*FX Rate:\s*(?P<fx>{_NUM}))?"
)

_SELL_RE = re.compile(
    rf"^(?P<ticker>{_TICKER})\s*-\s*(?P<name>.+?):\s*Sold\s+(?P<shares>{_NUM})\s+shares?\s+at\s+\$(?P<price>{_NUM})\s+per\s+share\s*\(executed at (?P<exec>\d{{4}}-\d{{2}}-\d{{2}})\)(?:,\s*FX Rate:\s*(?P<fx>{_NUM}))?"
)

_DIV_RE = re.compile(
    rf"^(?P<ticker>{_TICKER})\s*-\s*(?P<name>.+?):\s*Cash dividend distribution,\s*received on (?P<pay>\d{{4}}-\d{{2}}-\d{{2}}),\s*record date of (?P<record>\d{{4}}-\d{{2}}-\d{{2}})(?:,\s*FX Rate:\s*(?P<fx>{_NUM}))?"
)

_SHARE_TRANSFER_RE = re.compile(
    rf"^(?P<ticker>{_TICKER})\s*-\s*(?P<name>.+?):\s*Tax-free transfer of (?P<shares>{_NUM})\s+shares?\s+(?:out of|into) the account"
)

_DIRECT_DEPOSIT_RE = re.compile(r"^Direct deposit from\s+(?P<employer>.+?)\s*$")


@dataclass(frozen=True)
class BuyInfo:
    ticker: str
    name: str
    shares: Decimal
    price: Decimal
    executed_at: date
    fx_rate: Optional[Decimal]


@dataclass(frozen=True)
class SellInfo:
    ticker: str
    name: str
    shares: Decimal
    price: Decimal
    executed_at: date
    fx_rate: Optional[Decimal]


@dataclass(frozen=True)
class DivInfo:
    ticker: str
    name: str
    pay_date: date
    record_date: date
    fx_rate: Optional[Decimal]


@dataclass(frozen=True)
class ShareTransferInfo:
    ticker: str
    name: str
    shares: Decimal


@dataclass(frozen=True)
class DirectDepositInfo:
    employer: str


def _dec(s: str) -> Optional[Decimal]:
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return None


def _date(s: str) -> Optional[date]:
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


def parse_buy(desc: str) -> Optional[BuyInfo]:
    m = _BUY_RE.match(desc)
    if not m:
        return None
    shares = _dec(m.group("shares"))
    price = _dec(m.group("price"))
    exec_at = _date(m.group("exec"))
    if shares is None or price is None or exec_at is None:
        return None
    fx = _dec(m.group("fx")) if m.group("fx") else None
    return BuyInfo(
        ticker=m.group("ticker"),
        name=m.group("name").strip(),
        shares=shares,
        price=price,
        executed_at=exec_at,
        fx_rate=fx,
    )


def parse_sell(desc: str) -> Optional[SellInfo]:
    m = _SELL_RE.match(desc)
    if not m:
        return None
    shares = _dec(m.group("shares"))
    price = _dec(m.group("price"))
    exec_at = _date(m.group("exec"))
    if shares is None or price is None or exec_at is None:
        return None
    fx = _dec(m.group("fx")) if m.group("fx") else None
    return SellInfo(
        ticker=m.group("ticker"),
        name=m.group("name").strip(),
        shares=shares,
        price=price,
        executed_at=exec_at,
        fx_rate=fx,
    )


def parse_div(desc: str) -> Optional[DivInfo]:
    m = _DIV_RE.match(desc)
    if not m:
        return None
    pay = _date(m.group("pay"))
    record = _date(m.group("record"))
    if pay is None or record is None:
        return None
    fx = _dec(m.group("fx")) if m.group("fx") else None
    return DivInfo(
        ticker=m.group("ticker"),
        name=m.group("name").strip(),
        pay_date=pay,
        record_date=record,
        fx_rate=fx,
    )


def parse_share_transfer(desc: str) -> Optional[ShareTransferInfo]:
    m = _SHARE_TRANSFER_RE.match(desc)
    if not m:
        return None
    shares = _dec(m.group("shares"))
    if shares is None:
        return None
    return ShareTransferInfo(
        ticker=m.group("ticker"),
        name=m.group("name").strip(),
        shares=shares,
    )


def parse_direct_deposit(desc: str) -> Optional[DirectDepositInfo]:
    m = _DIRECT_DEPOSIT_RE.match(desc)
    if not m:
        return None
    return DirectDepositInfo(employer=m.group("employer").strip())
