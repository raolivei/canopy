# Canopy

**Your Canadian investments. Under one canopy.**

Canopy is a self-hosted Canadian-investment tracker built around **continuous net-worth tracking in CAD**:

- **Drop Wealthsimple statements** (any mix of TFSA / RRSP / FHSA / Crypto / Chequing / Credit Card / Line of Credit CSVs) — they're auto-classified into investments, cash, and debt and de-duplicated on re-import. Accounts are created automatically; they show up under Accounts (cash + credit + LOC) or Holdings (investments).
- **Capture CAD-denominated holdings that don't auto-sync** (private equity, real estate, DPSP) as dated **portfolio review snapshots** — TSV/CSV in, history by as-of date out.
- **See one net-worth number in CAD** on the dashboard (investments + cash − debt), with a combined timeline chart built from every statement drop and every review snapshot.

It is inspired by Monarch Money, Ghostfolio, and Firefly III, runs fully local on Raspberry Pi k3s clusters (accessed privately over Tailscale — never on the public internet), and stores all data locally without cloud dependencies.

## Project Objectives

- A single dashboard for Canadian net-worth tracking — investments, cash, and debt in **CAD only**.
- Drop-in Wealthsimple statement support; Questrade / Wise / RBC CSV next.
- Store all data locally — no cloud dependencies.
- Accounts page separates bank / credit / LOC from investment holdings.
- Run lean — optimized for Raspberry Pi hardware.
- Modular so other developers can fork and extend.

### Design Rationale

**Why Single Dashboard?**
Financial health requires seeing the big picture. Combining portfolio, budgeting, and transactions in one view helps users understand their complete financial situation without switching between tools.

**Why Local Storage?**

- **Privacy:** Financial data never leaves your control
- **Security:** No cloud breaches can expose your data
- **Control:** You decide when and how to back up
- **Compliance:** Meets data residency requirements

**Why CAD Only?**
Scope keeps the product simple and the UX uncluttered. Canopy is built for Canadians tracking Canadian-registered accounts (TFSA / RRSP / FHSA / DPSP) and CAD-denominated debt. Foreign-listed securities inside a Wealthsimple account are still imported — only the reporting currency is fixed.

**Why CSV/OFX Import?**
Most banks don't offer APIs. CSV/OFX files are universal formats that allow users to import transaction history from any financial institution, making the tool truly platform-agnostic.

**Why Raspberry Pi Optimized?**
Democratizes self-hosting by using affordable, low-power hardware. Enables 24/7 operation without significant electricity costs while maintaining full control over data.

## Core Features

### Wealthsimple CSV Auto-Importer (✅ Primary input channel — 0.8.0)

Canopy ingests Wealthsimple monthly-statement CSV exports end-to-end so net worth (investments + cash − debt) works from a single drop, no API keys required.

**Supported account classes** (auto-classified from filename + header):

- **Investments** → `Asset`: TFSA, TFSA Long, RRSP (`Retirement ⛱️`), FHSA, Emerging (`🇮🇳🇯🇵🇧🇷`), Crypto. Shown on **Holdings**.
- **Cash** → `Asset` (`BANK_CHECKING`): Chequing. Shown on **Accounts**.
- **Debt** → `Liability`: credit card, Portfolio line of credit. Shown on **Accounts**.
- **Skipped**: Direct Indexing (flagged but never written).

**Flow**:

1. Drop any mix of CSVs at `/portfolio/wealthsimple-import`.
2. Preview shows account label, type, row counts, duplicates, and warnings.
3. Commit writes normalized `Transaction`, `Lot` (on BUY), `Dividend` (on DIV), `AccountBalanceHistory` / `LiabilityBalanceHistory` end-of-statement snapshots. Credit-card balances are reconstructed from `opening_balance + sum(deltas)`.
4. Each row is hashed into `ImportedEvent` so re-dropping the same file is a no-op.
5. Dashboard net-worth hero and timeline chart (`/v1/wealthsimple-import/networth-timeline`) update immediately.

**Relevant files**:

- Backend: `backend/services/wealthsimple/{filename_parser,row_parser,description_parser,importer}.py`, `backend/api/wealthsimple_import.py`
- Frontend: `frontend/pages/portfolio/wealthsimple-import.tsx`, `frontend/pages/index.tsx` (net-worth hero)
- Migration: `backend/alembic/versions/20260419_0007_add_liability_opening_balance.py`
- Tests: `backend/tests/test_wealthsimple_{filename_parser,description_parser,importer}.py` (30 tests)

### Portfolio Review Snapshots (✅ Implemented in 0.7.0, CAD-only in 0.9.0)

For CAD-denominated holdings that don't export a machine-readable CSV (private equity, real estate, DPSP), drop a TSV/CSV snapshot at `/portfolio/import` and Canopy persists it as a dated review row. Non-Canadian sections (Brazil, Crypto) in legacy spreadsheets are ignored; only the Canadian block is ingested.

### Transaction Management (✅ Implemented)

- ✅ Transaction tracking with categories and types (income, expense, transfer, buy, sell)
- ✅ Single-currency (CAD) display across the app
- ✅ Modern Monarch Money-inspired UI with dark mode support
- ✅ Dashboard with charts and statistics (cash flow, spending by category)
- ✅ Transaction CRUD API endpoints
- ✅ CSV import for Wealthsimple / RBC / TD / Scotiabank / generic CSV
- ✅ Duplicate detection and validation
- ✅ Investment transaction tracking with ticker symbols
- ✅ Rich transaction data (merchant, notes, tags, original statement)

### Portfolio & Insights (✅ Implemented)

- ✅ Investment portfolio tracking (stocks, ETFs, crypto, registered accounts TFSA / RRSP / FHSA / DPSP)
- ✅ Net worth dashboard in CAD
- ✅ Asset allocation by type, country, and institution
- ✅ Growth metrics (monthly/yearly rates, best/worst months)
- ✅ Historical portfolio snapshots and trends
- ✅ Real estate tracking with payment schedules (50% partnership support)
- ✅ Liability tracking (credit cards, loans, mortgages)

### FIRE Planning (✅ Implemented)

- ✅ FIRE number calculation (based on expenses and safe withdrawal rate)
- ✅ Years-to-FIRE projection with compound growth
- ✅ 30-year net worth projections
- ✅ What-if scenarios (save more, different returns, reduce expenses)
- ✅ Passive income projections at FIRE

### Integrations (🔄 In Progress)

- 🔄 Questrade API (OAuth 2.0) - UI ready, API pending
- 🔄 Wise API - UI ready, API pending (CAD balance only)
- 🔄 RBC Canada CSV export - planned
- ✅ Wealthsimple CSV drop (`/portfolio/wealthsimple-import`)

### Planned Features

- 💰 Budgeting with categories and goals
- 🧾 OFX import
- 📤 Local backup to S3-compatible storage (MinIO/B2)
- 🔒 Encrypted secrets (no external vault)
- 📊 Dividend calendar and income streams

## Current Version

**v0.8.0** — Wealthsimple CSV auto-importer + unified net-worth dashboard. See [CHANGELOG.md](./CHANGELOG.md).

## Deployment & Security

Canopy handles personal financial data (bank transactions, investment positions, account numbers, net worth). The recommended deployment:

- **Private ingress only** — expose `canopy.eldertree.local` inside the cluster and **do not** publish a public `canopy.eldertree.xyz` (or equivalent) host. HTTP Basic Auth on a public URL is not sufficient protection for this data.
- **Access from anywhere via Tailscale** — all client devices (Mac, iOS, Android) join the tailnet and resolve `canopy.eldertree.local` through Pi-hole. See `pi-fleet/docs/TAILSCALE.md` in the infra repo for the iOS/Android setup.
- **Secrets in Vault** — database passwords and any future API keys are managed by External Secrets Operator, never committed to Git.

## Quick Start

### Prerequisites

- Docker and Docker Compose (recommended)
- Python 3.11+ with venv (for local development fallback)
- Node.js 18+ and npm (for local development fallback)
- k3s cluster (optional, for production deployment)

### Recommended: Docker Compose (Primary Method)

```bash
# Load port assignments from workspace-config
source ../workspace-config/ports/.env.ports

# Start all services with hot reload
docker-compose up

# Or start in detached mode
docker-compose up -d
```

**Access:**

- Frontend: http://localhost:3001
- API: http://localhost:8001
- API Docs: http://localhost:8001/docs

**Benefits:**

- Consistent environment (matches production)
- Hot reload enabled via volume mounts
- No local Python/Node version conflicts
- Single command to start everything

See `../workspace-config/docs/DOCKER_COMPOSE_GUIDE.md` for complete guide.

### Alternative: Local Development (Fallback)

#### Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=/path/to/canopy python3 -m uvicorn app.server:app --reload --host 0.0.0.0 --port 8001
```

**Why PYTHONPATH?**
Python needs to find the `backend` module for absolute imports (`from backend.api import ...`). Setting PYTHONPATH to project root allows imports to work regardless of current directory.

**Why `--reload`?**
Enables auto-reload on code changes during development, speeding up iteration. Remove in production for better performance.

**Why `0.0.0.0`?**
Binds to all network interfaces, allowing access from other devices on your network (e.g., testing on mobile). Use `127.0.0.1` for localhost-only access.

#### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

**Why Separate Processes?**
Backend and frontend are independent services. Separating them allows:

- Independent scaling
- Different deployment strategies
- Team members to work on one without affecting the other
- Technology choices (Python backend, Node.js frontend)

### Testing

Run the test script to verify all functionality:

```bash
./test_app.sh
```

### Access

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Repo Structure

```
canopy/
 ├── backend/
 │   ├── api/              # API endpoints
 │   │   ├── portfolio.py      # Portfolio CRUD
 │   │   ├── insights.py       # Insights & FIRE calculations
 │   │   ├── integrations.py   # External API integrations
 │   │   ├── transactions.py   # Transaction management
 │   │   └── currency.py       # Currency conversion
 │   ├── db/               # Database layer
 │   │   ├── models/           # SQLAlchemy ORM models
 │   │   │   ├── asset.py          # Assets (20+ types)
 │   │   │   ├── real_estate.py    # Real estate & payments
 │   │   │   ├── liability.py      # Liabilities & tracking
 │   │   │   └── ...
 │   │   ├── base.py           # SQLAlchemy base
 │   │   └── session.py        # Session management
 │   ├── services/         # Business logic
 │   │   ├── insights_calculator.py  # Net worth, allocation
 │   │   ├── fire_calculator.py      # FIRE planning
 │   │   ├── price_fetcher.py        # Yahoo Finance
 │   │   └── portfolio_calculator.py # Portfolio metrics
 │   ├── scripts/          # Utility scripts
 │   │   └── seed_portfolio.py   # Database seeding
 │   ├── alembic/          # Database migrations
 │   ├── models/           # Pydantic schemas
 │   ├── app/              # FastAPI application
 │   └── ingest/           # CSV import + Celery tasks
 ├── frontend/
 │   ├── components/       # React components
 │   │   ├── AllocationChart.tsx
 │   │   ├── PerformanceChart.tsx
 │   │   ├── PortfolioHoldingsTable.tsx
 │   │   └── ...
 │   ├── pages/            # Next.js pages
 │   │   ├── insights.tsx      # Insights dashboard
 │   │   ├── portfolio.tsx     # Portfolio management
 │   │   ├── settings/
 │   │   │   └── integrations.tsx  # API integrations
 │   │   └── ...
 │   └── utils/            # Utility functions
 ├── k8s/                  # Kubernetes manifests
 ├── .github/workflows/    # CI/CD
 ├── CHANGELOG.md          # Version history
 ├── ARCHITECTURE.md       # Architecture decisions
 └── README.md
```

## CSV Import

Canopy now supports importing transactions from CSV files with smart format detection:

### Supported Formats

- **Monarch Money** - Full support including merchant names, categories, tags, and investment transactions
- **Chase Bank** - Standard CSV export format
- **Bank of America** - Checking and credit card statements
- **Wells Fargo** - Transaction history exports
- **Capital One** - With debit/credit columns
- **American Express** - Card statements
- **TD Bank, RBC, Nubank** - And many more
- **Generic CSV** - Custom field mapping for any format

### Key Features

- 🎯 Automatic format detection
- 🔍 Duplicate transaction detection
- 🇨🇦 CAD-only (USD-listed securities inside Wealthsimple accounts are still imported)
- 📊 Import preview before committing
- 🏷️ Rich data support (merchant, tags, notes, original statement)
- 📈 Investment transaction tracking (Buy/Sell with ticker symbols)
- 📝 Import history tracking

See **[CSV_IMPORT_GUIDE.md](./CSV_IMPORT_GUIDE.md)** for detailed instructions and examples.

## Insights & FIRE Planning

The Insights page (`/insights`) provides comprehensive financial analytics:

### Net Worth Dashboard

- Total net worth in CAD
- Assets vs liabilities breakdown
- Allocation by account type / country / institution
- Growth metrics (monthly, yearly, YTD)

### FIRE Calculator

Calculate your path to Financial Independence:

- **FIRE Number**: Target net worth based on your expenses
- **Years to FIRE**: How long until you reach financial independence
- **Progress**: Visual progress bar showing % complete
- **Projections**: 30-year net worth projections

Default assumptions (customizable):

- Monthly expenses: C$5,000
- Safe Withdrawal Rate: 4%
- Expected Return: 7%

### What-If Scenarios

Compare different scenarios:

- Save $500 more per month
- Save $1000 more per month
- Reduce expenses by 10%
- 8% vs 7% vs 5% annual returns

## Bootstrapping data

Canopy has no seed script — it is designed to be populated from your own statements:

1. Drop a Wealthsimple monthly statement (any combination of TFSA / RRSP / FHSA / Chequing / Credit Card / LOC / Crypto CSVs) at `/portfolio/wealthsimple-import`. Accounts + transactions + balance snapshots are created automatically.
2. (Optional) Drop a CAD portfolio snapshot (TSV/CSV) at `/portfolio/import` for holdings that don't auto-sync (private equity, real estate, DPSP).

Both paths feed the same net-worth timeline and Accounts page.

## Documentation

- **[CHANGELOG.md](./CHANGELOG.md)** - Version history and release notes
- **[MASTER_PROMPT.md](./MASTER_PROMPT.md)** - Complete application recreation guide
- **[CSV_IMPORT_GUIDE.md](./CSV_IMPORT_GUIDE.md)** - CSV import documentation and format guide
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Architecture decisions and rationale
- **[test_app.sh](./test_app.sh)** - Test script for verifying functionality
- **[examples/](./examples/)** - Sample CSV files for different formats

## GitHub Issues

Track ongoing development:

- [#21 - Questrade API Integration](https://github.com/raolivei/canopy/issues/21)
- [#23 - Wise API Integration](https://github.com/raolivei/canopy/issues/23)
- [#24 - Dividend Tracking](https://github.com/raolivei/canopy/issues/24)
- [#25 - Real-time Currency Rates](https://github.com/raolivei/canopy/issues/25)
- [#26 - Property Value Estimation](https://github.com/raolivei/canopy/issues/26)
