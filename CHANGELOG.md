# Changelog

Notable releases only — **details belong in commits / PRs**, not here.

## Versioning

Pre-release **0.x**; **1.0.0** when feature-complete.

## [0.10.3] - 2026-04-19

- README refresh; FIRE optional CAGR from snapshots; net worth chart (stacked area + debt axis); portfolio dividends + positions split; accounts grouping; nav/import/integrations polish + logos; privacy “hide amounts”; **Cursor** project agent skills under `.cursor/skills/` (repo conventions, stack map, UI/backend/import notes).
- Wise sync writes prices; insights use balance history; holdings cash rows show display name (hide Monarch internal symbols).
- CI may tag `v$(VERSION)` after image push on `main`.

## [0.10.2] - 2026-04-18

- Monarch **Balances** CSV importer + unified monarch file drop; API `{transactions, balances}`; classifier/parser broadened.

## [0.10.1] - 2026-04-18

- Danger Zone reset UI; WS net-worth timeline includes lot book value; accounts from latest balance history; holdings `Decimal` / `$0` fixes; MobileNav hydration guard.

## [0.10.0] - 2026-04-18

- BoC **USDCAD** store + `/v1/fx/*`; **currency view** (CAD / USD / combined) across dashboard, accounts, holdings, timeline; hooks `useCurrencyView` / `useFxRate`.

## [0.9.0] - 2026-04-18

- **CAD + USD** scope; BR/multi-currency cruft removed; `GET /v1/accounts`; Monarch transaction importer + canonical-hash dedup; batch portfolio-review import; WS/Migration fixes (dividend enum, multi-ccy balance rows).

## [0.8.0] - 2026-04-18

- **Wealthsimple CSV** import, filename/row parsers, `/v1/wealthsimple-import/*`, net-worth timeline, dashboard hero.

## [0.7.0] - 2026-04-01

- Portfolio review CSV model + API + dashboard charts; import page.

## [0.6.0] - 2026-02-18

- Slate/teal design system, chart theme, Toast/Table, component pass.

## [0.5.0]

- Wise integration (settings + sync API).

## [0.4.0]

- Insights + FIRE APIs/pages; real estate & liability models; major schema migration.

## [0.3.0] and earlier

- Rebrand LedgerLight → **Canopy**; prior dev: backend scaffold, transactions/currency, UI shell, dark mode, docs. Superseded by work above.
