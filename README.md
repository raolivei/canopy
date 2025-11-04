# LedgerLight

LedgerLight is a privacy-first, self-hosted personal finance and investment cockpit inspired by Ghostfolio and Firefly III. It consolidates portfolio analytics, budgeting, and transaction tracking into a single dashboard designed to run on a Raspberry Pi k3s cluster with no cloud dependencies.

## Project Objectives

- Combine portfolio, budgeting, and net-worth views into one dashboard.
- Keep data local and encrypted — no external services required.
- Support multi-currency assets (CAD, USD, BRL) out of the box.
- Provide frictionless CSV/OFX import pipelines for banks and brokerages.
- Run lean enough for Raspberry Pi hardware.
- Remain modular and forkable for future community extensions.

## Architecture

| Layer        | Component                                    | Stack                                  |
| ------------ | -------------------------------------------- | -------------------------------------- |
| Frontend     | Responsive finance dashboard                 | Next.js + Tailwind (static export)     |
| Backend      | REST API + background ingest services        | FastAPI + Celery                       |
| Database     | Transaction & asset store                    | PostgreSQL + Redis                     |
| Importers    | CSV/OFX/Yahoo Finance/CoinGecko pipelines    | Celery tasks & scheduled jobs          |
| Auth         | Local JWT                                    | FastAPI security                       |
| Infra / Ops  | Deployment, GitHub Actions runners, secrets  | k3s, kubectl, Terraform (future work)  |

## Monorepo Layout

```
ledgerlight/
├── backend/                # FastAPI app, Celery workers, domain models
│   ├── app/                # Application setup, configuration, routers
│   ├── api/                # API route definitions
│   ├── ingest/             # Celery task definitions for importers
│   ├── models/             # Pydantic data models
│   ├── tests/              # Backend test suite (pytest)
│   ├── pyproject.toml      # Python project metadata & lint configuration
│   └── requirements.txt
├── frontend/               # Next.js + Tailwind static dashboard
│   ├── components/         # Reusable UI building blocks
│   ├── pages/              # Page routes
│   ├── styles/             # Tailwind entrypoint
│   ├── package.json
│   └── tsconfig.json
├── docker/                 # Container build definitions for CI
├── k8s/                    # Kubernetes manifests (namespaced)
├── .github/workflows/      # CI/CD pipelines for build & deploy
├── ledgerlight.yaml        # Aggregated manifest for `kubectl apply -f`
├── CHANGELOG.md
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.11
- Node.js 20.x and npm
- Docker (for container builds)
- kubectl (for deployment)

### Backend (FastAPI)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn backend.app.server:app --reload
```

Run the backend tests:

```bash
cd backend
pytest
```

### Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev
```

To generate the static export served in production:

```bash
cd frontend
npm run export
```

### Containers

Dockerfiles for the backend and static frontend live in `docker/`. Build images locally with:

```bash
docker build -f docker/backend.Dockerfile -t ledgerlight-backend .
docker build -f docker/frontend.Dockerfile -t ledgerlight-frontend .
```

## Deployment

The project targets a Raspberry Pi k3s cluster and avoids Helm/Argo. Apply the bundled manifest once secrets are configured:

```bash
kubectl apply -f k8s/secrets.example.yaml   # customize before applying
kubectl apply -f ledgerlight.yaml
```

All manifests are also split under `k8s/` for modular management. The GitHub Actions workflow builds GHCR images and runs `kubectl apply` from a self-hosted runner using the same manifests.

## Roadmap

- Phase 1 (MVP): portfolio & budget summaries, CSV imports, automated deployment.
- Phase 2: Ghostfolio-compatible API, Firefly III interoperability, daily FX/crypto fetchers, PWA.
- Stretch: local AI insights, multi-user support, regional tax reporting, wealth projections.

Refer to `CHANGELOG.md` for an accurate timeline of changes between releases.
