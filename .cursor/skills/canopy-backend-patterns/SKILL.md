---
name: canopy-backend-patterns
description: >-
  Canopy FastAPI services: portfolio math, balance-based assets, FX, integrations.
  Use when changing backend/api, services, or models.
---

# Backend patterns

## Balance-based vs traded assets

- **`BALANCE_BASED_ASSET_TYPES`** in `portfolio_calculator.py` (bank, retirement shells, cash, etc.): **`current_price`** is the **total balance**, not per-share price.
- **`native_balances_from_history`**: prefer latest **`AccountBalanceHistory`** row (native currency) aligned with Accounts API—do not rely only on `Asset.current_price` for those types when history exists.

## Holding summaries

- **`get_holding_summary`** returns `symbol`, `name`, `market_value`, etc. Importers may set **`symbol`** to an internal key and **`name`** to the user-facing label—UIs for balance accounts should favor **name** for display.

## FX

- Rates stored in **`fx_rates`**; **`backend/services/fx.py`** for latest / as-of / convert. Combined CAD/USD views depend on this chain being consistent with timeline and accounts endpoints.

## Integrations

- **Wise** / **Questrade**: logic in `services/wise_integration.py`, `services/questrade_integration.py`; routes under **`/v1/integrations`**.
- Respect **CAD/USD** product limits (e.g. Wise pockets in other currencies may be skipped or reported separately).
- **Wise** sets **`Asset.current_price`** on sync and does **not** write `AccountBalanceHistory`. Holdings/accounts must not let CSV/Monarch snapshot rows override that balance with **$0**.

## Imports (high level)

- **Wealthsimple** and **Monarch** have dedicated parsers/importers; dedup via **`imported_events`** / **canonical hash** where implemented—changes to hashing or cutover rules affect both sources.
