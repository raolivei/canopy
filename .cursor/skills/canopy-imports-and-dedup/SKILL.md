---
name: canopy-imports-and-dedup
description: >-
  Monarch and Wealthsimple import behavior, internal keys vs display names, and
  dedup. Use when changing importers, monarch/*, wealthsimple/*, or import APIs.
---

# Imports and dedup

## Internal keys vs labels

- Importers may create **`Asset.symbol`** (or liability keys) as **stable internal identifiers** (e.g. Monarch-derived slugs). **`Asset.name`** should remain **human-readable**.
- Any **user-facing** list (holdings, accounts) should prefer **name** + institution/last4—not raw slug—as the primary label unless the row is a traded security ticker.

## Monarch

- Transactions and **balances** may use separate CSV shapes; routing by **header** (e.g. `Date,Balance,Account` → balances) when combined upload is supported.
- Do not assume all currencies: product scope is **CAD/USD**; foreign rows may be skipped with counters.

## Wealthsimple

- Filename and row parsers are strict; classify WS files so they do not hit the **portfolio snapshot** importer by mistake.

## Dedup

- **Canonical hash** / per-source hashes prevent double-counting across Monarch and Wealthsimple—edits to fingerprint rules require careful regression tests.

## Testing

- Tests must use **synthetic** CSV strings and entities—never real export snippets from production.
