---
name: agentic-issue-creation
description: 'Draft a well-evidenced bug ticket from test execution results, but only for genuine defects backed by an approved requirement - never for routine test maintenance issues that can simply be fixed. Use this whenever a test failure needs to be escalated to a human, whenever the user asks to "file a ticket," "create an issue," "write up this bug," or after investigating failures that turn out not to be explainable by any known fix pattern. Do not trigger this for failures that are stale-test drift fixable via known patterns - fix those instead (see self-healing-regression skill).'
---

# Agent-Based Issue Creation

Drafts a properly evidenced bug ticket from real test execution results — but
only when escalation is actually warranted, and never as a substitute for a fix
the agent could and should have applied itself.

## When to create a ticket (and when NOT to)

**Create a ticket only when ALL of these are true:**
1. The failure does not match any known fix pattern in
   `knowledge_base/fix_patterns.json` (you've verified this — checked the trigger
   strings AND recomputed the numbers to confirm no pattern's factor explains it)
2. An approved requirement in `knowledge_base/requirements.json` documents the
   behavior the test correctly asserts
3. The live backend/application is observably violating that requirement
4. No code change removes or supersedes the requirement

**Do NOT create a ticket when:**
- The failure is explainable by a known pattern — fix it instead (see the
  self-healing-regression skill)
- The test asserts behavior with no backing requirement — this is an
  "unsupported test expectation," not a confirmed defect. Say so explicitly and
  don't file a ticket implying the application is wrong when the test itself
  might be the thing that's incorrect or premature.
- You're not fully sure — say what's ambiguous and ask, rather than filing a
  ticket that later turns out to be a misdiagnosis.

## Ticket contents

Write tickets as markdown files under `tickets/` (create the directory if it
doesn't exist). Every ticket should include:

- **Title** — concise, states the actual defect, not just "test X failing"
- **Severity** — with brief justification (financial/business impact, blast
  radius, how many scenarios are affected)
- **Requirement violated** — quote the requirement ID and its exact approved
  text from `requirements.json`
- **Evidence table** — for each affected scenario: quantity/inputs, expected
  value (per the requirement), actual value (from the live backend), and the
  ratio or delta between them
- **Root cause hypothesis** — your best explanation for why the defect exists
  (e.g. "a runtime flag governing this behavior is disabled"), citing what you
  checked to arrive at that hypothesis
- **Why this is NOT routine test drift** — explicitly state which patterns you
  checked and ruled out, and why the requirement-violation explanation fits
  better
- **Steps to reproduce** — concrete, runnable steps (API calls or scenario names)
  a human could follow to see the defect themselves
- **Explicit instruction not to "fix" the test** — state plainly that the test
  baseline is correct and must not be changed to match the broken behavior,
  since doing so would silently legitimize the defect

## After filing

Report back to the user: which scenarios remain failing on purpose, the ticket
file path, and a one-line summary of the requirement violated. Do not treat a
filed ticket as "the task is done" if other scenarios in the same investigation
were still fixable — finish those first (or in parallel), and be clear about
which failures got which treatment.
