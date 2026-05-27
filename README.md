# Canopy

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Node](https://img.shields.io/badge/node-18+-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)
![Next.js](https://img.shields.io/badge/Next.js-14.0-black.svg)
![PR Checks](https://github.com/raolivei/canopy/actions/workflows/pr.yml/badge.svg)
![Build](https://github.com/raolivei/canopy/actions/workflows/build-and-push.yml/badge.svg)

**Canadian net worth and investments — self-hosted.**

Canopy is a personal finance app for **CAD + USD**: Wealthsimple and Monarch CSV imports, optional **Wise** (CAD/USD balances) and **Questrade** integrations, portfolio holdings, cash/credit accounts, insights, and a **FIRE calculator**. Data stays on your infrastructure (e.g. k3s at home, Tailscale access).

## What it does

| Area | Description |
|------|-------------|
| **Dashboard** | Net worth from Wealthsimple timeline + Monarch balances; currency toggle (CAD / USD / combined). |
| **Import** | Wealthsimple statements, Monarch transactions + balances, legacy portfolio snapshots, bank CSV. |
| **Portfolio** | Positions & accounts (securities vs cash/registered balances), allocation, performance, dividends. |
| **Accounts** | Chequing, savings, credit, LOC — grouped optionally by institution or debit vs credit. |
| **Insights** | Net worth, allocation, growth from snapshots; **FIRE** with default 7% or **CAGR from portfolio snapshots** (≥60 days of history). |
| **Integrations** | Wise sync (CAD/USD only), Questrade (OAuth refresh token). |

## Stack

- **Backend:** FastAPI, SQLAlchemy, PostgreSQL, Alembic  
- **Frontend:** Next.js, React Query, Tailwind, Recharts  
- **FX:** Bank of Canada USDCAD cache (`fx_rates`) for combined views  

Default local ports (see `docker-compose` / workspace config): **frontend `3001`**, **API `8001`**.

## Quick start

```bash
# From repo root, with workspace port env if you use it:
source ../workspace-config/ports/.env.ports   # optional
docker-compose up
```

- App: http://localhost:3001  
- API docs: http://localhost:8001/docs  

Set **`NEXT_PUBLIC_API_URL`** (e.g. `http://localhost:8001`) so the browser can reach the API from the Next dev server.

**Database migrations** (required whenever the API image includes new Alembic revisions):

```bash
docker compose exec api sh /app/backend/scripts/migrate.sh
# or: docker compose exec api sh -c "cd /app/backend && alembic upgrade head"
```

**Kubernetes** (after deploying a new API image):

```bash
kubectl -n canopy exec deploy/canopy-api -- sh /app/backend/scripts/migrate.sh
```

If migrations are not applied, you will see errors such as missing tables (`portfolio_reviews`, `fx_rates`) or columns (`liabilities.opening_balance`).

Local fallback without Docker: `backend` → uvicorn on 8001; `frontend` → `npm run dev` (port from `package.json` / env).

## Repo layout

```
canopy/
├── backend/           # FastAPI — api/, services/, db/models/, alembic/
├── frontend/        # Next.js — pages/, components/
├── k8s/               # Kubernetes manifests (eldertree / GHCR)
├── CHANGELOG.md
└── README.md
```

Deeper docs: [CHANGELOG.md](./CHANGELOG.md), [ARCHITECTURE.md](./ARCHITECTURE.md), [CSV_IMPORT_GUIDE.md](./CSV_IMPORT_GUIDE.md).

## GitHub issues — triage (manual)

Close or narrow when you merge work:

| Issue | Suggested action |
|-------|------------------|
| [#23 Wise API](https://github.com/raolivei/canopy/issues/23) | **Close or narrow** — Wise sync exists (CAD/USD balances + transactions). Open follow-ups only for extra currencies/FX. |
| [#21 Questrade](https://github.com/raolivei/canopy/issues/21) | **Keep open** until OAuth + sync are stable in prod; UI exists. |
| [#24 Dividends](https://github.com/raolivei/canopy/issues/24) | **Open** — tracking UI exists; “income streams” scope may still apply. |
| [#26 Property](https://github.com/raolivei/canopy/issues/26) | **Open**. |
| [#27 API docs](https://github.com/raolivei/canopy/issues/27) | **Open**. |
| [#29 / #30 “suites”](https://github.com/raolivei/canopy/issues) | **Open** — roadmap. |

## Branches

After merging feature work to `main`, delete stale locals:

```bash
git checkout main && git pull
git branch --merged main   # safe candidates
git branch -d <branch-name>
```

Remote deletes: `git push origin --delete <branch>` only when the branch is merged and obsolete.

## Brand

Logo: [`frontend/public/brand/`](./frontend/public/brand/).

## Security

Treat as **sensitive financial data**. Prefer private network / Tailscale; do not expose the app broadly without strong auth. Secrets via your cluster’s secret store (e.g. Vault), not in Git.
