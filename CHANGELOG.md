# Changelog

All notable changes to this project will be documented in this file.

## Versioning

**Current Status**: Pre-release (0.x.x versions)

- **0.x.x**: Development versions - features are being built and tested  
- **1.0.0**: First stable release - will be tagged when feature-complete and production-ready

## [0.2.3-dev] - 2025-01-XX

### Changed
- Updated MASTER_PROMPT.md with project documentation
- Updated backend configuration (config.py)
- Updated Kubernetes deployment manifests (k8s/deploy.yaml)

### Added
- Claude AI settings configuration (.claude/settings.local.json)

## [0.3.0] - 2025-11-13 - 🌳 **Canopy Launch** (Pre-release)

### BREAKING CHANGE - Project Rebranded

**LedgerLight is now Canopy** - Complete rebrand and vision expansion.
**Note**: Still in pre-1.0 development. Version 1.0.0 will be the first production-ready release.

### What's New in Canopy

**Tagline**: "Your financial life. Under one canopy."

**Vision**: Self-hosted personal finance, investment, and budgeting dashboard inspired by Monarch Money, Ghostfolio, and Firefly III. Fully local on Raspberry Pi k3s clusters.

### Changed

- **Project Name**: LedgerLight → Canopy
- **Branding**: New logo featuring tree canopy forming the letter "C"
- **Description**: Expanded vision to emphasize budgeting, investment tracking, and Monarch-level UX
- **Documentation**: Updated README, ARCHITECTURE with Canopy vision
- **Backend**: Renamed API title to "Canopy API"
- **Frontend**: All page titles, meta tags, and OG images updated
- **Database**: Connection strings updated from ledgerlight to canopy
- **Package Names**:
  - `ledgerlight-backend` → `canopy-backend`
  - `ledgerlight-frontend` → `canopy-frontend`

### Migration Guide

See [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) for complete migration instructions including:

- GitHub repository renaming
- Local environment updates
- Brand asset replacement
- Pi cluster deployment updates

### Planned Features (Roadmap)

**MVP+** (In Development):

- Budget management (Fixed/Flexible/Non-monthly envelopes)
- Investment portfolio tracking (stocks, ETFs, crypto)
- Goals tracking (retirement, savings)
- Recurring transaction detection
- Net worth snapshots and charts
- Cash flow analysis (enhanced)
- Celery background tasks for price ingestion

**Deployment**:

- K8s manifests for Pi cluster (eldertree control plane)
- GitHub Actions with self-hosted runner
- Minimal YAML, yearly maintenance philosophy

### Architecture Highlights

**Backend**: FastAPI + Celery + Redis + PostgreSQL  
**Frontend**: Next.js + Tailwind + shadcn  
**Infra**: k3s on Raspberry Pi (eldertree + fleet-worker nodes)  
**Deployment**: kubectl apply (no Helm, no ArgoCD)

### Design Philosophy

- **Self-hosted**: Full privacy, no cloud dependencies
- **Offline-friendly**: Works without internet
- **Multi-currency**: CAD, USD, BRL, EUR, GBP
- **Monarch-level UX**: Polished, calm, premium design
- **Pi-optimized**: Lean, efficient, minimal resource usage
- **Modular**: Easy to fork and extend

### Credits

Built by Rafael Oliveira (@raolivei) for the Pi fleet homelab.

---

## [0.2.2-dev] - 2025-11-04 (Pre-release)

### Fixed

- Fixed currency conversion endpoint returning 500 error
  - **Why:** Pydantic v2 deprecated `dict()` method in favor of `model_dump()`. The error occurred because code was using deprecated API.
  - **Solution:** Updated to use `model_dump()` with fallback to `dict()` for backward compatibility.
- Updated to use `model_dump()` for Pydantic v2 compatibility in transaction currency conversion
- Added fallback to `dict()` for Pydantic v1 support
- Currency conversion query parameter now works correctly (`/v1/transactions/?currency=CAD`)

### Added

- Comprehensive architecture documentation (ARCHITECTURE.md)
  - **Why:** Document design decisions and rationale to help future developers understand the "why" behind technical choices
  - **Contents:** Architecture overview, technology choices, API design, frontend architecture, data management, security considerations, performance optimizations
- Enhanced documentation with "why" explanations
  - **Why:** Understanding rationale helps maintainability and prevents regression of design decisions
  - **Updated:** MASTER_PROMPT.md, README.md, CHANGELOG.md with design rationale sections

## [0.2.1-dev] - 2025-11-04 (Pre-release)

### Fixed

- Integrated transaction and currency routers into server.py
  - **Why:** Feature branches created routers separately. Integration ensures all endpoints are accessible.
  - **Solution:** Conditional import pattern allows routers to work even if some are missing.
- Added CORS middleware for frontend-backend communication
  - **Why:** Browser Same-Origin Policy blocks cross-origin requests. Frontend (port 3000) needs to call backend (port 8000).
  - **Solution:** CORS middleware explicitly allows frontend origin.
- Added missing transaction model to dev branch
  - **Why:** Transaction API requires Transaction model but it was only in feature branch.
  - **Solution:** Added model to dev branch to ensure complete functionality.
- Verified all API endpoints working correctly
- Stable application state with full functionality

## [Unreleased]

### Added

- **Backend API Setup** (`feature/backend-api-setup`):

  - FastAPI application with CORS middleware configuration
  - Transaction models (Transaction, TransactionCreate, TransactionType enum)
  - Transaction CRUD API endpoints (GET all, GET by ID, POST, DELETE)
  - Health check endpoint at `/v1/health`
  - Python requirements.txt with FastAPI, Uvicorn, SQLAlchemy, Pydantic dependencies
  - In-memory transaction storage (ready for database migration)

- **UI Redesign** (`feature/ui-redesign-monarch-style`):

  - Modern Monarch Money-inspired UI design
  - Sidebar navigation component with active state highlighting
  - Reusable StatCard component for dashboard metrics
  - Redesigned dashboard with:
    - Cash flow area chart (income vs expenses over time)
    - Spending by category pie chart
    - Recent transactions list
    - Summary stat cards (Total Income, Expenses, Net Cash Flow, Spending)
  - Redesigned transactions page with improved layout and card-based summaries
  - Custom Tailwind CSS components (card, card-hover, btn-primary, btn-secondary, input-modern)
  - Tailwind configuration with primary color palette and Inter font family
  - Responsive grid layouts and modern card designs

- **Currency Support** (`feature/currency-support`):

  - Multi-currency support (USD, CAD, BRL, EUR, GBP)
  - Currency API endpoints (`/v1/currency/supported`, `/v1/currency/rates`, `/v1/currency/convert`)
  - Currency conversion logic with mock exchange rates
  - CurrencySelector component for frontend
  - Currency formatting utilities (formatCurrency, convertCurrency, formatCurrencyCompact)
  - Transactions API support for optional currency conversion
  - Display currency toggle in UI
  - Show both original and converted amounts when currencies differ

- **Dark Mode** (`feature/dark-mode`):

  - DarkModeToggle component with localStorage persistence
  - System preference detection for automatic dark mode
  - Dark mode styles throughout all UI components
  - Integration in sidebar and page headers
  - Tailwind class-based dark mode configuration
  - SSR-safe implementation to prevent hydration mismatches

- **Placeholder Pages** (`feature/placeholder-pages`):

  - Portfolio page with stat cards for investment metrics
  - Accounts page with account cards (Checking, Credit Card, Savings)
  - Settings page with currency selector, dark mode toggle, and placeholder sections
  - All pages include proper Next.js Head components and dark mode support

- **Documentation** (`docs/master-prompt`):
  - Comprehensive MASTER_PROMPT.md with complete application recreation guide
  - Project structure documentation
  - Setup instructions for backend and frontend
  - API specifications and data models
  - UI/UX design system documentation
  - Complete feature roadmap with implementation phases
  - Troubleshooting guide and development workflow

### Fixed

- **SSR and State Fixes** (`bugfix/ssr-and-state-fixes`):
  - Fixed missing `showConverted` and `convertedAmounts` state variables in transactions page
  - Fixed SSR error with `document` access in chart tooltips
  - Added `isDarkMode` state tracking for client-side dark mode detection
  - Prevented hydration mismatches in dark mode toggle component

## [0.1.0-dev] - 2025-11-03 (Pre-release)

### Added

- README with detailed objectives, architecture, and onboarding workflows.
- FastAPI backend scaffold featuring:
  - Application factory, configuration via `pydantic-settings`, and cached settings loader.
  - Versioned API routing (`/v1/health`, `/v1/summary`) plus smoke tests.
  - Celery ingest task stub and domain models for portfolio data.
  - Backend-specific Dockerfile, requirements, and `.env` example.
- Next.js 14 + Tailwind frontend setup:
  - KPI dashboard page, reusable layout components, Tailwind theme extension.
  - Static export workflow and Dockerfile for NGINX runtime.
- Infra and delivery tooling:
  - Kubernetes namespace, deployments (API, worker, frontend), services, ingress, and secrets example.
  - Aggregated `ledgerlight.yaml` for single-command deployment.
  - GitHub Actions workflow to build/push container images to GHCR and deploy via `kubectl`.
