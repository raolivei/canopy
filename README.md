# LedgerLight  

LedgerLight is a self-hosted personal finance & investment dashboard that merges portfolio analytics, budgeting, and transaction tracking into one unified platform. It is designed to run on a Raspberry Pi cluster with a lean footprint, storing all data locally without cloud dependencies.  

## Project Objectives  
- Combine portfolio, budgeting, and net-worth views into a single dashboard.  
- Store all data locally — no cloud dependencies.  
- Support multi-currency (CAD, USD, BRL, EUR, GBP) assets.  
- Allow easy CSV/OFX imports for banks and brokerages.  
- Run lean — optimized for Raspberry Pi hardware.  
- Be modular so other developers can fork and extend.  

## Core Features (MVP - Implemented)  
- ✅ Transaction tracking with categories and types (income, expense, transfer)
- ✅ Multi-currency FX conversions with display currency toggle
- ✅ Modern Monarch Money-inspired UI with dark mode support
- ✅ Dashboard with charts and statistics (cash flow, spending by category)
- ✅ Transaction CRUD API endpoints
- ✅ Currency conversion API endpoints
- 📈 Investment tracking (stocks, ETFs, crypto, cash) - Planned
- 💰 Budgeting with categories and goals - Planned
- 🧾 CSV/OFX import & reconciliation - Planned
- 📤 Local backup to S3-compatible storage (MinIO/B2) - Planned
- 🔒 Encrypted secrets (no external vault) - Planned

## Current Version

**v0.2.2** - Stable MVP release with full transaction and currency support.

See [CHANGELOG.md](./CHANGELOG.md) for detailed release notes.

## Quick Start

### Prerequisites
- Python 3.10+ with venv
- Node.js 18+ and npm
- Docker and Docker Compose (for PostgreSQL and Redis)

### Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=/path/to/ledger-light python3 -m uvicorn app.server:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

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
ledgerlight/  
 ├── backend/  
 │   ├── api/          # API endpoints (transactions, currency)
 │   ├── models/       # Pydantic models (transaction, currency)
 │   ├── app/          # FastAPI application
 │   └── ingest/       # CSV/OFX import handlers (planned)
 ├── frontend/  
 │   ├── components/   # React components (Sidebar, StatCard, etc.)
 │   ├── pages/        # Next.js pages (dashboard, transactions, etc.)
 │   └── utils/        # Utility functions (currency formatting)
 ├── k8s/              # Kubernetes manifests
 ├── .github/workflows/  
 │   └── deploy.yml  
 ├── CHANGELOG.md      # Version history
 ├── MASTER_PROMPT.md  # Comprehensive recreation guide
 └── README.md  
```

## Documentation

- **[CHANGELOG.md](./CHANGELOG.md)** - Version history and release notes
- **[MASTER_PROMPT.md](./MASTER_PROMPT.md)** - Complete application recreation guide
- **[test_app.sh](./test_app.sh)** - Test script for verifying functionality
