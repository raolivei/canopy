"""Pydantic schemas for the currency exchange ledger API.

Exchange records accept any ISO 4217 currency (an exception to Canopy's
CAD/USD scope); only CAD<->USD pairs get a Bank of Canada benchmark.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, BeforeValidator, ConfigDict, Field, model_validator

from backend.models.money import Money, Rate

ExchangeProvider = Literal["wise", "remitly", "instarem", "bank", "other"]
ExchangeSource = Literal["manual", "wise_csv", "remitly_csv", "instarem_csv"]


def _normalise_code(value: object) -> object:
    return value.strip().upper() if isinstance(value, str) else value


def _check_code(value: str) -> str:
    if len(value) != 3 or not value.isascii() or not value.isalpha():
        raise ValueError("must be a 3-letter ISO 4217 currency code")
    return value


CurrencyCode = Annotated[str, BeforeValidator(_normalise_code), AfterValidator(_check_code)]
PositiveAmount = Annotated[Decimal, Field(gt=0, max_digits=18, decimal_places=2)]
NonNegativeAmount = Annotated[Decimal, Field(ge=0, max_digits=18, decimal_places=2)]
QuotedRate = Annotated[Decimal, Field(gt=0, max_digits=18, decimal_places=8)]
Label = Annotated[str, Field(min_length=1, max_length=200)]


class ExchangeBase(BaseModel):
    from_asset_id: int | None = None
    to_asset_id: int | None = None
    from_label: Label | None = None
    to_label: Label | None = None
    fee_amount: NonNegativeAmount | None = None
    fee_currency: CurrencyCode | None = None
    quoted_rate: QuotedRate | None = None
    external_id: str | None = Field(None, max_length=100)
    notes: str | None = Field(None, max_length=2000)


class ExchangeCreate(ExchangeBase):
    date: dt.date
    provider: ExchangeProvider
    from_currency: CurrencyCode
    from_amount: PositiveAmount
    to_currency: CurrencyCode
    to_amount: PositiveAmount
    source: ExchangeSource = "manual"

    @model_validator(mode="after")
    def _distinct_currencies(self) -> ExchangeCreate:
        if self.from_currency == self.to_currency:
            raise ValueError("from_currency and to_currency must differ")
        return self


class ExchangeUpdate(ExchangeBase):
    """Partial update; cross-field rules are re-checked on the merged record."""

    date: dt.date | None = None
    provider: ExchangeProvider | None = None
    from_currency: CurrencyCode | None = None
    from_amount: PositiveAmount | None = None
    to_currency: CurrencyCode | None = None
    to_amount: PositiveAmount | None = None

    @model_validator(mode="after")
    def _no_null_required(self) -> ExchangeUpdate:
        required = ("date", "provider", "from_currency", "from_amount", "to_currency", "to_amount")
        nulled = [f for f in required if f in self.model_fields_set and getattr(self, f) is None]
        if nulled:
            raise ValueError(f"{', '.join(nulled)} cannot be null")
        return self


class Benchmark(BaseModel):
    """Bank of Canada reference rate for a CAD<->USD exchange."""

    rate: Rate = Field(description="1 from_currency in to_currency at the reference rate")
    as_of: dt.date
    source: str | None = None
    spread_pct: float = Field(description="How much worse the effective rate was than the reference, in %")


class ExchangeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: dt.date
    provider: str
    from_currency: str
    from_amount: Money
    to_currency: str
    to_amount: Money
    fee_amount: Money | None = None
    fee_currency: str | None = None
    quoted_rate: Rate | None = None
    effective_rate: Rate
    from_asset_id: int | None = None
    to_asset_id: int | None = None
    from_label: str | None = None
    to_label: str | None = None
    external_id: str | None = None
    source: str
    notes: str | None = None
    benchmark: Benchmark | None = None
    created_at: dt.datetime
    updated_at: dt.datetime


class PairSummary(BaseModel):
    from_currency: str
    to_currency: str
    count: int
    total_from: Money
    total_to: Money
    average_rate: Rate = Field(description="Weighted: total_to / total_from")
    fees: dict[str, Money] = Field(default_factory=dict, description="Fee totals by fee currency")
    benchmark_coverage: int = Field(0, description="Exchanges that had a Bank of Canada reference rate")
    spread_cost: Money | None = Field(
        None, description="Reference amount minus amount received, in to_currency, over covered exchanges"
    )
    spread_pct: float | None = None


class ExchangeSummary(BaseModel):
    count: int
    pairs: list[PairSummary]
