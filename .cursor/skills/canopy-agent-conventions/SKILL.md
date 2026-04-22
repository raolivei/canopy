---
name: canopy-agent-conventions
description: >-
  Canopy: CHANGELOG/commits, privacy, PR/git habits, and change scope. Use for
  any Canopy edit that touches docs, release notes, or shared artifacts.
---

# Agent conventions (Canopy)

## Changelog

- **Minimal**: themes only; one line per release section when possible. Detail belongs in **commits / PRs**, not `CHANGELOG.md`.
- Do not balloon entries with API field lists, file paths, or duplicate Changed vs Fixed narratives.

## Privacy (non-negotiable)

- Never put **real** names, institutions, account or card identifiers, addresses, or **real dollar amounts** from user data into: commits, PR bodies, `CHANGELOG`, README/examples, tests, fixtures, screenshots, or pasted logs.
- Use synthetic placeholders: `****8813`, `example@local`, tiny made-up CSV rows.

## Code and docs scope

- Change only what the task requires; match existing style and abstractions.
- Do not add unsolicited markdown guides or expand scope with drive-by refactors.

## Testing (before push)

- **Always run local tests (or lint) before committing or pushing**—do not rely on CI as the first signal.
- **Backend** (from repo root, Docker Compose): `docker compose exec api pytest` (or a scoped path, e.g. `pytest tests/test_monarch_parser.py -q`).
- **Frontend**: `cd frontend && npm run lint` and `npm test` when you changed `frontend/`.
- If Docker is not running, use the project **`backend/.venv`** with `pytest` installed, or say explicitly that tests were not run and why.

## Git / PR

- Work on **`feat/*`** (or `fix/*`, etc.); avoid committing directly to `main`.
- Conventional commits (`feat:`, `fix:`, `docs:`, …). PR titles should describe outcome, not only branch name.
- Open PRs may overlap: a large **`feat/portfolio-review-pivot`-style** branch can supersede older topic branches—rebase or close stale PRs that **conflict** with `main`.
