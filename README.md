# Canopy

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Node](https://img.shields.io/badge/node-18+-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)
![Next.js](https://img.shields.io/badge/Next.js-14.0-black.svg)
![Version](https://img.shields.io/badge/version-0.10.4-blue.svg)
![PR Checks](https://github.com/raolivei/canopy/actions/workflows/pr.yml/badge.svg)
![Build](https://github.com/raolivei/canopy/actions/workflows/build-and-push.yml/badge.svg)

**Personal finance dashboard — self-hosted, privacy-first.**

Canopy is a Canadian-focused personal finance app with **CAD + USD** multi-currency support. Track net worth, investments, and spending through Wealthsimple and Monarch CSV imports, optional **Wise** API and **Questrade** integrations, portfolio holdings, cash/credit accounts, insights, FIRE calculator, and an **AI assistant** for natural language queries. All data stays on your infrastructure (k3s cluster, Raspberry Pi, Tailscale access).

## What it does

| Area | Description |
|------|-------------|
| **Dashboard** | Net worth timeline from Wealthsimple statements + Monarch balances; stacked area chart with debt axis; currency toggle (CAD / USD / combined). YTD performance tracking. |
| **Import** | Wealthsimple monthly statements (Shape-A CSV), Monarch transactions + balances, Amex Canada (Year-End Summary / Monthly Statement), generic bank CSV, legacy portfolio snapshots. |
| **Portfolio** | Holdings with performance metrics, cost basis, lots tracking; allocation charts; dividends table; positions split by securities vs cash/registered accounts. |
| **Accounts** | Cash and debt tabs; chequing, savings, credit cards, lines of credit; balance history; multi-currency display; grouping by institution or account type. |
| **Transactions** | Full transaction CRUD; categories; search and filtering; annual reports; natural language queries via AI assistant. |
| **Insights** | Net worth trends, allocation analysis, growth from snapshots; **FIRE calculator** with default 7% return or **CAGR from portfolio snapshots** (requires ≥60 days of history). |
| **Integrations** | **Wise API** (automated CAD/USD balance sync), **Questrade** (OAuth refresh token for account fetch). |
| **AI Assistant** | Floating chatbot (⌘⇧A) for natural language queries about spending, transactions, portfolio. Supports OpenClaw (cluster-hosted) and Ollama (local). Function calling with conversation history. |

## Stack

- **Backend:** FastAPI, SQLAlchemy, PostgreSQL, Alembic, Celery, Redis  
- **Frontend:** Next.js 14, React 18, React Query (TanStack Query), Tailwind CSS, Recharts, Framer Motion  
- **FX:** Bank of Canada Valet API for USDCAD rate caching (`fx_rates` table)  
- **AI:** OpenClaw/Ollama integration with function calling for natural language queries  
- **Testing:** pytest (backend), Jest/ESLint (frontend)  
- **Code Quality:** Ruff (Python formatting/linting), ESLint (TypeScript)  

Default local ports (see `docker-compose` / workspace config): **frontend `3001`**, **API `8001`**, **PostgreSQL `5433`**, **Redis `6380`**.

## Quick start

### Docker Compose (Recommended)

```bash
# From canopy/ directory, with workspace port env if you use it:
source ../workspace-config/ports/.env.ports   # optional
docker-compose up
```

- **App:** http://localhost:3001  
- **API docs:** http://localhost:8001/docs  
- **Postgres:** localhost:5433  
- **Redis:** localhost:6380  

**Environment variables** (create `.env` file or set in shell):

```bash
# Required for frontend to reach API from browser
NEXT_PUBLIC_API_URL=http://localhost:8001

# Optional: AI Assistant (choose one)
ASSISTANT_PROVIDER=openclaw  # or ollama
OPENCLAW_URL=http://openclaw.eldertree.local:8080
OPENCLAW_MODEL=llama3.1:70b

# Optional: Integrations
WISE_API_TOKEN=your_wise_token
QUESTRADE_REFRESH_TOKEN=your_questrade_token
```

**Database migrations** (required whenever the API image includes new Alembic revisions):

```bash
docker compose exec api sh /app/backend/scripts/migrate.sh
# or: docker compose exec api sh -c "cd /app/backend && alembic upgrade head"
```

If migrations are not applied, you will see errors such as missing tables (`assistant_conversations`, `fx_rates`) or columns (`liabilities.opening_balance`).

### Kubernetes

After deploying a new API image:

```bash
kubectl -n canopy exec deploy/canopy-api -- sh /app/backend/scripts/migrate.sh
```

### Local Development (without Docker)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv/Scripts/activate on Windows
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8001
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Testing:**
```bash
# Backend (always run before commit/push)
docker-compose exec api pytest
# or: pytest tests/test_monarch_parser.py -q  # scoped

# Frontend
cd frontend && npm test
cd frontend && npm run lint
```

## Repo layout

```
canopy/
├── backend/              # FastAPI backend
│   ├── api/             # API endpoints (/v1/*)
│   ├── services/        # Business logic (portfolio calculations, FX, imports)
│   ├── db/models/       # SQLAlchemy ORM models
│   ├── models/          # Pydantic request/response models
│   ├── ingest/          # CSV parsers (Wealthsimple, Monarch, Amex)
│   ├── alembic/         # Database migrations
│   └── scripts/         # Migration and utility scripts
├── frontend/            # Next.js frontend
│   ├── pages/          # Next.js pages (Dashboard, Portfolio, Accounts, etc.)
│   ├── components/     # React components (UI, charts, forms)
│   └── utils/          # Utilities (API client, date filtering, currency hooks)
├── k8s/                 # Kubernetes manifests (eldertree cluster / GHCR)
├── .github/workflows/   # CI/CD (PR checks, build and push)
├── CHANGELOG.md         # Release notes
├── ARCHITECTURE.md      # Design decisions
├── CSV_IMPORT_GUIDE.md  # Import format documentation (if exists)
├── CLAUDE.md            # Development guide for Claude Code
└── README.md            # This file
```

**Documentation:**
- [CHANGELOG.md](./CHANGELOG.md) — Release notes and version history  
- [ARCHITECTURE.md](./ARCHITECTURE.md) — Design decisions and technology choices  
- [CLAUDE.md](./CLAUDE.md) — Development guide with commands, patterns, and conventions

## Features in Detail

### AI Assistant

The AI assistant provides natural language queries for financial data analysis:

- **Query Examples:** “How much did I spend on gas at Costco this month?”, “Show my portfolio performance”, “What's my net worth trend?”
- **Keyboard Shortcut:** ⌘⇧A (Cmd+Shift+A) to toggle chatbot
- **Features:** Suggested questions, copy responses, conversation history, function calling for data access
- **Providers:** OpenClaw (cluster-hosted, preferred) or Ollama (local fallback)
- **Storage:** Conversation history in PostgreSQL (`assistant_conversations`, `assistant_messages`)

### Multi-Currency Support

- **Currencies:** CAD, USD, combined view
- **FX Rates:** Bank of Canada Valet API with 1.35 fallback for stale/missing rates
- **Display Toggle:** Switch currency view across Dashboard, Accounts, Portfolio, Timeline
- **Storage:** Transactions stored in original currency; conversions on-demand

### Import System

- **Wealthsimple:** Monthly statements (Shape-A CSV with sub-CSVs); auto-creates accounts (cash → Accounts, investments → Holdings, debt → Accounts)
- **Monarch Money:** Transactions CSV + Balances CSV; unified classifier/parser
- **Amex Canada:** Year-End Summary (DD/MM/YYYY, Charges/Credits columns); Monthly Statement (Date/Amount/Account, “17 Apr 2026” dates)
- **Generic CSV:** Bank transactions with flexible column mapping

### Integrations

- **Wise API:** Automated balance sync for multi-currency accounts; creates `wise_balance` assets; stores FX rates and prices
- **Questrade:** OAuth refresh token support; background sync via Celery tasks

## Development

### Workspace Conventions

Canopy follows shared workspace conventions:

- **Git Workflow:** Feature branches (`feat/`, `fix/`, `docs/`), conventional commits, never commit to main
- **Testing:** Always run local tests before commit/push (CI is not the first gate)
- **Documentation:** Update CHANGELOG.md for all changes
- **Code Quality:** Ruff for Python, ESLint for TypeScript (extends workspace-config shared configs)
- **Dependencies:** Dependabot for automated updates

See [CLAUDE.md](./CLAUDE.md) for full development guide.

### Docker Images

- **API:** `ghcr.io/raolivei/canopy-api:<tag>`  
- **Frontend:** `ghcr.io/raolivei/canopy-frontend:<tag>`  
- **Tags:** Semantic versioning (e.g., `0.10.4`) or `latest`

### CI/CD

- **PR Checks:** pytest (backend), ESLint (frontend)
- **Build and Push:** Automated Docker image builds on merge to `main`
- **Auto-tagging:** May tag `v$(VERSION)` after image push

## Branches

After merging feature work to `main`, delete stale locals:

```bash
git checkout main && git pull
git branch --merged main   # safe candidates
git branch -d <branch-name>
```

Remote deletes: `git push origin --delete <branch>` only when the branch is merged and obsolete.

## Key Design Decisions

- **Self-hosted only:** No cloud dependencies; all data stays on your infrastructure
- **Privacy-first:** Never commit real user data; use synthetic placeholders (`****8813`, `example@local`)
- **Canadian focus:** Multi-currency support (CAD/USD) with Wealthsimple and Canadian bank integrations
- **Raspberry Pi optimized:** Resource-efficient for low-power hardware (K3s on Raspberry Pi 5)
- **Storage strategy:** Original currency preserved; conversions on-demand to avoid rounding errors
- **Balance-based assets:** Monarch and Wise imports create balance-only assets (no security symbol); portfolio uses lot-based holdings

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed rationale behind technology and design choices.

## Security

Treat as **sensitive financial data**:

- **Network Access:** Prefer private network (Tailscale, VPN) or strong authentication before exposing broadly
- **Secrets Management:** Use cluster secret store (Vault, External Secrets) — never commit secrets to Git
- **CORS:** Production restricts to specific domains (e.g., `canopy.eldertree.xyz`, `.eldertree.local`)
- **Data Privacy:** No real user data in commits, examples, tests, or logs

## Brand

Logo and brand assets: [`frontend/public/brand/`](./frontend/public/brand/).

## Roadmap

Version 0.10.4 (pre-1.0 release). Feature-complete status targeted for 1.0.0.

**Recent additions:**
- AI assistant with conversation history (0.10.5)
- Workspace config adoption (Ruff, ESLint, Dependabot) (0.10.4)
- Multi-currency support with BoC FX rates (0.10.0)
- Wise API integration (0.9.0)
- Wealthsimple and Monarch importers (0.8.0)

**Potential future features:**
- Property/real estate tracking
- Income streams and dividend projections
- API documentation improvements
- Additional integrations

See [CHANGELOG.md](./CHANGELOG.md) for full version history.

## Contributing

This is a personal self-hosted project. If you find it useful and want to adapt it for your own use:

1. Fork the repository
2. Follow the workspace conventions in [CLAUDE.md](./CLAUDE.md)
3. Run tests locally before committing
4. Update CHANGELOG.md for any changes

## License

This project is for personal use. See repository for license details.
