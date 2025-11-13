# Canopy  

**Your financial life. Under one canopy.**

Canopy is a self-hosted personal finance, investment, and budgeting dashboard inspired by Monarch Money, Ghostfolio, and Firefly III. It runs fully local on Raspberry Pi k3s clusters with a lean footprint, storing all data locally without cloud dependencies.  

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

## Core Features (MVP - Implemented)  
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
- 📈 Investment portfolio tracking (stocks, ETFs, crypto, cash) - Planned
- 💰 Budgeting with categories and goals - Planned
- 🧾 OFX import - Planned
- 📤 Local backup to S3-compatible storage (MinIO/B2) - Planned
- 🔒 Encrypted secrets (no external vault) - Planned

## Current Version

**v0.2.2-dev** - Development build with MVP features (pre-release, not for production use).

See [CHANGELOG.md](./CHANGELOG.md) for detailed release notes.

## Quick Start

### Prerequisites
- Python 3.11+ with venv
- Node.js 18+ and npm
- Docker and Docker Compose (for PostgreSQL and Redis)
- k3s cluster (optional, for production deployment)

### Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=/path/to/canopy python3 -m uvicorn app.server:app --reload --host 0.0.0.0 --port 8000
```

**Why PYTHONPATH?**
Python needs to find the `backend` module for absolute imports (`from backend.api import ...`). Setting PYTHONPATH to project root allows imports to work regardless of current directory.

**Why `--reload`?**
Enables auto-reload on code changes during development, speeding up iteration. Remove in production for better performance.

**Why `0.0.0.0`?**
Binds to all network interfaces, allowing access from other devices on your network (e.g., testing on mobile). Use `127.0.0.1` for localhost-only access.

### Frontend Setup
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
 │   ├── api/          # API endpoints (transactions, currency, budgets, goals)
 │   ├── models/       # Pydantic models (transaction, budget, goal, holdings)
 │   ├── app/          # FastAPI application
 │   ├── ingest/       # CSV/OFX import handlers + Celery tasks
 │   └── celery/       # Celery config and workers
 ├── frontend/  
 │   ├── components/   # React components (Sidebar, StatCard, Charts, etc.)
 │   ├── pages/        # Next.js pages (dashboard, transactions, budget, goals, etc.)
 │   └── utils/        # Utility functions (currency, formatting, charts)
 ├── k8s/              # Kubernetes manifests for Pi cluster
 ├── .github/workflows/  
 │   └── deploy.yml    # Self-hosted runner CI/CD
 ├── CHANGELOG.md      # Version history
 ├── ARCHITECTURE.md   # Architecture decisions
 └── README.md  
```

## CSV Import

LedgerLight now supports importing transactions from CSV files with smart format detection:

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

## Documentation

- **[CHANGELOG.md](./CHANGELOG.md)** - Version history and release notes
- **[MASTER_PROMPT.md](./MASTER_PROMPT.md)** - Complete application recreation guide
- **[CSV_IMPORT_GUIDE.md](./CSV_IMPORT_GUIDE.md)** - CSV import documentation and format guide
- **[test_app.sh](./test_app.sh)** - Test script for verifying functionality
- **[examples/](./examples/)** - Sample CSV files for different formats
