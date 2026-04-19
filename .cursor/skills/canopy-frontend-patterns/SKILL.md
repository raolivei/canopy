---
name: canopy-frontend-patterns
description: >-
  Canopy Next.js UI patterns: portfolio holdings, integrations, currency view,
  API base URL. Use when editing frontend/pages or shared components.
---

# Frontend patterns

## API base URL

- Browser calls must use **`NEXT_PUBLIC_API_URL`** (e.g. `http://localhost:8000`). Relative `/v1/...` calls break in the client.
- Integrations and other flows should surface a clear message when the base URL is unset and map **fetch** failures to readable copy (not raw “Failed to fetch” only).

## Currency view

- **`useCurrencyView`** + **`useFxRate`** drive **CAD / USD / combined** behavior across dashboard, accounts, portfolio, timeline.
- Conversion helpers live with the hooks; avoid hardcoded FX constants in pages.

## Portfolio holdings table (`PortfolioHoldingsTable`)

- Splits **securities** vs **cash & accounts** (balance-based asset types).
- **Balance-based rows**: show **display `name` only** as the main line—do not emphasize internal importer **symbols** (e.g. Monarch slug like `MONARCH-RBC-…`) when a human-readable name exists. Securities keep **symbol + name**.
- Column header pattern: **Symbol / account**.

## Integrations settings page

- Prefer **brand logos** as static assets under **`frontend/public/integrations/*.svg`** (or vetted sources), not emojis in the card header.
- Monochrome marks (e.g. Wise) may need **dark mode** treatment (`invert` / brightness) so they stay visible.

## Privacy mode

- **`useMoney()`** / `formatCurrency*` support masking when privacy toggle is on; new money surfaces should use the same helpers.
