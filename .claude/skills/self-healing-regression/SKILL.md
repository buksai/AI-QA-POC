---
name: self-healing-regression
description: 'Investigate and self-heal a failing Java regression suite for the Trafigura trade capture test framework. Use this whenever the regression suite in trafigura-scenario-v2/agent/workspace is failing, whenever the user asks to "run the tests," "check the suite," "investigate failures," or mentions periodic (daily/weekly) regression runs. Also trigger proactively if TestRunner.java reports any failures during an unrelated task, since a broken suite blocks everything else. Do NOT trigger for one-off single-test debugging unrelated to the regression pack.'
---

# Self-Healing Regression Suite

Investigates real test failures in the Java regression suite and proposes/applies
fixes — the daily/weekly self-healing cycle a QA team would run.

## Where things live

- `TestRunner.java` — compiles and runs every scenario in `src/scenarios/` on a
  concurrent worker pool. Run it with:
  ```
  find src -name "*.java" > sources.txt
  javac -d out @sources.txt TestRunner.java
  java -cp out:. TestRunner
  ```
- Backend must be running first: `cd ../../backend && java -cp out api.TradeApiServer 5100`
  (compile it first if `out/` doesn't exist: `find src -name "*.java" > sources.txt && javac -d out @sources.txt`)
- `knowledge_base/fix_patterns.json` — patterns the team has taught the agent over
  time (each has an `id`, a `trigger` string to match against failure output, a
  `root_cause`, a `fix` description, a worked numeric `example`, and who taught it).
  **Always read this before attempting a fix from scratch** — if a failure's error
  message matches a pattern's `trigger`, use that pattern's fix.
- `knowledge_base/requirements.json` — approved business requirements. **Before
  concluding a failure is a genuine product defect, you must check this file** and
  confirm an approved requirement backs the expected test behavior.
- `knowledge_base/scenario_manifest.json` — maps every scenario ID to a category
  (e.g. `pricing_date`, `fee_drift`, `healthy`, `genuine_defect`). Use it to
  reconcile exact pass/fail counts by category instead of eyeballing raw output.

## Investigation procedure

1. **Run the suite** and capture full output (per-test PASS/FAIL lines + any
   AssertionError/RuntimeException detail).
2. **Check live backend state** — this is a real running Java process with runtime
   toggles (e.g. `GET /api/admin/handling-fee`, `/api/admin/pricing-cutoff`,
   `/api/admin/volume-discount`). A restarted backend silently resets these to
   healthy defaults, which can make a previously-broken suite look clean again —
   if the suite passes unexpectedly, check whether this happened before reporting
   "all healthy."
3. **Read the knowledge base.** For each failure, match its error message against
   every pattern's `trigger`. A pattern match means this is stale-test drift, not
   a defect.
4. **Verify the match mathematically before trusting it.** Don't just pattern-match
   the trigger string — recompute the numbers yourself (e.g. if a valuation is off
   by exactly the fee pattern's known factor, the ratio should match precisely).
   If the ratio doesn't match any known pattern's factor, do NOT force that fix —
   this is a signal you may be looking at a genuine defect (see below) or an
   unknown issue.
5. **Apply fixes at scale, not one file at a time.** If many scenarios share the
   same stale value (a hardcoded date, an old fee-exclusive baseline), fix them
   all in one pass — grep for the pattern across `src/scenarios/*.java` and update
   every match. Preserve each file's own quantity/values; don't collapse different
   files to one literal number if they compute their expected value from their own
   inputs (e.g. `qty * price` expressions) — append the fix factor to the
   expression instead of replacing it with a single number.
6. **Before touching ANY scenario file, check whether its own comments/docstring
   forbid it.** Files documenting a genuine defect (see requirements skill/section)
   will say so explicitly — respect that and do not "fix" their baseline.
7. **Re-run the suite** after applying fixes to confirm the fix worked and nothing
   else regressed.
8. **Report clearly**, categorized: which failures were fixed (and which pattern/
   fix explained each), and which remain failing and why (see next section).

## Distinguishing stale tests from genuine defects

A failure is **stale-test drift** (fix it) when:
- Its error matches a known pattern's trigger, AND
- The corrected numbers match that pattern's expected factor exactly

A failure is a **genuine product defect** (do NOT fix the test) when:
- No known pattern explains the failure ratio/behavior, AND
- An approved requirement in `knowledge_base/requirements.json` documents the
  expected behavior the test asserts, AND
- The backend is observably violating that requirement

If a failure matches neither of these cleanly, say so explicitly — don't force a
classification. Leave it failing and flag it as needing human review, citing what
you checked and why it didn't fit either bucket.

## Reporting format

End every investigation with:
1. Before/after pass-fail counts (use the scenario manifest to break down by
   category if helpful)
2. What was fixed, and which knowledge-base pattern(s) explained it, with the
   actual diff or before/after values
3. What was deliberately left failing, and why — cite the requirement ID if
   applicable
4. Anything ambiguous that needs a human decision
