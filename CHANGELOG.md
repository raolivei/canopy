# Changelog

Notable releases only — **details belong in commits / PRs**, not here.

## Versioning

Pre-release **0.x**; **1.0.0** when feature-complete.

## [Unreleased]

- **Recurring transactions UI (list, edit, predict):** Complete frontend implementation for recurring pattern management. New page `/recurring` displays detected/stored patterns with list view, detail modal (confidence score, recent occurrences timeline, known delays), and edit form (frequency, amount, next date, active toggle). Components: `RecurringList` (pattern table with approve/edit/delete, active/inactive sections), `RecurringCard` (pattern details with confidence badge and occurrence timeline), `RecurringForm` (edit form with validation). API endpoints: `GET /v1/recurring/detect` (pattern detection with confidence), `GET /v1/recurring/` (list stored patterns), `POST /v1/recurring/` (approve/save pattern), `PUT /v1/recurring/{id}` (update), `DELETE /v1/recurring/{id}` (delete). Database model `RecurringPattern` stores merchant, category, average_amount, variance, frequency, next_expected, confidence, occurrences, skip_dates. Migration `20260613_0018`. Frontend uses TanStack React Query for data fetching; styled modals for batch approval of detected patterns. Test at http://localhost:3001/recurring.
- **Assistant high-value tools (6 new):** Expanded `AssistantService` with 6 high-value tools for Monarch parity. Added tools: `get_accounts()` (all account types, balances, currency), `get_budget_status()` (current month budget vs actuals by category), `get_recurring_summary()` (detected recurring transactions with confidence), `get_cashflow_analysis()` (monthly income/expenses/savings trend), `analyze_spending_patterns()` (top merchants/categories, trends), `get_merchant_insights()` (spending history per merchant). Each tool callable via LLM function calling; returns structured JSON. Full unit test coverage (25+ tests) in `test_assistant_tools.py` with SQLite in-memory DB fixtures. Tools integrate with `RecurringService` (pattern detection), `BudgetService` (budget tracking), and transaction queries for data-driven assistant responses.
- **Transaction rules engine:** Auto-categorization, tagging, and splitting system for transaction automation. Models: `Rule` (metadata, priority), `RuleCondition` (field, operator, value), `RuleAction` (action_type, config). Supports 7 match operators (equals, contains, regex, starts_with, ends_with, greater_than, less_than) and 3 action types (set_category, add_tag, split). Service: `RuleService` with rule creation/update/delete, condition evaluation (AND logic), action application, and batch processing. Priority-based rule ordering. Comprehensive test suite with 25+ test cases covering condition matching, action application, and CRUD operations. Migration `20260613_0015` creates rules, rule_conditions, rule_actions tables.
- **Category taxonomy:** Formalized transaction categories with hierarchy support for Monarch parity. New `categories` table with parent-child relationships, Monarch category name preservation, and UI metadata (color, icon). Models: `Category` with hierarchy methods (`get_path()`, `get_children()`, `get_descendants()`, `is_root()`, `is_leaf()`). Transactions now have `category_id` FK while preserving legacy `category` string for backwards compatibility. Seeded default categories: Income, Expenses (with subcategories: Groceries, Dining Out, Utilities, Transportation, Shopping, Entertainment, Healthcare, Fees), Transfers, Investments, Debt. Migration `20260613_0016` creates schema; `20260613_0017` populates existing transactions by matching category strings to formal records. Supports future category filtering in budgets, rules, and cashflow analysis.

## [0.11.0] - 2026-06-12

- **Cashflow service:** Added `CashflowService` for monthly cashflow analysis. Methods: `get_monthly_metrics()` returns monthly income/expenses/savings/rate + top categories; `get_cashflow_trend(months)` returns last N months of metrics; `get_cashflow_summary(start_date, end_date)` calculates aggregate totals and trend direction. Handles edge cases: zero income (savings_rate=0), uncategorized transactions, and trend calculation via first/second-half savings rate comparison. Full unit test coverage with SQLite in-memory database.
- **Budget models:** Added `Budget`, `BudgetCategory`, and `BudgetTracking` models for Monarch parity P1 feature. Supports recurring budget periods (MONTHLY, QUARTERLY, ANNUAL), rollover behavior, and budget tracking history. Database migration `20260612_0014` creates `budgets`, `budget_categories`, and `budget_tracking` tables with appropriate indexes for fast lookups and period-based queries.
- **Budget API endpoints:** Added `/v1/budgets/*` REST endpoints for CRUD operations and tracking:
  - `GET /v1/budgets/` - List all budgets (with `active_only` filter)
  - `POST /v1/budgets/` - Create new budget
  - `GET /v1/budgets/{budget_id}` - Get budget with all categories
  - `PUT /v1/budgets/{budget_id}` - Update budget metadata (name, description, is_active)
  - `DELETE /v1/budgets/{budget_id}` - Delete budget and all categories
  - `POST /v1/budgets/{budget_id}/categories` - Add category to budget with limit
  - `GET /v1/budgets/{budget_id}/tracking` - Get budget vs actuals for date range
  - All endpoints include comprehensive error handling (404, 400) and auto-generated Swagger docs.
- **Navigation:** Added sidebar links for new Monarch parity features: Budgets (PieChart icon), Cashflow (TrendingDown icon), and Recurring (Repeat icon). Placeholder pages created at `/budgets`, `/cashflow`, and `/recurring` for P2 feature development. Mobile navigation via Settings menu.

## [0.10.4] - 2026-05-26

- **Workspace config adoption:** Extend shared Ruff config from workspace-config/python/ruff.toml; symlink ESLint config for Next.js frontend; add Dependabot for automated dependency updates.

## [0.10.5] - 2026-05-01

- **AI Assistant:** Floating chatbot available on all pages (⌘⇧A to toggle). Natural language queries for transactions, spending, portfolio. Features: suggested questions, copy responses, conversation history, function calling with data access. Backend provider abstraction (Ollama/OpenClaw) via `ASSISTANT_PROVIDER` env var. PostgreSQL storage. UI: glassmorphism design, smooth animations, keyboard shortcuts, mobile full-screen.
- **Config consolidation:** Removed `.cursorrules` and `.claude-plugin/` in favor of `CLAUDE.md` as single source of truth for Claude Code project conventions.
- **Database migration:** `20260501_0013` adds `assistant_conversations` and `assistant_messages` tables for chat history.
- **Dependencies:** Added `ollama>=0.3.0` and `openai>=1.0.0` to backend requirements for LLM provider integration.

## [0.10.4] - 2026-04-19

- **Agent / workflow:** `.cursorrules` + **Cursor skills** (`canopy-agent-conventions`, `canopy-backend-patterns`) require **local pytest / lint before push**, not CI as the first signal.
- **Monarch parser:** Dropped the loose **`individual`** investment substring (it matched everyday bank labels like **`Individual (...)`** and routed them to **INVESTMENT**, so `/v1/accounts` stayed empty while `/v1/transactions` showed rows). Tightened markers to **`individual investing`**, **`individual brokerage`**, **`brokerage`**; added **Amex / Discover** debt hints. **Follow-up:** those **`Individual (...last4)`** labels then became **UNKNOWN**, so the importer skipped them and **Accounts** still had nothing — classify **`Individual`/`Joint` + `(...` mask** as **CASH** (still not **`Individual Investing (...)`**). **Further:** normalise Unicode **ellipsis** (`…` → `...`); allow spaces after **`(`** in the mask; add TD-style **cash** substrings (**`banking plan`**, **`all-inclusive`**, **`borderless`**, **`minimum balance`**). **`GET /v1/accounts`** now also lists legacy **`assets.asset_type = other`** rows from **`csv_import`** when the **current** Monarch classifier says **CASH**, so old mis-stored rows show without a full re-import.
- **Alembic `20260423_0011`:** purge migration now deletes **`snapshot_holdings`** (was wrongly checking **`portfolio_snapshot_holdings`**) before removing BR-scoped **`assets`**, avoiding FK failures on `snapshot_holdings_asset_id_fkey` when upgrading old databases.
- **Admin row counts / migrations:** `GET /v1/admin/row-counts` uses **`COUNT(*)`** per table (not ORM `.count()`) so liabilities counts work when the table exists but a newer column is not migrated yet. **`backend/scripts/migrate.sh`** documents **`alembic upgrade head`** for Compose and k8s; production still requires migrations for tables such as **`fx_rates`** and **`portfolio_reviews`**.
- **Settings danger zone / production:** API **CORS** accepts **`CORS_ALLOW_ORIGINS`** (Helm: `canopy.eldertree.xyz` + `.local`). Settings admin fetches use **`credentials: 'include'`**. Frontend image **`NEXT_PUBLIC_API_URL`** defaults empty at build (same-origin `/v1`); removed invalid cluster-only URL from sample k8s. **Do not** set `NEXT_PUBLIC_API_URL` to in-cluster service names in Kubernetes — they are not reachable from the browser.
- **Transactions page:** list/create/delete now call **`NEXT_PUBLIC_API_URL`** (same as Accounts / imports), so Monarch- and Wise-imported rows appear instead of failing silently when the frontend and API run on different origins.
- **Navigation:** **Transactions** promoted to primary sidebar (after Accounts) and added to mobile bottom bar (**Txns**); removed the old collapsed **Advanced** section that hid it.

## [0.10.3] - 2026-04-19

- **Integrations:** Questrate accepts **`QUESTRADE_REFRESH_TOKEN`** from the environment when the request body omits a token (same pattern as **`WISE_API_TOKEN`**), so Vault / External Secrets can inject broker tokens without storing them in the browser. **`GET /v1/integrations/questrade/status`** mirrors Wise; Settings → Integrations lets you Connect / Sync with an empty field when the API has that env var.
- **Wealthsimple:** map Shape-A transaction codes **SPEND** (cash-account debit) and **TRFINTF** (registered transfer in) so monthly statements do not surface unknown-code warnings.
- **CSV import:** Amex Canada **Year-End Summary** preset (`Charges $` / `Credits $`, DD/MM/YYYY); **monthly statement** preset (`Date` / `Amount` / `Account #`, `17 Apr 2026` dates); detection when using Generic CSV; Import options **Amex Year-End Summary (CA)** and **Amex Monthly Statement (CA)**; Monarch default no longer mis-maps those files when headers match.
- README refresh; FIRE optional CAGR from snapshots; net worth chart (stacked area + debt axis); portfolio dividends + positions split; accounts grouping; nav/import/integrations polish + logos; privacy "hide amounts"; **Cursor** project agent skills under `.cursor/skills/` (repo conventions, stack map, UI/backend/import notes).
- Wise sync writes prices; insights use balance history; holdings cash rows show display name (hide Monarch internal symbols). Wise balances ignore CSV balance-history rows so snapshots never override API `current_price` with $0.
- **FX**: If BoC/USDCAD is not cached yet, combined CAD/USD views use a **1.35 display fallback** (backend + portfolio) so balances do not all show as $0; rate is still flagged stale when approximate.
- CI may tag `v$(VERSION)` after image push on `main`.
- **API**: `GET /v1/transactions/annual-report` registered before `/{id}` (fixes 422); `year` query optional (defaults to current calendar year). **UI**: Privacy toggle mount-gates lucide icons (Dark Reader hydration).
- **Dev:** `docker-compose.yml` drops obsolete Compose `version` key (silences CLI warning).

## [0.10.2] - 2026-04-18

- Monarch **Balances** CSV importer + unified monarch file drop; API `{transactions, balances}`; classifier/parser broadened.

## [0.10.1] - 2026-04-18

- Danger Zone reset UI; WS net-worth timeline includes lot book value; accounts from latest balance history; holdings `Decimal` / `$0` fixes; MobileNav hydration guard.

## [0.10.0] - 2026-04-18

- BoC **USDCAD** store + `/v1/fx/*`; **currency view** (CAD / USD / combined) across dashboard, accounts, holdings, timeline; hooks `useCurrencyView` / `useFxRate`.

## [0.9.0] - 2026-04-18

- **Wise integration:** Automated balance sync via Wise API; **`GET /v1/integrations/wise/sync-balances`** fetches multi-currency balances, creates/updates Assets (`type=wise_balance`, USD/EUR/...), writes native-currency balance history, stores FX rates and asset prices; Settings → Integrations shows real-time Wise balance status. **Questrade:** `sync_questrade` Celery task (Questrade account fetch + balance store).
- **Insights endpoint**: `GET /v1/insights/calculate` aggregates holdings, liabilities, dividends, FIRE projection, allocations.
- **Dashboard timeline**: Net worth line chart from portfolio snapshots; YTD performance card; allocation donut with `recharts`.
- **Accounts**: Cash/debt tab; liability rows; balance history; multi-currency display.
- **Holdings**: Performance metrics; lots & cost basis; dividends table; allocation charts.
- **UI polish**: Card stats; table components; dark mode fixes; mobile nav; privacy mode toggles.

## [0.8.0] - 2026-04-14

- Wealthsimple monthly statements parser (Shape-A CSV with monthly sub-CSVs); Monarch Transactions importer; unified CSV classification pipeline; admin debug endpoints.

## [0.7.0] - 2026-04-13

- Portfolio snapshots + holdings; lot tracking; dividend records; real estate assets; liability support; balance history; admin purge endpoints.

## [0.6.0] - 2026-04-11

- FX rate caching (BoC Valet API); portfolio calculations service; multi-currency views.

## [0.5.0] - 2026-04-10

- Celery task queue; Redis integration; Questrade background sync.

## [0.4.0] - 2026-04-08

- Transaction CRUD; categories; CSV import; generic parsers.

## [0.3.0] - 2026-04-06

- Asset management; holdings tracking; price history.

## [0.2.0] - 2026-04-04

- PostgreSQL schema; Alembic migrations; SQLAlchemy ORM.

## [0.1.0] - 2026-04-02

- Initial FastAPI backend scaffold; Next.js frontend; Docker Compose setup; k8s manifests.
