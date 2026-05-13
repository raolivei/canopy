# Canopy Development Guide

Self-hosted Canadian investment tracker (CAD only). Runs on **eldertree** k3s cluster. The app ingests Wealthsimple monthly statements and optional CAD portfolio snapshots; all dashboard numbers are CAD.

## Workspace

See \`../workspace-config/docs/PROJECT_CONVENTIONS.md\` for shared conventions (git workflow, CHANGELOG, Docker/GHCR, K8s, security).

**Ports** (from \`../workspace-config/ports/.env.ports\`):

- Frontend: \`3001\`
- API: \`8001\`
- PostgreSQL: \`5433\`
- Redis: \`6380\`

## Commands

\`\`\`bash
# Development (Docker Compose - recommended)
source ../workspace-config/ports/.env.ports
docker-compose up                    # Start all services
docker-compose up -d                 # Start detached

# Testing (run locally before commit/push—CI is not the first gate)
docker-compose exec api pytest       # Backend (scoped: pytest tests/test_monarch_parser.py -q)
cd frontend && npm test              # Frontend tests
cd frontend && npm run lint          # Also run when touching frontend/

# Database
docker-compose exec api alembic upgrade head           # Run migrations
docker-compose exec api alembic revision --autogenerate -m "desc"  # New migration
docker-compose exec postgres psql -U postgres -d canopy  # PostgreSQL shell

# Linting (run after changes)
cd backend && ruff check . && ruff format .  # Python
cd frontend && npm run lint                   # TypeScript
\`\`\`

## Workflow

1. Always lint/format after code changes
2. **Always run local tests (or scoped pytest / lint) before commit or push**
3. Update CHANGELOG.md for all changes
4. Never run git commands at workspace root

## Project Overview

\`\`\`
canopy/
├── backend/           # FastAPI (Python)
│   ├── api/          # API endpoints
│   ├── models/       # Pydantic models
│   ├── app/          # FastAPI app
│   ├── ingest/       # CSV/OFX import
│   └── services/     # Business logic
├── frontend/         # Next.js (TypeScript)
│   ├── components/   # React components
│   ├── pages/        # Next.js pages
│   └── utils/        # Utilities
└── k8s/              # Kubernetes manifests
\`\`\`

## Code Style

**Python**: See \`backend/api/transactions.py\` for route patterns, \`backend/models/transaction.py\` for Pydantic models.

**TypeScript**: See \`frontend/components/\` for component patterns. Use Tailwind CSS.

## Common Tasks

### Adding API Endpoint

1. Add route in \`backend/api/\`
2. Add Pydantic model in \`backend/models/\`
3. Update API docs (auto-generated)

### Adding CSV Import Format

1. Add parser in \`backend/ingest/csv_parsers.py\`
2. Add example CSV in \`examples/\`

### Adding Frontend Component

1. Create in \`frontend/components/\`
2. Use Tailwind for styling
3. Follow existing patterns

## Docker Images

- API: \`ghcr.io/raolivei/canopy-api:<tag>\`
- Frontend: \`ghcr.io/raolivei/canopy-frontend:<tag>\`

## Key Design Decisions

- **Self-hosted only**: No cloud dependencies
- **Privacy-first**: All data stored locally
- **CAD only**: Canadian investments focus — no multi-currency FX plumbing
- **Wealthsimple-first**: Importer auto-creates accounts (cash → Accounts page, investments → Holdings, debt → Accounts page)
- **Raspberry Pi optimized**: Low-power hardware

## AI Assistant

The app includes an AI assistant for natural language queries about financial data (e.g., "How much did I spend on gas at Costco this month?").

**Supported Providers:**
- **OpenClaw** (cluster-hosted, preferred when available) - Set `ASSISTANT_PROVIDER=openclaw` and `OPENCLAW_URL=http://openclaw.cluster.local`
- **Ollama** (local fallback) - Set `ASSISTANT_PROVIDER=ollama` and `OLLAMA_HOST=http://localhost:11434`

**Setup:**
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

**Features:**
- Query transactions, spending summaries, portfolio holdings
- Conversation history stored in PostgreSQL
- Function calling for data access (text-to-SQL)

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

- Escape apostrophes in JSX text: use `&apos;` not `'`
- Run `npm run lint` before committing frontend changes
- CI enforces all ESLint rules (no warnings = errors in build)
