# Canopy - AI Assistant Context

## Quick Reference

- **Project Type**: Self-hosted personal finance tracker (private/proprietary)
- **Purpose**: Canadian net worth and investments (CAD + USD)
- **Deployed to**: `eldertree` Raspberry Pi k3s cluster
- **Namespace**: `canopy`
- **Tech Stack**: FastAPI (Python) + Next.js (TypeScript)
- **Data Sources**: Wealthsimple, Monarch CSV, Wise, Questrade
- **Ports**: 3001 (frontend), 8001 (api), 5433 (postgres), 6380 (redis)

## Critical Rules

### Git & Workflow
- **NEVER commit directly to main** - Always use feature branches
- **Branch naming**: `feat/`, `fix/`, `docs/`, `chore/`
- **Never run git commands at workspace root** - Always `cd canopy/` first
- **Always run local tests before commit/push** - CI is not the first gate

### Testing & Linting
- **Backend**: `docker-compose exec api pytest` (or scoped: `pytest tests/test_monarch_parser.py -q`)
- **Frontend**: `cd frontend && npm test && npm run lint`
- **Linting**: `cd backend && ruff check . && ruff format .`
- **MUST run tests locally** before pushing - Don't rely on CI as first check

### Changelog & Versioning
- **ALWAYS update CHANGELOG.md** for all changes (features, fixes, refactors)
- **Git tag versions must match Docker image tags**
- Follow [Keep a Changelog](https://keepachangelog.com/) format

### Code Quality
- **Python**: Ruff for linting/formatting, type hints required, Pydantic models
- **TypeScript**: ESLint enforced, no warnings in CI, escape apostrophes (`&apos;`)
- **Tailwind CSS**: Utility-first styling, no custom CSS files

### Security
- **Treat as sensitive financial data** - Private network/Tailscale only
- **Never commit secrets** - Use Vault or cluster secret store
- **No broad exposure** - Self-hosted only, strong auth required

## When to Read What

### Getting Started
- **New to project?** → This file + [README.md](README.md) + [ARCHITECTURE.md](ARCHITECTURE.md)
- **Quick start?** → [README.md](README.md) (Docker Compose setup)
- **Workspace conventions?** → `../workspace-config/docs/PROJECT_CONVENTIONS.md`

### Development
- **Architecture decisions?** → [ARCHITECTURE.md](ARCHITECTURE.md) (why FastAPI, Next.js, Tailwind, etc.)
- **CSV imports?** → [CSV_IMPORT_GUIDE.md](CSV_IMPORT_GUIDE.md)
- **Agent patterns?** → [AGENTS.md](AGENTS.md)

### Deployment & Operations
- **Deploying to k3s?** → [DEPLOYMENT.md](DEPLOYMENT.md)
- **Emergency deployment?** → [EMERGENCY_DEPLOYMENT.md](EMERGENCY_DEPLOYMENT.md)
- **GHCR issues?** → [DEPLOYMENT.md](DEPLOYMENT.md) section "GitHub Container Registry"

### Code Reference
- **API patterns?** → `backend/api/transactions.py` (route examples)
- **Pydantic models?** → `backend/models/transaction.py`
- **Frontend components?** → `frontend/components/` (Tailwind patterns)
- **UI patterns?** → This file (section "UI Patterns")

### Planning
- **Changelog?** → [CHANGELOG.md](CHANGELOG.md)
- **GitHub issues?** → See [README.md](README.md) section "GitHub issues - triage"

## Project Structure

```
canopy/
├── backend/           # FastAPI (Python)
│   ├── api/          # API endpoints
│   ├── models/       # Pydantic models
│   ├── app/          # FastAPI app configuration
│   ├── ingest/       # CSV/OFX import parsers
│   ├── services/     # Business logic
│   └── db/           # Database models (SQLAlchemy)
├── frontend/         # Next.js (TypeScript)
│   ├── components/   # React components
│   ├── pages/        # Next.js pages
│   ├── utils/        # Utilities (dateFiltering, etc.)
│   └── public/       # Static assets
├── k8s/              # Kubernetes manifests
├── scripts/          # Utility scripts
├── examples/         # Example CSV files
├── CLAUDE.md         # This file - AI assistant entry point
├── AGENTS.md         # Agent development patterns
├── ARCHITECTURE.md   # Design decisions and rationale
├── DEPLOYMENT.md     # Kubernetes deployment guide
└── README.md         # Quick start and overview
```

## Data Model Overview

**Key Features:**
- **Multi-currency**: CAD + USD (Bank of Canada FX rates cached in `fx_rates`)
- **Import sources**: Wealthsimple statements, Monarch CSV, Wise API, Questrade OAuth
- **Accounts**: Chequing, savings, credit, LOC, investments
- **Portfolio**: Holdings, allocations, performance, dividends
- **FIRE calculator**: Uses 7% default or CAGR from portfolio snapshots (≥60 days)

**Tables:**
- `transactions` - Financial transactions (multi-currency)
- `accounts` - Cash/credit accounts
- `portfolio_holdings` - Investment positions
- `portfolio_reviews` - Snapshot history
- `fx_rates` - Exchange rate cache (Bank of Canada)
- `liabilities` - Debt tracking

## Environment Setup

### Docker Compose (Recommended)

```bash
# Load workspace port assignments
source ../workspace-config/ports/.env.ports

# Start all services (hot reload enabled)
docker-compose up

# Start detached
docker-compose up -d

# Access services
# Frontend: http://localhost:3001
# API: http://localhost:8001
# API Docs: http://localhost:8001/docs
```

### Database Migrations

```bash
# Run migrations (after API updates)
docker-compose exec api alembic upgrade head

# Create new migration
docker-compose exec api alembic revision --autogenerate -m "description"

# PostgreSQL shell
docker-compose exec postgres psql -U postgres -d canopy
```

### Testing

```bash
# Backend tests (ALWAYS run before commit)
docker-compose exec api pytest

# Scoped test
docker-compose exec api pytest tests/test_monarch_parser.py -q

# Frontend tests
cd frontend && npm test

# Frontend linting (ALWAYS run before commit)
cd frontend && npm run lint
```

### Linting

```bash
# Python (Ruff)
cd backend
ruff check .
ruff format .

# TypeScript (ESLint)
cd frontend
npm run lint
```

## Common Tasks

### Adding API Endpoint
1. Create branch: `feat/add-endpoint`
2. Add route in `backend/api/` (see `transactions.py` for patterns)
3. Add Pydantic model in `backend/models/`
4. Add tests in `backend/tests/`
5. Run tests: `docker-compose exec api pytest`
6. Update CHANGELOG.md

### Adding CSV Import Format
1. Create branch: `feat/add-csv-parser`
2. Add parser in `backend/ingest/csv_parsers.py`
3. Add example CSV in `examples/`
4. Add tests
5. Update [CSV_IMPORT_GUIDE.md](CSV_IMPORT_GUIDE.md)

### Adding Frontend Component
1. Create branch: `feat/add-component`
2. Create component in `frontend/components/`
3. Use Tailwind CSS for styling
4. Follow existing patterns (see `frontend/components/ui/`)
5. Run lint: `npm run lint`
6. Update CHANGELOG.md

### Deploying to Kubernetes
1. Build images locally or via GitHub Actions
2. Push to GHCR: `ghcr.io/raolivei/canopy-api:latest`
3. Apply manifests: `kubectl apply -f k8s/`
4. Run migrations: `kubectl -n canopy exec deploy/canopy-api -- sh /app/backend/scripts/migrate.sh`
5. Verify: `kubectl get pods -n canopy`

## UI Patterns

### Time Period Controls

Use `PeriodSelector` component + `dateFiltering` utilities for time-series filtering.

**Available periods**: 5D, 1M, 3M, 6M, 1Y, YTD, All

**Example** (see `frontend/pages/index.tsx`):
```typescript
import { PeriodSelector } from "@/components/ui/PeriodSelector";
import { filterByPeriod, TimePeriod } from "@/utils/dateFiltering";

const [period, setPeriod] = useState<TimePeriod>("all");

const filteredData = useMemo(() => {
  const mapped = data.map((item) => ({
    ...item,
    rawDate: item.date, // Keep ISO date for filtering
  }));
  return filterByPeriod(mapped, (item) => item.rawDate, period);
}, [data, period]);

<PeriodSelector selectedPeriod={period} onPeriodChange={setPeriod} />
```

### Reusable UI Components

Located in `frontend/components/ui/`:
- `Button.tsx` - Multiple variants (primary, secondary, ghost) and sizes
- `Card.tsx` - Container components
- `Input.tsx`, `Select.tsx` - Form controls
- `PeriodSelector.tsx` - Time period button group
- `Badge.tsx`, `Modal.tsx`, `Skeleton.tsx` - Common UI elements

### ESLint Rules

- **Escape apostrophes in JSX**: Use `&apos;` not `'`
- **Run `npm run lint` before committing** frontend changes
- **CI enforces all ESLint rules** - No warnings = errors in build

## AI Assistant Feature

The app includes an AI assistant for natural language financial queries.

### Supported Providers
- **OpenClaw** (cluster-hosted, preferred) - `ASSISTANT_PROVIDER=openclaw`
- **Ollama** (local fallback) - `ASSISTANT_PROVIDER=ollama`

### Setup
```bash
# Option 1: Use OpenClaw (cluster)
ASSISTANT_PROVIDER=openclaw
OPENCLAW_URL=http://openclaw.eldertree.local:8080
OPENCLAW_MODEL=llama3.1:70b

# Option 2: Use Ollama (local)
ASSISTANT_PROVIDER=ollama
OLLAMA_HOST=http://localhost:11434
ollama pull llama3.1:8b
```

### Features
- Query transactions, spending summaries, portfolio holdings
- Conversation history stored in PostgreSQL
- Function calling for data access (text-to-SQL)
- Natural language interface (e.g., "How much did I spend on gas at Costco this month?")

## Docker Images

- **API**: `ghcr.io/raolivei/canopy-api:<tag>`
- **Frontend**: `ghcr.io/raolivei/canopy-frontend:<tag>`

### Image Tags
- `main` - Latest from main branch
- `latest` - Latest stable release
- `v0.10.3` - Specific version tag
- `sha-<commit>` - Commit-specific tag

### GHCR Access
Private repository = private packages. Login required:
```bash
echo YOUR_GH_PAT | docker login ghcr.io -u raolivei --password-stdin
```

Use PAT with **read:packages** (pull) or **write:packages** (push).

## Key Design Decisions

From [ARCHITECTURE.md](ARCHITECTURE.md):

- **Self-hosted only** - No cloud dependencies, privacy-first
- **CAD + USD only** - Canadian investments focus, no multi-currency FX plumbing
- **Wealthsimple-first** - Auto-creates accounts from imports
- **Raspberry Pi optimized** - Low-power hardware compatible
- **FastAPI** - Performance, type safety, auto-documentation
- **Next.js** - SSR/SSG, optimized builds, file-based routing
- **Tailwind CSS** - Rapid development, design system consistency
- **Store original currency** - Convert on-demand, preserve data integrity

## Branch Management

After merging to `main`, delete stale branches:
```bash
git checkout main && git pull
git branch --merged main   # Safe candidates
git branch -d <branch-name>
```

Remote deletes (only when merged and obsolete):
```bash
git push origin --delete <branch>
```

## External References

- **Workspace Config**: `../workspace-config/` - Port assignments, conventions, shared scripts
- **Infrastructure**: `../pi-fleet/` - Kubernetes cluster configuration
- **Runbook**: https://docs.eldertree.xyz - eldertree cluster troubleshooting

## Search Tips

1. **Check ARCHITECTURE.md** for "why" behind design decisions
2. **Check CSV_IMPORT_GUIDE.md** for import format examples
3. **Check DEPLOYMENT.md** for GHCR and Kubernetes issues
4. **Check backend/api/** for API endpoint patterns
5. **Check frontend/components/ui/** for reusable component examples

## Important Notes

### Currency Handling
- All amounts stored in original currency
- FX conversion on-demand using Bank of Canada rates
- Currency toggle: CAD / USD / combined views

### Import Auto-Creation
Wealthsimple imports auto-create accounts:
- Cash → Accounts page
- Investments → Holdings
- Debt → Accounts page (liabilities)

### Resource Requirements
**Minimum per replica:**
- API: 256Mi RAM, 250m CPU
- Frontend: 128Mi RAM, 100m CPU
- Redis: 64Mi RAM, 50m CPU
- Postgres: 256Mi RAM, 250m CPU

**Total default (2 API, 2 Frontend)**: ~1.2Gi RAM, ~1 CPU

## Key Principles

1. **Privacy-First** - Self-hosted, no cloud, data stays local
2. **Test-First** - Local tests before commit/push (CI is not the gate)
3. **Type Safety** - Pydantic models, TypeScript strict mode
4. **Auto Documentation** - FastAPI OpenAPI, code comments minimal
5. **Maintainability** - Monorepo, co-located concerns, clear structure
6. **Performance** - Async FastAPI, Next.js optimizations, Tailwind purge

---

**Last Updated**: 2026-05-07  
**For Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md)  
**For Deployment**: See [DEPLOYMENT.md](DEPLOYMENT.md)  
**For Agents**: See [AGENTS.md](AGENTS.md)
