# Changelog

All notable changes to this project will be documented in this file.

## Versioning

**Current Status**: Pre-release (0.x.x versions)

- **0.x.x**: Development versions - features are being built and tested
- **1.0.0**: First stable release - will be tagged when feature-complete and production-ready

## [0.10.2] - 2026-04-18 — Monarch account-balance snapshots

Closes the last big valuation gap for non-Wealthsimple accounts: RBC, Scotia, credit cards, and every other Monarch-connected institution now ships historical balance snapshots into Canopy, so the Accounts page and net-worth timeline stop showing `$0` for them. The Monarch CSV drop zone now auto-detects and imports Monarch's second export — **Balances** — alongside transactions in a single upload.

### Added

- **Monarch *Balances* CSV importer** (`backend/services/monarch/balances_parser.py`, `balances_importer.py`). Parses Monarch's `Date,Balance,Account` export, resolves each row through the same last-4 / name matcher the transactions importer uses (so WS-imported accounts and Monarch-imported accounts converge on the same Canopy entity), and upserts into `AccountBalanceHistory` (assets) or `LiabilityBalanceHistory` (liabilities). Monarch reports liability balances as negative ("you owe $21,818" → `-21818.66`); the importer flips the sign so downstream "amount owed" math stays consistent with the WS importer. End-to-end smoke run on the author's real export: 580 rows in, **486 snapshots inserted**, 57 foreign-currency (EUR/TRY/COP/MXN/…) rows skipped, 37 unclassifiable rows skipped. 13 new tests covering multi-currency coexistence, re-upload idempotency, update-in-place on changed values, and liability sign flipping.
- **Unified drop zone** on `/portfolio/monarch-import`: a single file picker now accepts both Monarch exports at once. Each file is routed to the right importer by peeking at its header row (`Date,Balance,Account` → balances; everything else → transactions). The results pane shows separate "transaction files" and "balance files" sections with their respective counters.
- **Broadened account classifier** (`monarch/parser.py`):
  - Foreign-currency prefixes now include `COP`, `MXN`, `AUD`, `CHF`, `SGD`, `HKD`, `INR` on top of the existing `EUR/JPY/GBP/BRL/TRY`.
  - Debt markers picked up `credit_card` (Wealthsimple's snake-case label), `line_of_credit`, `line of credit`, `loan`, `mortgage`. This is what rescues `PORTFOLIO_LINE_OF_CREDIT (...CYMA)`, `car loan (...7001)`, and generic `CREDIT_CARD (...SDuQ)` rows from the "unknown" bucket.
  - Investment markers picked up `direct_index` so Wealthsimple's `DIRECT_INDEX_NON_REGISTERED` accounts land as investments (even though we don't import their WS statements anymore, Monarch still sees them).

### API

- `POST /v1/monarch-import/preview` and `/commit` now return a unified `{transactions, balances}` envelope. Old clients that only read `transactions_added` from the response will need to switch to `transactions.transactions_added` — the only consumer in the tree (the Monarch import page) has been migrated.
- File-upload cap raised from 5 → 10 to accommodate Monarch exports + multiple monthly Wealthsimple files in the same request.

### Why

Before this change the only balance data Canopy had for non-WS accounts was whatever the transactions importer could reconstruct from transaction deltas — which, without a starting balance, is useless. RBC / Scotia / credit-card balances all landed at `$0` on the Accounts page and the net-worth timeline underreported total assets. Monarch already aggregates authoritative balances across all linked institutions, so using its CSV export is the cheapest path to correctness.

---

## [0.10.1] - 2026-04-18 — Net-worth valuation + Danger Zone

Fixes a valuation gap where Wealthsimple investment accounts only contributed their uninvested cash sub-balance to net worth (because `AccountBalanceHistory` captures cash, not the market value of held securities). Adds a Settings "Danger Zone" that lets you wipe all imported data from one place. Also fixes a crash on the Holdings page.

### Added

- **Settings → Danger Zone**: delete all imported data with a typed-confirmation workflow. Lists per-table row counts, requires typing `RESET ALL DATA`, and invalidates every cached list on success. The endpoint (`POST /v1/admin/reset-data` with header `X-Confirm-Reset: RESET ALL DATA`) already existed — this surfaces it. FX-rate cache is preserved so the next session doesn't re-hit the BoC API unnecessarily.

### Changed

- **`GET /v1/wealthsimple-import/networth-timeline`** now folds the book value of every open lot into the `inv` bucket for each timeline point. Book value = `quantity × price_per_unit`, scoped by `Asset.currency`, and filtered to lots that were open on that date (`purchase_date <= d` and not closed before `d`). Previously the "Investments" figure for a Wealthsimple retirement account was just the uninvested CAD/USD sub-balance in that account, making net worth look wildly under-stated when securities were sitting in the account. New test: `test_timeline_folds_lot_book_value_into_investments`.
- **`PortfolioCalculator.get_holding_summary`**: when `Asset.current_price` is `None` but the position has unsold lots, `market_value` now falls back to total cost basis (assumes 0% return) so Holdings and Allocation charts render a non-zero value. Once a price-sync service lands, this fallback becomes a no-op.

### Fixed

- **Holdings page crash**: `TypeError: total_return_pct.toFixed is not a function`. FastAPI serializes `Decimal` as a JSON string; the Holdings hero now coerces `summary.total_return_pct` to `Number` before formatting and guards against `NaN`.
- **Accounts page showed every asset at $0**: `GET /v1/accounts/` was reading `Asset.current_price` (which no CSV importer populates) instead of the latest `AccountBalanceHistory` row. New helper `_latest_balances_by_asset` pulls the newest native-currency snapshot per asset and the Wealthsimple Chequing account now surfaces its real $1.61 balance. Regression test: `test_latest_balances_pulls_from_account_balance_history`.
- **Dark Reader hydration warning on mobile**: `Extra attributes from the server: data-darkreader-inline-stroke,style` from the Dark Reader browser extension injecting attributes onto lucide SVG icons before React hydrates. `MobileNav` now mount-gates on `useEffect` (the same pattern `Sidebar` already uses) so the server-rendered markup doesn't try to match an extension-mutated DOM.

### Notes

The `networth-timeline` aggregation does **not** yet use live market prices. Without a price-sync service, book value is the best honest proxy we have; when live prices arrive, the aggregator will automatically prefer them (via `Asset.current_price` on the lots' asset rows).

## [0.10.0] - 2026-04-18 — Questrade-style multi-currency views

Canopy now mirrors the Questrade / Wealthsimple "show me one currency or the combined total" UX. Every balance surface — dashboard hero, net-worth timeline, Accounts, and Holdings — respects a single global toggle: **CAD only**, **USD only**, **Combined CAD** (USD converted into CAD), or **Combined USD** (CAD converted into USD). Historical points use the FX rate as of that date; live totals use the latest Bank of Canada rate.

### Added

- **FX rate store**: new `fx_rates(pair, as_of_date, rate, source)` table with a unique `(pair, as_of_date)` constraint (Alembic `20260424_0012`). Seeds and writes `USDCAD` observations from the Bank of Canada Valet API.
- **`backend/services/fx.py`**: central FX helper — `get_latest_rate`, `get_rate_on` (exact match, else most-recent prior observation, else None), `convert(amount, from_ccy, to_ccy, on_date)`, `ensure_latest_rate_cached` (no-op if the cache is fresh, fetches otherwise), and `backfill_range` for bulk historical warm-ups. Stale threshold is 3 days.
- **`GET /v1/fx/usd-cad`**: returns `{ rate, as_of_date, is_stale, source }`. Warms the cache on request so the first page load after a cold start self-heals.
- **`POST /v1/fx/backfill?from=YYYY-MM-DD&to=YYYY-MM-DD`**: admin-style endpoint for seeding historical rates in one call.
- **`useCurrencyView` hook** (`frontend/hooks/useCurrencyView.ts`): SSR-safe React hook that persists the selected view in `localStorage` (`canopy.currencyView`), broadcasts changes across tabs via the `storage` event, and exposes `view`, `setView`, `viewCurrency(view)`, `viewLabel(view)`, `isSingleCurrencyView(view)`, and `convertForView(amount, fromCurrency, view, usdCadRate)`. `convertForView` filters single-currency views to zero for mismatched rows and applies the supplied FX rate for combined views.
- **`useFxRate` hook** (`frontend/hooks/useFxRate.ts`): React-Query wrapper around `/v1/fx/usd-cad` with a 10-minute stale time; exposes `rate`, `as_of_date`, and `is_stale`.
- **`CurrencyViewToggle` component** (`frontend/components/CurrencyViewToggle.tsx`): Questrade-style four-way segmented control — CAD / USD / Combined CAD / Combined USD — with a live `1 USD = X.XXXX CAD (as of YYYY-MM-DD)` caption. When the rate is stale the caption flips to amber and surfaces a warning.

### Changed

- **`GET /v1/accounts`** now returns, in addition to the existing per-account list:
  - `totals_by_currency`: `{ CAD: { cash, debt, net }, USD: { cash, debt, net } }` computed from the native balances on each account (no conversion).
  - `totals_combined`: `{ CAD: { cash, debt, net }, USD: { cash, debt, net } }` with the opposite-currency side converted at the latest USDCAD rate, so the "Combined CAD" button renders `CAD_cash + USD_cash * rate` etc.
  - `fx`: `{ pair, rate, as_of_date, is_stale }`.
  The endpoint warms the FX cache before aggregating so combined totals are never based on a cold cache.
- **`GET /v1/wealthsimple-import/networth-timeline`** now returns, per point, four slices — `cad`, `usd`, `combined_cad`, `combined_usd` — each with `investments / cash / debt / net_worth`, plus the per-date `fx_rate` used. Combined slices apply the FX rate for that specific date (falling back to the most recent prior observation for weekends / holidays); if no FX rate exists at all for a date, only the native slices are populated and the combined ones mirror the native side. The response also exposes `latest_slices` and `fx` metadata so the frontend can default to today's values without re-querying.
- **`GET /v1/wealthsimple-import/accounts`**: each Wealthsimple account now carries `balances_by_currency: { CAD, USD }` sub-balances, derived from the most recent `AccountBalanceHistory` rows per currency. Drives the native-currency badge + faded-in-excluded-views UX on the Accounts page.
- **Dashboard hero and timeline** (`pages/index.tsx`): consume the new timeline payload directly. Hero KPIs, the deltas strip, and the multi-line timeline chart all reformat to `displayCurrency` and pick the matching slice for every data point.
- **Accounts page** (`pages/accounts.tsx`): summary metrics (Cash / Debt / Net) read from `totals_by_currency` (single-currency views) or `totals_combined` (combined views). Individual account cards keep their native-currency label; in a single-currency view mismatched cards are faded, and in combined views they show an `≈` approximation in the view's target currency.
- **Holdings page** (`pages/portfolio.tsx`): total-portfolio-value hero, holdings table, and the "Allocation by Currency" panel all react to the global toggle. The legacy `EXCHANGE_RATES = { USD: { CAD: 1.35 } }` constant and the per-page currency dropdown are deleted — conversions go through `convertForView` / `useFxRate` and inherit the live BoC rate.

### Tests

- `backend/tests/test_fx_service.py`: exact-date hit, closest-prior-observation fallback, empty-store → None, latest fetch, `is_stale` threshold, `convert` arithmetic, and `ensure_latest_rate_cached` against a mocked Valet response (refresh path, cache-hit path, simulated outage path).
- `backend/tests/test_accounts_multi_currency.py`: `_roll_up_by_currency` buckets cash / debt per currency; `_combine_totals` cross-currency arithmetic with a known rate; graceful degradation when FX is missing.
- `backend/tests/test_networth_timeline_multi_currency.py`: end-to-end — seeds CAD+USD balances and `fx_rates` rows, asserts each point's four slices are correct with the per-date rate, and asserts fallback to the prior-observation rate when the exact date has no FX row.

## [0.9.0] - 2026-04-18 — Canadian investments focus, CAD + USD

Simplify the product: Canopy is a Canadian investment tracker scoped to **CAD + USD**. Brazil and all other non-Canadian / non-USD plumbing is removed. The Accounts page is wired to a dedicated endpoint that only shows cash / credit / LOC — investments stay on Holdings.

### Scope cleanup — CAD + USD only

- **Monarch importer** now treats USD accounts (WS USD, US chequing, US credit cards) as first-class: `USD account (...)`, `USA Checking (...)`, and `Credit Card USA (...)` are routed to CASH / DEBT with `currency=USD`; autocreated entities inherit the row's currency (CAD **or** USD). Any other prefix (EUR / JPY / GBP / BRL / TRY) is classified as `FOREIGN` and skipped.
- **Legacy bank-CSV importer** (`backend/services/csv_parser.py`, `backend/models/csv_import.py`): Brazilian brokerage formats (Nubank, Clear, XP, B3 CEI, Itau, Bradesco, Santander) removed from the `BankFormat` enum, detection regex, and field mappings. `_parse_brazilian_amount` helper deleted; `_parse_amount` currency strip list narrowed to `$ / C$ / CAD / USD`. Default currency is now `CAD`.
- **Integrations catalog** (`GET /v1/integrations/csv-formats`, `GET /v1/integrations`): Brazilian bank entries (Nubank / Clear / XP / B3 CEI / Pluggy) dropped.
- **Real-estate model**: default `country='CA'`, default `currency='CAD'` (was `BR` / `BRL`).
- **Frontend `CurrencyBadge`**: dropped `BRL` / `EUR` / `GBP` colour slots; only `CAD` + `USD` remain.
- **Portfolio-review parser** keeps its skip logic for legacy multi-region spreadsheets (BR / Crypto / Emerging / International sections were already ignored in 0.9.0) — only the Canada section contributes rows.
- **Data purge** (Alembic `20260423_0011`): one-shot migration that deletes any remaining rows with `country='BR'` or `currency='BRL'` across `assets`, `liabilities`, `transactions`, and `real_estate_properties`, cascading through `account_balance_history`, `lots`, `dividends`, `price_history`, `liability_balance_history`, `liability_payments`, and real-estate children.

### Added

- **`GET /v1/accounts`** (`backend/api/accounts.py`): unified view of cash assets (checking / savings / cash) and liabilities (credit, line of credit, loan). Powers the Accounts page directly from records created by the Wealthsimple importer.
- **Accounts page** (`pages/accounts.tsx`) rewritten to fetch from `/v1/accounts` — total cash, total debt, net position, and a per-account card grid. Empty state links straight to the Wealthsimple importer.
- **Multi-file portfolio-snapshot import**: new `POST /v1/portfolio-reviews/import/batch` accepts a list of CSVs and processes each in an isolated transaction (one bad file doesn't kill the rest); response is a per-file success/error list. `/portfolio/import` UI now supports drag-selecting multiple files with a per-file removal list and per-file result summary.
- **Monarch Money CSV importer** (`backend/services/monarch/`, `backend/api/monarch_import.py`, `frontend/pages/portfolio/monarch-import.tsx`): backfill years of transaction history from a Monarch export without double-counting Wealthsimple-owned activity.
  - `parser.py` validates the 8-column header, classifies each account into investment / cash / debt / foreign / pseudo, and drops Monarch's internal `Transfer` / `Income` / `Uncategorized` pseudo-accounts.
  - `accounts.py` resolves a Monarch account label to a Canopy `Asset` / `Liability` - matching by exact name, then by trailing account last-4, and autocreating a CAD-denominated Canadian entity when nothing matches.
  - `importer.py` enforces two layers of dedup: **Layer 1** drops any Monarch row whose date is on or after `min(Transaction.date)` for that entity where `import_source='wealthsimple_csv'` (Wealthsimple owns the account from that point forward); **Layer 2** consults the new `imported_events.canonical_hash` column to catch cross-source duplicates that slip through the cutover. Per-file reports break skips down into `skipped_pseudo`, `skipped_foreign`, `skipped_unknown_account`, `skipped_ws_covered`, `skipped_canonical_dup`, and `skipped_source_dup`.
  - `POST /v1/monarch-import/preview` dry-runs against a savepoint (rollback on exit); `POST /v1/monarch-import/commit` persists. Both accept up to 5 files at 25MB each.
  - `/portfolio/monarch-import` UI is a multi-file drop zone with Preview / Import buttons, an autocreated-entities summary, and per-file breakdowns. Monarch and Wealthsimple each get their own sidebar + command-palette entry; dropping a Monarch-looking file on `/portfolio/import` now surfaces a banner routing to the correct importer.
- **Canonical-hash dedup ledger** (`backend/services/canonical_hash.py`, Alembic `20260422_0010`): every importer can now record a source-agnostic fingerprint of a transaction (`sha256(entity_key | date | amount)`) alongside its per-source hash. The Wealthsimple importer writes it on every row going forward; the Monarch importer reads it to block cross-source duplicates. Existing `imported_events` rows are left with a `NULL` canonical value and get backfilled lazily on the next ingest.

### Changed

- **Scope is CAD + USD**: the product is a Canadian investment tracker. The multi-currency API (`/v1/currency`), exchange-rate service, `CurrencySelector` component, and currency dropdowns on Transactions / Insights / Import / Settings / Portfolio are all removed. `AccountBalanceHistory` keeps CAD + USD sub-balances side-by-side (see 0.9.0 fix below); net-worth aggregation filters to CAD.
- **Portfolio review parser**: only the Canadian section is ingested. Non-Canadian sections in legacy multi-region spreadsheets (e.g. Brazil / Crypto / Emerging / International blocks) are silently skipped. Intended for CAD-denominated holdings that don't auto-sync (private equity, real estate, DPSP). Columns collapse to `Value (CAD)`.
- **Database** (Alembic `20260420_0008`): `portfolio_reviews.total_value_usd` → `total_value_cad`; `portfolio_review_lines.value_usd` → `value_cad`; `region`, `currency`, `value_native`, `pct_region`, `fx_note` columns dropped.
- **Insights / FIRE calculators** (`services/insights_calculator.py`, `services/fire_calculator.py`) rewritten to operate on CAD directly — no conversion step, no `base_currency` parameter, no currency-exposure section.
- **Asset model**: default `currency="CAD"`, default `country="CA"`. `RETIREMENT_401K`, `RETIREMENT_IRA`, `RETIREMENT_ROTH_IRA` enum values dropped (Canadian-registered accounts only).
- **Bank CSV import** (`pages/import.tsx`): institution list trimmed to Wealthsimple / RBC / TD / Scotiabank / Generic CSV — US banks removed.
- **Dev workflow**: `backend/scripts/seed_portfolio.py` and the `make reseed` target are deleted. Bootstrap Canopy by dropping a Wealthsimple statement or a CAD portfolio snapshot.

### Removed

- `backend/api/currency.py`, `backend/models/currency.py`, `backend/services/exchange_rate_service.py`, `backend/scripts/seed_portfolio.py`.
- `frontend/components/CurrencySelector.tsx`; all USD / BRL / EUR dropdown options in forms.
- "Moomoo" integration references from the settings integrations catalog.

### Brand

- **Five logo explorations** added under `frontend/public/brand/concepts/` (three AI-generated PNGs — wallet-leaf, tree-coin, maple-shield — and two hand-authored monoline SVGs — leaf-chart, monogram). Reviewable at [`/logos`](https://canopy.eldertree.xyz/logos). The active logo (`canopy-icon.svg`, banner) is unchanged.

### Fixed

- **Wealthsimple DIV rows no longer blow up the importer.** `Dividend.dividend_type` column now uses `values_callable` so SQLAlchemy emits the enum **value** (`"cash"`) instead of the enum **name** (`"CASH"`), matching the lowercase values stored in the Postgres `dividendtype` enum. Same fix pattern as the earlier `AssetType` column. Previously, any file with a DIV transaction failed with `invalid input value for enum dividendtype: "CASH"`.
- **Wealthsimple importer now stores CAD + USD cash sub-balances side-by-side.**
  Wealthsimple investment statements (TFSA, FHSA, Retirement, ...) can carry
  both a CAD and a USD cash sub-balance when the account holds US stocks.
  The importer was writing one `account_balance_history` row per currency
  for the same `(asset_id, as_of_date)`, which collided with the old
  `uq_account_balance_asset_date` unique constraint and aborted the whole
  batch. Alembic `20260421_0009` widens the unique key to
  `(asset_id, as_of_date, currency)` — now both rows can coexist. The
  net-worth aggregator and latest-balance lookups explicitly filter to
  `currency = 'CAD'` so totals stay in one unit; non-CAD rows are preserved
  on-disk for future display on account detail.
- **Snapshot importer now guides Wealthsimple uploads to the right page.** Dropping files like `Chequing-monthly-statement-transactions-…`, `credit-card-statement-transactions-…`, or `TFSA-monthly-statement-transactions-…` on `/portfolio/import` returned a cryptic "No Canadian rows found" error. The frontend now detects these filename patterns at select-time and shows a banner with a one-click switch to `/portfolio/wealthsimple-import` (plus a "drop Wealthsimple files, keep the snapshots" shortcut); the backend mirrors the detection and returns an actionable error naming the correct importer if a Wealthsimple file still hits the snapshot endpoint.

---

## [0.8.0] - 2026-04-18 — Continuous net-worth tracking

This release re-frames Canopy around **continuous** net-worth tracking rather than semi-annual reviews. Monthly Wealthsimple statement drops now auto-classify into investments, cash, and debt and feed a unified net-worth dashboard; the 0.7.0 portfolio-review importer remains the input channel for holdings that don't export machine-readable CSVs (Brazilian brokerages, Binance, etc.).

### Added

- **Wealthsimple CSV drop zone** (`/portfolio/wealthsimple-import`): drop any combination of monthly-statement CSV exports (TFSA, RRSP, FHSA, Emerging, TFSA Long, Chequing, Crypto, credit card, Portfolio line of credit). Files are auto-classified from their filename, previewed with row counts / duplicates / warnings, then committed in one click.
- **Filename parser** (`services/wealthsimple/filename_parser.py`): 9 WS filename patterns supported (including emoji-labelled accounts like `Retirement ⛱️` and `Emerging 🇮🇳🇯🇵🇧🇷`); Direct Indexing is recognized and explicitly marked `skip` (account closed).
- **Row and description parsers** (`services/wealthsimple/row_parser.py`, `description_parser.py`): detects the two WS CSV shapes (investment/cash vs. credit-card), maps native transaction codes to a canonical `RowKind`, and extracts structured fields from `description` text (ticker / shares / price / exec date / FX for BUY, SELL, DIV, SHARE_TRANSFER, DIRECT_DEPOSIT).
- **Importer service** (`services/wealthsimple/importer.py`): upserts account-level `Asset` (investment/cash) and `Liability` (credit card, line of credit) records, writes `Lot` on BUY, marks lots sold on SELL, creates `Dividend` on DIV, records every row as a normalized `Transaction`, dedups via `ImportedEvent` hashes so re-imports are no-ops, and writes end-of-statement snapshots into `AccountBalanceHistory` / `LiabilityBalanceHistory`.
- **Alembic `20260419_0007`**: adds `liabilities.opening_balance Numeric(18,2) default 0` so credit-card balances can be reconstructed from partial monthly deltas.
- **API `/v1/wealthsimple-import`**:
  - `POST /preview` — multipart upload, dry-run classification + row counts + duplicate counts per file.
  - `POST /commit` — multipart upload, persists all rows; returns per-file summary.
  - `GET /accounts` — lists Wealthsimple `Asset` and `Liability` accounts currently known to Canopy.
  - `GET /networth-timeline` — combined timeline of investments + cash − debt, built by forward-filling `AccountBalanceHistory` and `LiabilityBalanceHistory` snapshots.
- **Dashboard net-worth hero** (`pages/index.tsx`): four KPI tiles (Net worth, Investments, Cash, Debt) and a multi-line timeline chart (investments / cash / debt / net worth) fed by `/networth-timeline`.
- **Navigation**: "Wealthsimple import" added as a primary sidebar item and to the command palette (keywords: `wealthsimple`, `ws`, `csv`, `tfsa`, `rrsp`, `fhsa`, `chequing`, `credit`).
- **Tests**: 30 new tests under `backend/tests/` — filename parser (13), description parser (8), importer service (9: classification, credit-card running balance, LOC balance, Direct Indexing skip, end-of-statement snapshot, idempotent re-import, multi-file drop). `backend/tests/conftest.py` maps PostgreSQL `ARRAY` / `JSONB` types to SQLite-compatible `TEXT` / `JSON` so the suite can run against an in-memory SQLite database.

### Changed

- **Dashboard**: net-worth hero and combined timeline now sit above the portfolio-review card; review-driven USD total remains below for holdings that don't sync from Wealthsimple.
- **Product positioning**: README and sidebar language shift from "semi-annual portfolio review" to "continuous net-worth tracking" — portfolio reviews are now documented as one of two input channels (Wealthsimple CSV drops being the other), not the primary workflow.

---

## [0.7.0] - 2026-04-01 - Portfolio review (semi-annual) pivot

### Added

- **Portfolio review model**: `portfolio_reviews` and `portfolio_review_lines` (Alembic `20260401_0005`) for spreadsheet-style rows without requiring synced `Asset` records; one review per `as_of_date` by default.
- **CSV/TSV parser** (`services/portfolio_review_parser.py`): multi-section Brazil / Canada / Crypto blocks, tab/comma detection, skips plan rows with empty values, normalizes `~`, commas, em-dash placeholders, footnotes on numeric cells.
- **API** (`/v1/portfolio-reviews`): list, get by id, delete, `POST /import` (multipart file, optional `replace=true`), `GET /timeline`, `GET /{id}/allocation` (`group_by=region|platform|conviction`), `GET /compare`, `POST /import/preview`.
- **Dashboard** (`pages/index.tsx`): total USD from latest review, change vs previous review, line chart over reviews, pie charts by region and platform; empty state links to import.
- **Import page** (`/portfolio/import`): upload portfolio snapshot file.

### Changed

- **Navigation**: Primary items emphasize Dashboard, Import snapshot, Holdings, Accounts, Insights, Report, Settings. **Advanced / legacy** (collapsible): Transactions, Bank CSV import, Integrations. Command palette and mobile bottom nav aligned (mobile drops Transactions from the bar; use More / palette).
- **Positioning**: README describes portfolio progress tracking as the main story; bank/API sync documented as advanced.

---

## [0.6.0] - 2026-02-18 - Modern UI Redesign

### Changed

- **Design system overhaul**: Migrated from gray/warm-gray palette to slate-based design tokens with teal/emerald primary, indigo accent, and semantic success/warning/danger colors
- **Chart theming**: Centralized chart colors, tooltips, grids, and axes via `utils/chartTheme.ts` for consistent data visualization across Dashboard, Insights, Portfolio
- **Component library**: New `Toast` (notification system) and `Table` (sortable, paginated) UI components; barrel exports in `components/ui/index.ts`
- **Sidebar navigation**: Replaced orphaned warm-gray/golden gradients with gradient-primary and slate tokens
- **All components updated**: CurrencySelector, ErrorBoundary, DarkModeToggle, StatCard, SkeletonLoader, AddAssetModal (refactored to use Modal/Button/Input/Select UI), PortfolioHoldingsTable (CurrencyBadge), PerformanceChart, AllocationChart, DividendHistory
- **Global ToastProvider** integrated in `_app.tsx`

---

## [0.5.0] - Wise integration

### Added

- **Wise API integration** (Settings → Integrations):
  - **Connect**: Enter Wise API token (from wise.com → Settings → API tokens); test connection and persist token in browser (localStorage). Optional sandbox mode for testing.
  - **Sync Now**: Fetches Wise balances and transactions, creates/updates Canopy assets per currency (e.g. WISE_CAD, WISE_USD), and imports transactions with `import_source=wise`. Duplicates skipped by `import_id`.
  - **Disconnect**: Clears stored token and connection state.
- Backend: `GET /v1/integrations/wise/status` — returns `{ connected: true }` when `WISE_API_TOKEN` env is set.
- Backend: `POST /v1/integrations/wise/sync` — accepts optional `api_token` (or uses `WISE_API_TOKEN`), `sandbox`, `days`; upserts Wise assets and imports transactions.
- Backend: Optional `wise_api_token` in Settings (from `WISE_API_TOKEN` env / Vault) for server-side token.

### Changed

- Integrations page: Wise card uses dedicated Connect/Sync flow and success/error feedback.

---

## [0.4.0] - 2026-01-31 - 🎯 **Insights & FIRE Planning**

### Major Features

#### Portfolio Insights Dashboard

- **Net Worth Tracking**: Multi-currency net worth calculation with USD as base currency
- **Asset Allocation**: Breakdown by type, currency, country, and institution
- **Currency Exposure**: Risk assessment (concentrated/balanced/diversified)
- **Growth Metrics**: Monthly/yearly rates, best/worst months
- **Historical Snapshots**: Track portfolio value over time

#### FIRE Calculator

- **FIRE Number**: Calculate target net worth based on expenses and SWR
- **Years to FIRE**: Projection based on current savings rate
- **What-If Scenarios**: Compare different savings/return scenarios
- **30-Year Projections**: Visualize path to financial independence
- **Customizable Parameters**: SWR (4% default), return rate (7% default)

#### Real Estate Tracking

- **Property Management**: Track properties with payment schedules
- **Partnership Support**: 50% ownership split with partners (e.g., apartment with Alex)
- **Payment Series**: Track ATO, SINAL, MENSAIS, SEMESTRAIS payments
- **Equity Calculation**: Track how much of the property is paid off

#### Liability Management

- **Credit Cards**: Track balances, limits, APR, rewards programs
- **Loans**: Car loans, personal loans with amortization tracking
- **Balance History**: Historical balance tracking
- **Utilization Alerts**: Warn when credit utilization exceeds 30%

### New Files

**Backend Models:**

- `backend/db/models/asset.py` - Enhanced with 20+ asset types, institution/country tracking
- `backend/db/models/real_estate.py` - Property and payment schedule models
- `backend/db/models/liability.py` - Liability and payment tracking models

**Backend Services:**

- `backend/services/insights_calculator.py` - Net worth, allocation, growth calculations
- `backend/services/fire_calculator.py` - FIRE planning calculations

**Backend API:**

- `backend/api/insights.py` - Insights endpoints (/v1/insights/\*)

**Frontend Pages:**

- `frontend/pages/insights.tsx` - Insights dashboard with charts
- `frontend/pages/settings/integrations.tsx` - Integrations settings page

**Database Migrations:**

- `backend/alembic/versions/20260131_0002_add_insights_models.py`

**Scripts:**

- `backend/scripts/seed_portfolio.py` - Seed script for portfolio data

### API Endpoints Added

```
GET  /v1/insights/summary           - Complete insights summary
GET  /v1/insights/net-worth         - Net worth breakdown
GET  /v1/insights/allocation        - Asset allocation
GET  /v1/insights/currency-exposure - Currency exposure analysis
GET  /v1/insights/growth            - Growth metrics
GET  /v1/insights/historical        - Historical net worth data
GET  /v1/insights/fire              - FIRE calculations
POST /v1/insights/fire/calculate    - Custom FIRE calculations
GET  /v1/insights/projections       - Net worth projections
```

### UI Improvements

- Added Insights page to sidebar navigation
- Added Integrations page to sidebar navigation
- Currency switcher (USD/CAD/BRL/EUR) on Insights page
- Interactive FIRE calculator with sliders
- Asset allocation pie charts
- Currency exposure bar charts
- What-if scenario comparisons

### Technical Improvements

- Extended Asset model with 20+ asset types
- Added ownership_percentage for shared assets
- Added sync_source for API integration tracking
- Added institution and country fields for better categorization

---

## [0.2.3-dev] - 2025-01-XX

### Changed

- Updated MASTER_PROMPT.md with project documentation
- Updated backend configuration (config.py)
- Updated Kubernetes deployment manifests (k8s/deploy.yaml)

### Added

- Claude AI settings configuration (.claude/settings.local.json)

## [0.3.0] - 2025-11-13 - 🌳 **Canopy Launch** (Pre-release)

### BREAKING CHANGE - Project Rebranded

**LedgerLight is now Canopy** - Complete rebrand and vision expansion.
**Note**: Still in pre-1.0 development. Version 1.0.0 will be the first production-ready release.

### What's New in Canopy

**Tagline**: "Your financial life. Under one canopy."

**Vision**: Self-hosted personal finance, investment, and budgeting dashboard inspired by Monarch Money, Ghostfolio, and Firefly III. Fully local on Raspberry Pi k3s clusters.

### Changed

- **Project Name**: LedgerLight → Canopy
- **Branding**: New logo featuring tree canopy forming the letter "C"
- **Description**: Expanded vision to emphasize budgeting, investment tracking, and Monarch-level UX
- **Documentation**: Updated README, ARCHITECTURE with Canopy vision
- **Backend**: Renamed API title to "Canopy API"
- **Frontend**: All page titles, meta tags, and OG images updated
- **Database**: Connection strings updated from ledgerlight to canopy
- **Package Names**:
  - `ledgerlight-backend` → `canopy-backend`
  - `ledgerlight-frontend` → `canopy-frontend`

### Migration Guide

See [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) for complete migration instructions including:

- GitHub repository renaming
- Local environment updates
- Brand asset replacement
- Pi cluster deployment updates

### Planned Features (Roadmap)

**MVP+** (In Development):

- Budget management (Fixed/Flexible/Non-monthly envelopes)
- Investment portfolio tracking (stocks, ETFs, crypto)
- Goals tracking (retirement, savings)
- Recurring transaction detection
- Net worth snapshots and charts
- Cash flow analysis (enhanced)
- Celery background tasks for price ingestion

**Deployment**:

- K8s manifests for Pi cluster (eldertree control plane)
- GitHub Actions with self-hosted runner
- Minimal YAML, yearly maintenance philosophy

### Architecture Highlights

**Backend**: FastAPI + Celery + Redis + PostgreSQL  
**Frontend**: Next.js + Tailwind + shadcn  
**Infra**: k3s on Raspberry Pi (eldertree + fleet-worker nodes)  
**Deployment**: kubectl apply (no Helm, no ArgoCD)

### Design Philosophy

- **Self-hosted**: Full privacy, no cloud dependencies
- **Offline-friendly**: Works without internet
- **Multi-currency**: CAD, USD, BRL, EUR, GBP
- **Monarch-level UX**: Polished, calm, premium design
- **Pi-optimized**: Lean, efficient, minimal resource usage
- **Modular**: Easy to fork and extend

### Credits

Built by Rafael Oliveira (@raolivei) for the Pi fleet homelab.

---

## [0.2.2-dev] - 2025-11-04 (Pre-release)

### Fixed

- Fixed currency conversion endpoint returning 500 error
  - **Why:** Pydantic v2 deprecated `dict()` method in favor of `model_dump()`. The error occurred because code was using deprecated API.
  - **Solution:** Updated to use `model_dump()` with fallback to `dict()` for backward compatibility.
- Updated to use `model_dump()` for Pydantic v2 compatibility in transaction currency conversion
- Added fallback to `dict()` for Pydantic v1 support
- Currency conversion query parameter now works correctly (`/v1/transactions/?currency=CAD`)

### Added

- Comprehensive architecture documentation (ARCHITECTURE.md)
  - **Why:** Document design decisions and rationale to help future developers understand the "why" behind technical choices
  - **Contents:** Architecture overview, technology choices, API design, frontend architecture, data management, security considerations, performance optimizations
- Enhanced documentation with "why" explanations
  - **Why:** Understanding rationale helps maintainability and prevents regression of design decisions
  - **Updated:** MASTER_PROMPT.md, README.md, CHANGELOG.md with design rationale sections

## [0.2.1-dev] - 2025-11-04 (Pre-release)

### Fixed

- Integrated transaction and currency routers into server.py
  - **Why:** Feature branches created routers separately. Integration ensures all endpoints are accessible.
  - **Solution:** Conditional import pattern allows routers to work even if some are missing.
- Added CORS middleware for frontend-backend communication
  - **Why:** Browser Same-Origin Policy blocks cross-origin requests. Frontend (port 3000) needs to call backend (port 8000).
  - **Solution:** CORS middleware explicitly allows frontend origin.
- Added missing transaction model to dev branch
  - **Why:** Transaction API requires Transaction model but it was only in feature branch.
  - **Solution:** Added model to dev branch to ensure complete functionality.
- Verified all API endpoints working correctly
- Stable application state with full functionality

## [Unreleased]

### Added

- **Backend API Setup** (`feature/backend-api-setup`):
  - FastAPI application with CORS middleware configuration
  - Transaction models (Transaction, TransactionCreate, TransactionType enum)
  - Transaction CRUD API endpoints (GET all, GET by ID, POST, DELETE)
  - Health check endpoint at `/v1/health`
  - Python requirements.txt with FastAPI, Uvicorn, SQLAlchemy, Pydantic dependencies
  - In-memory transaction storage (ready for database migration)

- **UI Redesign** (`feature/ui-redesign-monarch-style`):
  - Modern Monarch Money-inspired UI design
  - Sidebar navigation component with active state highlighting
  - Reusable StatCard component for dashboard metrics
  - Redesigned dashboard with:
    - Cash flow area chart (income vs expenses over time)
    - Spending by category pie chart
    - Recent transactions list
    - Summary stat cards (Total Income, Expenses, Net Cash Flow, Spending)
  - Redesigned transactions page with improved layout and card-based summaries
  - Custom Tailwind CSS components (card, card-hover, btn-primary, btn-secondary, input-modern)
  - Tailwind configuration with primary color palette and Inter font family
  - Responsive grid layouts and modern card designs

- **Currency Support** (`feature/currency-support`):
  - Multi-currency support (USD, CAD, BRL, EUR, GBP)
  - Currency API endpoints (`/v1/currency/supported`, `/v1/currency/rates`, `/v1/currency/convert`)
  - Currency conversion logic with mock exchange rates
  - CurrencySelector component for frontend
  - Currency formatting utilities (formatCurrency, convertCurrency, formatCurrencyCompact)
  - Transactions API support for optional currency conversion
  - Display currency toggle in UI
  - Show both original and converted amounts when currencies differ

- **Dark Mode** (`feature/dark-mode`):
  - DarkModeToggle component with localStorage persistence
  - System preference detection for automatic dark mode
  - Dark mode styles throughout all UI components
  - Integration in sidebar and page headers
  - Tailwind class-based dark mode configuration
  - SSR-safe implementation to prevent hydration mismatches

- **Placeholder Pages** (`feature/placeholder-pages`):
  - Portfolio page with stat cards for investment metrics
  - Accounts page with account cards (Checking, Credit Card, Savings)
  - Settings page with currency selector, dark mode toggle, and placeholder sections
  - All pages include proper Next.js Head components and dark mode support

- **Documentation** (`docs/master-prompt`):
  - Comprehensive MASTER_PROMPT.md with complete application recreation guide
  - Project structure documentation
  - Setup instructions for backend and frontend
  - API specifications and data models
  - UI/UX design system documentation
  - Complete feature roadmap with implementation phases
  - Troubleshooting guide and development workflow

### Fixed

- **SSR and State Fixes** (`bugfix/ssr-and-state-fixes`):
  - Fixed missing `showConverted` and `convertedAmounts` state variables in transactions page
  - Fixed SSR error with `document` access in chart tooltips
  - Added `isDarkMode` state tracking for client-side dark mode detection
  - Prevented hydration mismatches in dark mode toggle component

## [0.1.0-dev] - 2025-11-03 (Pre-release)

### Added

- README with detailed objectives, architecture, and onboarding workflows.
- FastAPI backend scaffold featuring:
  - Application factory, configuration via `pydantic-settings`, and cached settings loader.
  - Versioned API routing (`/v1/health`, `/v1/summary`) plus smoke tests.
  - Celery ingest task stub and domain models for portfolio data.
  - Backend-specific Dockerfile, requirements, and `.env` example.
- Next.js 14 + Tailwind frontend setup:
  - KPI dashboard page, reusable layout components, Tailwind theme extension.
  - Static export workflow and Dockerfile for NGINX runtime.
- Infra and delivery tooling:
  - Kubernetes namespace, deployments (API, worker, frontend), services, ingress, and secrets example.
  - Aggregated `ledgerlight.yaml` for single-command deployment.
  - GitHub Actions workflow to build/push container images to GHCR and deploy via `kubectl`.
