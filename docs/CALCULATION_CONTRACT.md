# Canopy calculation contract

Status: in force for cash flow and budgets; adopted incrementally by reports,
exports and assistant tools. Implementation: `backend/services/calculation/`.

Every money figure Canopy shows, exports or lets the assistant quote must come
from this contract, so the same period and filters yield the same numbers
everywhere.

## Amounts and flow kind

- `Transaction.type` decides the flow kind. `income` and `expense` are cash
  flow; `transfer`, `buy` and `sell` are excluded, never silently folded in.
- The sign of `amount` is not trusted: importers disagree (Monarch keeps
  signed amounts, CSV stores absolute values). Consumers use `abs(amount)`.
- Unknown types are excluded and should be surfaced in review tooling.

## Calendar periods

- Periods are calendar months, quarters and years. Nothing approximates a
  month as 30 days.
- Every range is half-open: `start <= date < end_exclusive`. The last day of a
  month belongs to that month whatever time of day the row carries.
- Trend windows are "the N calendar months ending with the reference month"
  (`months_back`). Missing months are zero-filled so charts keep their axis.
- Comparisons use the immediately preceding period of the same kind
  (`prior_period_bounds`).
- Boundaries are evaluated in the clock the rows were stored in. Importers
  write date-only values, so this is the transaction's calendar date.
  Timezone-aware boundaries are a known limitation, not a hidden conversion.

## Money arithmetic

- Aggregate in SQL (`monthly_flows`) and in `Decimal`; quantize to cents
  (`ROUND_HALF_UP`) only at the reporting boundary.
- API responses serialize money through `backend/models/money.py:Money` as a
  2-decimal JSON number. Ratios (percentages, savings rate) are floats.
- Totals are kept per original currency first (`CurrencyFlow` per currency).

## Reporting currency and FX

- Converting to a reporting currency (`to_reporting`) is an explicit step that
  records provenance: pair, rate, observation date and source for every
  converted currency.
- The rate is the Bank of Canada observation in effect on the period's `as_of`
  date (month end for monthly buckets), falling back to the latest prior
  observation and recording *that* date.
- Missing rate or unsupported currency: the amount stays in `unconverted` and
  `fx_complete` is `false`. There is no fallback rate on the backend. The
  frontend display fallback used for portfolio views must never be reused for
  ledger totals or tax figures.
- Reporting conversions are for Wallet display and analysis. Tax conversions
  require the CRA-prescribed rate for the relevant date and are a separate,
  evidenced step in the Tax workspace.

## Exchange records

- The Exchange ledger (`exchanges` table, `/v1/exchange`) is the one place that
  stores currencies beyond CAD/USD. Each row keeps both legs in their original
  currency; nothing is converted to a reporting currency.
- Exchanges never create transactions, so they are invisible to cash flow,
  budgets and net worth.
- `from_amount` is the total that left the source balance, fees included;
  `fee_amount` is a breakdown of that total, not an extra cost. Importers must
  follow the same rule.
- The effective rate is always `to_amount / from_amount` (an all-in rate, so
  the spread against the reference already contains the fee); a provider's
  quoted rate is stored for reference only.
- Only CAD↔USD exchanges get a benchmark: the Bank of Canada USDCAD observation
  on the exchange date, or the latest one in the 10 days before it. Other
  pairs report no benchmark. There is no fallback rate.

## Known limitations

- No refund, hidden, pending or split markers in the transaction model; every
  stored row counts once (W2 adds these).
- Budgets have no currency column and are treated as CAD; non-CAD spend is
  converted with provenance when a rate exists, otherwise reported as
  unconverted.
- Quarterly budget periods are not modelled yet (#116).

## Tests that define the contract

`backend/tests/test_calculation_*.py`: month/quarter/year bounds including
Jan 31 → Feb, leap February and Dec → Jan; `months_back` and clamping;
classification by type; CAD-only, CAD+USD with and without a rate;
last-day-of-month inclusion; transfer exclusion; per-currency separation;
category grouping.
