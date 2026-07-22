---
name: smart-test-maintenance
description: 'Analyze a real application code or configuration change (backend or frontend), determine which automated test scenarios are impacted and why, and propose or apply test fixes based on that specific impact analysis. Use this whenever the user mentions a code change, a git diff, a config change, "what tests does this affect," impact analysis, or when investigating why previously-passing tests started failing after something changed in the application. This is distinct from routine self-healing: the emphasis here is explaining the causal chain from a specific change to specific impacted scenarios, not just fixing whatever is currently red.'
---

# Smart Test Maintenance from Application Changes

Maps a real application change (backend/frontend, config or code) to the specific
test scenarios it impacts, and proposes fixes tied to that analysis — not a
blind "run everything and see what's red" approach.

## Two kinds of application change you'll encounter here

1. **Live runtime configuration changes** — the backend
   (`trafigura-scenario-v2/backend`) exposes real admin endpoints that flip
   business-logic toggles at runtime (e.g. `/api/admin/handling-fee`,
   `/api/admin/pricing-cutoff`, `/api/admin/volume-discount`,
   `/api/admin/regression-event` which flips several at once). Check current
   state with `GET` on each endpoint before analyzing impact.
2. **Real committed source changes** — use `git log` and `git diff` (read-only;
   never `git reset` or `git checkout` on the user's behalf without being asked)
   to see what actually changed in a given file. E.g.:
   ```
   git log -1 --format=%H -- <path/to/file>
   git diff <that-commit>~1 <that-commit> -- <path/to/file>
   ```
   Scope this to the specific file/directory in question — don't run a broad
   diff across the whole repository, since that pulls in unrelated history.

## Impact analysis procedure

1. **Identify what actually changed.** Read the real diff or the current runtime
   config state — don't guess. Name the specific field, endpoint, method, or
   business rule that changed.
2. **Search for scenarios that reference the changed thing.** Grep
   `src/scenarios/*.java` for the relevant field name, method call, or endpoint.
   Read each match to understand exactly how it depends on the changed behavior —
   don't assume; check whether the reference is load-bearing (an assertion) or
   incidental (e.g. a date used only as a display field, not as a query
   parameter).
3. **Explain WHY each scenario is impacted**, specifically — cite the exact line
   or assertion in that file, and connect it to the exact change. A scenario is
   NOT impacted just because it superficially resembles others that are — verify
   each one individually. (For example: two scenarios might both reference the
   same date-like string, but only one of them actually passes it as a pricing
   query parameter — the other might only use it as a shipment month, in which
   case it's not actually impacted by a pricing-data change.)
4. **Propose the fix per scenario**, tied to the specific impact identified — not
   a generic "update the baseline" without justification.
5. **Apply fixes only to the scenarios confirmed impacted.** Don't touch files
   that merely look similar but weren't confirmed via step 2-3.
6. **Recompile and re-run** the specific impacted scenarios (or the full suite)
   to confirm the fix resolves them without introducing new failures.

## Output format

Present impact analysis as:
- **What changed** (the specific diff, endpoint, or config value, before → after)
- **Impacted scenarios** (list, each with the specific reason it's impacted)
- **Scenarios that looked related but were NOT impacted** (and why, if you
  checked and ruled any out — this builds trust that the analysis was real,
  not a blanket assumption)
- **Proposed/applied fix per impacted scenario**
- **Rerun confirmation**
