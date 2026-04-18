# Canopy

**Your financial life. Under one canopy.**

Canopy is a self-hosted personal finance dashboard. The **primary workflow** is a **semi-annual portfolio review**: import structured spreadsheet snapshots (Brazil / Canada / Crypto sections), store history by as-of date, and visualize allocation and total USD over time. Budgeting, bank CSV imports, Wise/Questrade-style integrations, and lot-level holdings remain available under **Advanced / legacy** in the sidebar—they are not the main navigation focus.

It is inspired by Monarch Money, Ghostfolio, and Firefly III, runs fully local on Raspberry Pi k3s clusters with a lean footprint, and stores all data locally without cloud dependencies.

## Project Objectives

- Combine portfolio, budgeting, and net-worth views into a single dashboard.
- Store all data locally — no cloud dependencies.
- Support multi-currency (CAD, USD, BRL, EUR, GBP) assets.
- Allow easy CSV/OFX imports for banks and brokerages.
- Run lean — optimized for Raspberry Pi hardware.
- Be modular so other developers can fork and extend.

### Design Rationale

**Why Single Dashboard?**
Financial health requires seeing the big picture. Combining portfolio, budgeting, and transactions in one view helps users understand their complete financial situation without switching between tools.

**Why Local Storage?**

- **Privacy:** Financial data never leaves your control
- **Security:** No cloud breaches can expose your data
- **Control:** You decide when and how to back up
- **Compliance:** Meets data residency requirements

**Why Multi-Currency?**
Modern users often have assets across currencies. Proper currency support enables accurate net worth calculation and meaningful spending analysis regardless of transaction currency.

**Why CSV/OFX Import?**
Most banks don't offer APIs. CSV/OFX files are universal formats that allow users to import transaction history from any financial institution, making the tool truly platform-agnostic.

**Why Raspberry Pi Optimized?**
Democratizes self-hosting by using affordable, low-power hardware. Enables 24/7 operation without significant electricity costs while maintaining full control over data.

## Core Features

### Transaction Management (✅ Implemented)

- ✅ Transaction tracking with categories and types (income, expense, transfer, buy, sell)
- ✅ Multi-currency FX conversions with display currency toggle
- ✅ Modern Monarch Money-inspired UI with dark mode support
- ✅ Dashboard with charts and statistics (cash flow, spending by category)
- ✅ Transaction CRUD API endpoints
- ✅ Currency conversion API endpoints
- ✅ CSV import with smart format detection (Monarch Money, Chase, Bank of America, etc.)
- ✅ Duplicate detection and validation
- ✅ Investment transaction tracking with ticker symbols
- ✅ Rich transaction data (merchant, notes, tags, original statement)

### Portfolio & Insights (✅ Implemented)

- ✅ Investment portfolio tracking (stocks, ETFs, crypto, retirement accounts)
- ✅ Net worth dashboard with multi-currency support (USD/CAD/BRL/EUR base)
- ✅ Asset allocation by type, currency, country, and institution
- ✅ Currency exposure analysis with risk assessment
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
- 🔄 Moomoo/Futu OpenAPI - UI ready, API pending
- 🔄 Wise API - UI ready, API pending
- ✅ CSV import for all major institutions

### Wealthsimple CSV Auto-Importer (✅ Implemented in 0.8.0)

Canopy ingests Wealthsimple monthly-statement CSV exports end-to-end so net worth (investments + cash − debt) works from a single drop, no API keys required.

**Supported account classes** (auto-classified from filename + header):

- **Investments** → `Asset` (kind `investment_account`): TFSA, TFSA Long, RRSP (`Retirement ⛱️`), FHSA, Emerging (`🇮🇳🇯🇵🇧🇷`), Crypto.
- **Cash** → `Asset` (kind `bank_account`): Chequing.
- **Debt** → `Liability`: credit card, Portfolio line of credit.
- **Skipped**: Direct Indexing (flagged but never written).

**How it works**:

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

### Planned Features

- 💰 Budgeting with categories and goals
- 🧾 OFX import
- 📤 Local backup to S3-compatible storage (MinIO/B2)
- 🔒 Encrypted secrets (no external vault)
- 📊 Dividend calendar and income streams

## Current Version

**v0.4.0** - Insights & FIRE Planning release with portfolio analytics.

See [CHANGELOG.md](./CHANGELOG.md) for detailed release notes.

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
- 💰 Multi-currency support
- 📊 Import preview before committing
- 🏷️ Rich data support (merchant, tags, notes, original statement)
- 📈 Investment transaction tracking (Buy/Sell with ticker symbols)
- 📝 Import history tracking

See **[CSV_IMPORT_GUIDE.md](./CSV_IMPORT_GUIDE.md)** for detailed instructions and examples.

## Insights & FIRE Planning

The Insights page (`/insights`) provides comprehensive financial analytics:

### Net Worth Dashboard

- Total net worth with multi-currency support
- Assets vs liabilities breakdown
- Currency exposure analysis
- Growth metrics (monthly, yearly, YTD)

### FIRE Calculator

Calculate your path to Financial Independence:

- **FIRE Number**: Target net worth based on your expenses
- **Years to FIRE**: How long until you reach financial independence
- **Progress**: Visual progress bar showing % complete
- **Projections**: 30-year net worth projections

Default assumptions (customizable):

- Monthly expenses: $5,000 CAD (~$3,600 USD)
- Safe Withdrawal Rate: 4%
- Expected Return: 7%

### What-If Scenarios

Compare different scenarios:

- Save $500 more per month
- Save $1000 more per month
- Reduce expenses by 10%
- 8% vs 7% vs 5% annual returns

## Database Seeding

To populate the database with sample data:

```bash
cd backend

# Seed the database
python -m backend.scripts.seed_portfolio

# Clear and reseed
python -m backend.scripts.seed_portfolio --clear
```

The seed script includes:

- 40+ accounts across Canada, USA, and Brazil
- Historical snapshots from Sep 2024 to present
- Real estate (apartment with 50% ownership)
- Liabilities (credit cards, car loan)
- Crypto holdings (by platform and aggregated by coin)

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
- [#22 - Moomoo API Integration](https://github.com/raolivei/canopy/issues/22)
- [#23 - Wise API Integration](https://github.com/raolivei/canopy/issues/23)
- [#24 - Dividend Tracking](https://github.com/raolivei/canopy/issues/24)
- [#25 - Real-time Currency Rates](https://github.com/raolivei/canopy/issues/25)
- [#26 - Property Value Estimation](https://github.com/raolivei/canopy/issues/26)
