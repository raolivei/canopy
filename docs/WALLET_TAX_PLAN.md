# Canopy Wallet and Tax implementation plan

Updated: 2026-11-15 (America/Toronto). Status: assessed and planned; implementation incomplete.

## Product direction

One Canopy application with two primary workspaces: **Wallet** and **Tax**.
Wallet should reproduce the useful workflows and analysis in the user's Monarch
account, then improve them through explainable calculations, reliable imports,
local processing, and integration with Tax. Tax should organize uploaded records
and CRA correspondence by tax year, maintain an evidence-backed ledger, and track
actions across years. Routine implementation is authorized. If a capability proves
infeasible, present the concrete limitation, alternatives, cost and consequence to
the user before dropping it or substituting a materially different workflow.

## Scope clarification: replace Monarch without bank connectivity

The user explicitly excludes bank connectivity from this build. Plaid, Finicity,
MX, bank-login automation and new direct bank/broker connectors are not milestones
or cancellation prerequisites. Existing integrations may remain available, but
expanding them is outside the current scope.

Use Monarch temporarily as a reference during development and migration. Prefer
read-only official MCP access for the data it exposes, and the browser for interaction
and chart behavior. Validate actual tool/schema/coverage support before promising
migration of budgets, rules, goals or historical balances. MCP exposes data and
operations, not Monarch's internal code or proprietary calculation algorithms.

After migration, Canopy must work with Monarch disconnected: bank/broker CSVs,
statements, tax PDFs/receipts, CRA correspondence and manual entries supply new data.
Prioritize batch upload, saved column mappings, account matching, deduplication,
reconciliation and clear data-through dates. CSV is preferred for structured
transactions; extracted statement data requires review and reconciliation.
Predictions must disclose the last imported date and not confuse stale data with
missed payments. Automated analysis runs after import; live bank refresh is excluded.

Before cancellation, preserve available history and configuration using supported
exports plus validated connector reads where useful, verify missing fields/coverage,
and exercise normal Canopy workflows with the Monarch connector disabled. Importing
new data without Monarch is the exit check; building a replacement aggregator is not.

## Evidence and limits of this assessment

- Inspected the signed-in Monarch web account on 2026-11-15: Dashboard, Reports
  (cash flow and spending), Budget, Recurring, Goals, Investments, Forecasting,
  Transactions and transaction details/filters, Accounts, Cash Flow, Settings,
  Rules, and MCP Connector. Browsing was read-only; no account records were edited.
- Goals was an empty setup state; Forecasting displayed onboarding. Their complete
  configured workflows remain unverified. Report saving, rule execution, bank
  refresh, AI answers, and destructive actions were not exercised.
- This is a workflow inventory, **not numerical parity certification**. No private
  account data, identifiers, amounts, exports, or screenshots belong in this plan,
  Git, fixtures, issues, logs, or the workspace knowledge index.
- Reviewed all 33 open issues returned by the repository search, no open PRs
  returned, and fetched relevant closed implementation issues individually.
  Base: `origin/main` at `da20763`; local checkout was one commit behind.
- Existing epics [#47](https://github.com/raolivei/canopy/issues/47) and
  [#50](https://github.com/raolivei/canopy/issues/50) are the Wallet feature and UX
  umbrellas. Their original checklists are stale. Do not create duplicate epics.
- Existing references to `MONARCH_PARITY.md`, a parity memory file and a Monarch
  playbook do not resolve in the inspected local checkouts. This document is the
  current consolidated plan, not evidence those earlier artifacts were delivered.

## Monarch workflow inventory and Canopy gaps

| Area | Observed reference behavior | Canopy evidence and planned completion |
|---|---|---|
| Dashboard | Reorderable widgets, weekly recap, net worth/spending comparisons, recurring items, contextual AI entry points | Existing dashboard and insights; add persisted layout, recap, consistent period/account/currency filters and drill-through |
| Accounts | Account list, refresh, sorting/filtering; net worth history on dashboard | Existing account/balance APIs; reconcile sources and liability signs, add import freshness/error states, manual assets and historical corrections (bank refresh/reconnect excluded) |
| Transactions | Search/date/filters, categories/accounts/tags/amount, bulk editing, configurable columns, review/hide, splits, notes, attachments, activity | Existing CRUD/imports are a starting point; complete review queue, pending-to-posted lifecycle, safe bulk preview/undo, conserved splits, attachment links, audit history |
| Budget | Fixed/flexible/non-monthly groups, planned/actual/remaining, month/year/decade controls, contributions, CSV export | Models/service/API exist; no budget page. Add flexible and category modes, period-specific plans, rollover and non-monthly funding, contribution handling, editing and transaction drill-down |
| Cash flow | Monthly/quarterly/yearly views and filters | Service/API/chart components exist; no cash-flow page. Correct date boundaries, FX, refunds and transfer treatment; add savings rate and period comparisons |
| Reports | Cash flow/spending/income tabs, date/filter controls, chart type/grouping, save/report selection | Annual report exists; add reusable report definitions, saved filters, category/merchant trends, income sources, comparisons, chart/table exports and reconciliation |
| Recurring | List/calendar, review suggestions, filters, management, next occurrences | Detection service exists; complete API + persistent confirmed schedules, exclusions, variable amounts, missed/changed bills, calendar and review UI |
| Goals | Save up/pay down, allocation and goal creation controls | Empty reference setup; Canopy FIRE is not a savings/debt goals workflow. Add account-linked goals, allocations/contributions, progress and debt scenarios; validate full reference flow later |
| Investments | Market/allocation views, date selectors, holdings, asset grouping, account/owner controls, chart download | Holdings/portfolio/FIRE exist; validate return methodology, cost basis, contributions vs returns, benchmark data, dividends and currency coverage |
| Forecasting | Onboarding advertises life events and retirement scenarios | Canopy FIRE provides a starting point; add scenario assumptions, income/expense events, debt, inflation and tax assumptions with explicit uncertainty; full Monarch behavior unverified |
| Categories/rules | Category groups, tags, merchant settings; rules can rename, categorize and split, and apply top-to-bottom | Taxonomy and rules service exist; add CRUD/preview UI and audit/undo. Existing first-match semantics differ from Monarch's described ordered rules; make behavior explicit and test conflicts |
| Assistant | Contextual prompts, transaction explanation, weekly recap entry points | Provider/tool abstractions exist; add grounded answers, source links and period/filter context. Actual response quality and connector coverage remain unverified |
| Household/settings | Members, preferences, notifications, businesses, data/security settings | Navigation observed, permission behavior unverified. Design ownership/scoping now; implement shared views, roles and notifications after core single-user flows |

Rollover, benchmark choices, goal calculations, notification behavior, and shared
access are requirements to validate further, not claims of completed account testing.
Retain Canopy's visual identity while matching useful workflows and results.

## Architecture and calculation contract

Keep Next.js, FastAPI, PostgreSQL/Alembic, and the existing worker/provider patterns.
Add a Wallet/Tax switch; keep existing Wallet URLs working. Shared settings, search,
assistant, accounts, attachments, ownership and audit events serve both workspaces.
Store tax originals in a dedicated private document store, not the static web tree
or repository; PostgreSQL holds metadata, structured facts and links.

Before extending reports, establish one calculation layer used by pages, exports
and assistant tools. Define signed amounts, account/currency ownership, liabilities,
transfers, refunds, hidden/pending transactions, splits, calendar boundaries,
missing months, source precedence and FX dates. Use Decimal throughout aggregation.
Preserve original currency and rate provenance; missing FX must be explicit.
The current cash-flow implementation sums currencies then labels totals CAD and
uses approximate 30-day months. These are correctness gaps despite closed #66.
Portfolio display fallback FX must never silently become a tax conversion rate.

Imports need stable source IDs, idempotency, amendment detection, preview, reversible
batches and reconciliation. A repeated transaction with the same date/amount is not
necessarily a duplicate. Link pending to posted records without erasing reviewed
metadata. Register and exercise every router through the actual application:
budget/cash-flow routes currently exist on disk but are not mounted in `server.py`.
Do not simply expose them and declare their calculations validated.

## Tax model and workflows

| Record | Required meaning |
|---|---|
| Tax profile/year | Taxpayer ownership, jurisdiction, tax year, workflow status, completeness and unresolved items |
| Document/version | Original encrypted bytes, hash, media type, issuer/type, issue/receipt/upload dates, related years, processing status, superseded/amended relationships |
| Extracted fact | Field/line/box, raw value, normalized Decimal/currency, page and text span, extraction version/confidence, review state and correction history |
| Return/assessment | Filed return version vs original assessment vs reassessment; preserve all versions and distinguish reported from assessed amounts |
| Ledger entry | Assessment, payment, refund, interest, adjustment or credit; dated evidence and allocations across relevant years; avoid double counting balances and flows |
| Correspondence/action | CRA case/reference, linked documents/years, request summary, stated deadline and source, owner/status, draft response and resolution evidence |
| Wallet link | Match payments/refunds/eligible expenses to existing transactions, including partial/multiple matches; no duplicate financial transaction created from an upload |

Upload → validate/quarantine → hash/deduplicate → preserve original → extract text
or OCR in a bounded worker → classify → propose facts/year links → review uncertainty
→ update ledger/timeline → suggest actions. Reprocessing is idempotent and retains
provenance; failed/corrupt/password-protected files get actionable recovery states.
Document text is untrusted content and cannot authorize tools, correspondence or
changes. An LLM proposes facts; deterministic code checks dates, types and arithmetic.

Initial types: tax slips, contribution receipts, filed returns, notices of assessment
and reassessment, CRA requests and supporting receipts. A letter received in a later
year links to its actual tax year(s), retaining all dates. Multiple taxpayers remain
separate. Show carryforwards/contribution figures as sourced snapshots with as-of
dates, not guessed current entitlement. Track explicit and calculated deadlines
separately; legal deadline rules require verified sources and user review.

Year screen: summary, document checklist, filed/assessed comparison, ledger,
correspondence timeline, outstanding actions and export. Cross-year screen: history,
changes, carryforward evidence and unresolved cases. Assistant answers cite document
pages and distinguish confirmed facts from estimates. Tax tags in Wallet identify
items for review; categorization alone does not establish deductibility.

Exports bundle originals, structured data and a reviewed summary for the accountant
or filing software. CRA responses, payments and filing remain deliberate user actions.
NETFILE filing uses certified software; Canopy is initially a records/preparation
system ([CRA guidance](https://www.canada.ca/en/services/taxes/income-tax/personal-income-tax/how-file/tax-software/send-return.html)).

## Security and operations foundation

No application authentication was found in the inspected API wiring. Confirm the
actual deployed access boundary, then implement consistent authentication and
ownership enforcement for APIs, documents, exports, jobs and assistant retrieval.
Test unauthorized access and object-level isolation. Add secure session/CSRF controls
appropriate to the chosen auth mechanism and reauthentication for sensitive exports.

Use existing Vault/External Secrets and GitOps release workflows. Encrypt document
storage and backups, protect keys separately, test restoration of DB plus originals,
and define retention/deletion behavior including derived text, indexes and backups.
Mask identifiers, avoid private data in logs/metrics and keep tax files outside
workspace indexing. Verify the actual processing destination of each model provider;
a locally hosted gateway alone does not prove local inference. Bound file size,
page count, processing time, worker concurrency and retries for Raspberry Pi capacity.
Monitor job state/latency/errors, not balances or financial text.

## Existing issue reconciliation

All issue numbers below refer to `raolivei/canopy`. States are observed as of this
assessment; recommendations here have not changed GitHub issue state.

| Existing work | State/evidence | Disposition |
|---|---|---|
| #47 / #50 | Open feature/UX epics with stale checklists | Retain as umbrellas; align child acceptance with this plan and real workflows |
| #48 / #49 | Open migration/secrets foundation | Verify deployment and finish with migration-failure + restore tests; security work precedes tax ingestion |
| #61–#63 | Closed budget models/service/API | Reuse; route wiring, period plans, validation and integration tests still needed before #64–#65 |
| #64 / #65 | Open budget UI/chart | Deliver one complete workflow, including flex/non-monthly semantics from account review |
| #66 / #67 | Service closed, UI open | Correct calculation contract and route wiring before completing page and reports |
| #68 / #69 | Detection closed, UI open | Reuse detection; add persisted review decisions, API and list/calendar workflow |
| #70–#72 | Taxonomy/engine closed, rules UI open | Reuse foundations; complete category administration, preview, rule-order semantics and split invariants |
| #51 / #54–#57 | Closed skeleton/button/chart/insights/accessibility work | Verify on new screens; component-level completion does not establish page coverage |
| #52 / #53 / #58–#60 | Open recovery/confirmations/filter/export/bulk work | Apply consistently to Wallet and Tax; sensitive form persistence must avoid leaking records into browser storage |
| #73 / #74 | Open Monarch API spike/scheduled sync | Re-scope #73 to temporary official read-only reference access; defer permanent scheduled Monarch sync (#74) |
| #75–#77 | Tools closed, golden questions/provider deployment open | Remove false parity evidence, finish real calculations, expand tool coverage and test actual tool selection |
| #78 / #79 / #80 | Open metrics/playbook/cutover | Redact financial values, document official connector and coverage, require reconciled history + working CSV/document imports with Monarch disconnected before cutover |
| #82–#84 | Open query limits/N+1/aggregation | Aggregate complete periods in SQL; paginate listings. Never cap rows silently to make a financial total faster |
| #21 / #23 | Open broker/payment integrations, code already exists | Existing code may remain; expansion is outside this build and these issues do not block Monarch cancellation |
| #24 | Open dividend/income streams | Fit within Wallet investments and connect supporting documents to Tax |
| #26 | Open legacy property feature | Manual value/history/equity first; automated valuation and Brazil scope require feasibility review |
| #16 | Open ML categorization | Preserve user categories and corrections; start with rules and measured confidence before committing to a heavy ML stack |
| #17 | Open legacy multi-bank automation | Explicitly excluded by the user; defer bank/aggregator connectivity and browser-login automation |
| #27 | Open API docs | Generate current routes/contracts; document auth, errors, pagination, exports and Tax |
| #29 / #30 | Open investment intelligence/OpenClaw suites | Map into Wallet investments/assistant; external fundamentals/news/valuation sources need separate evidence and decisions |
| #106 | Closed CI inactivity investigation | Closure documents no eligible events after June, not a disabled workflow. Do not reopen without new evidence; test current release path when shipping |

New work packages needed (local planning IDs, not invented GitHub issues):
W1 shared navigation and ownership; W2 transaction review/splits/attachments;
W3 saved reports/weekly recap; W4 goals and forecasting; W5 account freshness and
source reconciliation; T1 secure document vault; T2 extraction/review; T3 yearly
tax ledger and assessment history; T4 CRA actions and reminders; T5 cross-year
assistant, Wallet matching and accountant export. Create/link these under the
existing Wallet epics and a Tax epic when publishing the implementation backlog.

## Delivery order and exit checks

| Milestone | Dependencies and scope | Exit evidence |
|---|---|---|
| 0. Honest baseline | Account workflow inventory, issue audit, independent reference validation | No missing-reference passes; every feature marked observed/partial/unverified; private comparison protocol defined |
| 1. Shared foundation | Auth/ownership, migrations, secrets, backup/restore, calculation contract, imports | Unauthorized requests fail; restored records/files agree; synthetic money/FX/date/dedup tests pass; actual routes exercised |
| 2. Wallet daily use | Milestone 1; transactions, categories/rules, budgets, cash flow, recurring, navigation | End-to-end create/edit/review/filter/drill-down/export workflows work with consistent totals, mobile/keyboard/error recovery |
| 3. Tax first release | Milestone 1 document controls and navigation; T1–T4 | Mixed-year PDF/scan batch produces source-linked reviewable facts, preserves amendments, shows yearly ledger and CRA action timeline; no unreviewed deadline treated as confirmed |
| 4. Full analysis | Milestone 2; reports, recaps, goals, forecast, investment analysis; T5 after milestone 3 | Same period/filter yields same numbers across UI/API/export/assistant; forecast assumptions visible; tax citations and Wallet matches verified |
| 5. Parallel use/cutover | All agreed must-have capabilities and CSV/document/manual ingestion | Two complete monthly review cycles reconciled, available history/configuration preserved with gaps resolved, normal workflows verified with Monarch disconnected, rollback/restore proven; user decides subscription cancellation |

Use small releasable changes with feature flags where useful, preserving existing
Wallet routes. Avoid a year-long divergent branch. Reuse image publishing and Flux
automation; any new Eldertree hostname requires the workspace routing playbook.
Show each UI increment locally with synthetic data before PRs. Test migrations on
PostgreSQL, not only SQLite, and verify ARM OCR/model resource use before promising
interactive performance. No time estimate is a delivery guarantee before these spikes.

## Verification protocol

Use a fixed cutoff, same account set, timezone, dates, currencies and visibility
filters. Compare counts, source IDs and exact monetary sums (cent-level differences
explained by stated rounding); do not accept blanket ±2% or ±5% ledger tolerances.
Compare investment values at aligned timestamps and quote sources. Estimates and
predictions use explicit tolerances and methodology, not ledger equality rules.

Keep CI fixtures synthetic. Live account validation remains private and records
only sanitized outcomes in the repository. Missing permissions, provider omissions,
pagination gaps or unavailable references are **unverified**, never success.
Test transfers, refunds, duplicate-looking purchases, amended imports, hidden/pending
rows, split conservation, leap dates/month ends, missing FX, liability signs,
multiple currencies and accounts. For Tax test duplicates, reassessments, multi-year
letters, ambiguous deadlines, corrupt files, OCR failures and partial payment matches.

The current golden-question implementation also contains placeholder budget and
subscription answers and a net-worth calculation based on income. Removing its
self-comparison fallback is only the first fix; it remains unsuitable for cutover
certification until calculations, official connector schemas, pagination, provenance
and coverage checks are complete. Its API currently supplies no Monarch client.

## Feasibility decisions and user checkpoints

| Capability | Current evidence | Next decision |
|---|---|---|
| Official Monarch connector | Account settings expose `https://api.monarch.com/mcp`; no tools connected. Official documentation supports OAuth/read-only access | Prefer this for authorized reference comparisons over the old unofficial-client proposal. A new persistent connection requires the user's OAuth consent; browser assessment already works |
| Connector completeness | Monarch documents that Finicity-sourced data is unavailable through MCP, plus usage limits | Inventory account coverage before numeric comparisons; use supported exports/UI where needed, with explicit incomplete coverage. Do not switch bank providers automatically |
| Independent bank sync | Explicitly excluded by the user | No Plaid/Finicity/MX integration, bank-login automation or new direct connectors in this build; use CSV/documents/manual entries |
| Goals/forecasting | Setup/onboarding observed; full behavior unverified | Continue read-only reference review or use a disposable test profile before changing the live plan |
| OCR/LLM capacity | Local provider abstractions exist; document performance unmeasured | Benchmark representative synthetic PDFs/scans on target hardware; ask before external document processing or extra infrastructure spending |
| Automatic CRA filing/responses | Records/preparation feasible; certified filing is a separate integration | Keep draft/export workflow; ask about any filing integration rather than implying uploads file a return |
| Household/business/international scope | Settings and legacy issues exist; tax need currently CRA-focused | Model ownership now. Clarify additional taxpayers, business returns or jurisdictions before their dependent implementation; preserve current CAD/USD behavior |

Sources: [Monarch connector documentation](https://help.monarch.com/hc/en-us/articles/50207234679956-Monarch-MCP-Connector),
updated November 13, 2026; signed-in UI observations above; repository code and linked
GitHub issues. The post-Monarch ingestion strategy is CSV/document upload and manual entry.
No bank subscription, provider access or data coverage is assumed.

## Work completed in this change

- Recorded this assessment and issue/dependency map; linked it from README.
- Removed the golden-question fallback that used Canopy's own answers as Monarch
  references. Missing/failed references now produce unavailable failures; execution
  errors remain in the denominator, respect stop-on-failure and hide exception bodies.
- Added regression tests for absent/failing references, error accounting and genuine
  mismatches. This change does not connect Monarch, enable tax uploads or establish parity.

Next implementation slice: shared calculation contract and actual route/service
integration tests, then budget/cash-flow workflows and the document security foundation.

Validation for this change: 25 focused tests passed (existing golden questions, new
reference-failure regressions, and application health). Changed Python sections were
formatted; targeted correctness lint and the new test file's lint passed. Full project
lint is blocked by the existing missing `workspace-config/python/ruff.toml` extension;
an isolated full lint also reports pre-existing findings in the touched service/schema.
No production deployment, GitHub issue mutation or numerical parity certification
was performed.
