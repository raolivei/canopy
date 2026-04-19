---
name: canopy-agent-conventions
description: >-
  Canopy repo norms for AI agents: CHANGELOG style, privacy, and scope. Apply
  when editing Canopy, writing changelog/commits, or handling user/financial data.
---

# Canopy agent conventions

## Changelog

- Keep entries **short**: one line per theme when possible; avoid repeating the same story across Changed/Fixed.
- No multi-paragraph feature specs in `CHANGELOG.md` — link to PR/issue if detail is needed.

## Privacy and public artifacts

- **Never** put real names, account numbers, full card/bank numbers, addresses, or transaction amounts from the author’s data into: commits, PR text, `CHANGELOG`, README examples, tests, fixtures, screenshots, or logs.
- Use placeholders (`****8813`, `example@…`, synthetic CSV snippets) in examples and tests.

## Code changes

- Touch only what the task needs; match existing patterns; no drive-by refactors or unsolicited docs.
