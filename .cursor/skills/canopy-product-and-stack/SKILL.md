---
name: canopy-product-and-stack
description: >-
  Canopy product scope, stack, and repo layout. Use when planning features,
  imports, or deployment-related work.
---

# Product and stack

## What Canopy is

- **Self-hosted** personal finance / investments tracker, **Canadian focus**, operating in **CAD and USD** (not a multi-region product).
- Primary inputs: **Wealthsimple** monthly CSVs, **Monarch Money** exports (transactions + balances), manual portfolio snapshots, bank CSV where supported.
- Optional: **Wise** / **Questrade** integrations; net worth, accounts, holdings, insights/FIRE.

## Stack (typical)

- **Backend**: FastAPI, SQLAlchemy, Alembic, PostgreSQL; tests often runnable with SQLite via `conftest.py`.
- **Frontend**: Next.js, React, Tailwind; React Query for API calls.
- **Images / CI**: Docker + GitHub Actions; version in `VERSION`; tags may follow CI (`v$(VERSION)` pattern when enabled).

## Repo layout (high level)

- `backend/api/` — route modules (`portfolio`, `accounts`, `integrations`, `wealthsimple_import`, `monarch_import`, `insights`, `fx`, …).
- `backend/services/` — calculators, importers (`wealthsimple/`, `monarch/`, …), FX, Wise/Questrade.
- `backend/db/models/` — assets, liabilities, balance history, lots, etc.
- `frontend/pages/` — routes (`portfolio`, `accounts`, `settings/integrations`, …).
- `frontend/components/` — shared UI (`PortfolioHoldingsTable`, charts, layout).
- `k8s/` or fleet docs may live outside this repo; cluster context can appear in workspace rules.
