# Trafigura-specific POC — Real Java Trade Capture Scenario

Built to match what was discussed on the call: Java-based test framework, action
building blocks, baseline comparison against Jupiter valuation, commodity trade
lifecycle (copper concentrate, tranches, shipment). This is a **real, runnable**
system — not pasted text — using the same domain vocabulary described.

**Priority use case demonstrated: self-healing (UC1).**

## Requirements
- JDK 21 (or any recent JDK) — `java -version` and `javac -version` to check
- Python 3 with `anthropic` and `python-dotenv` installed (`pip install anthropic python-dotenv`)
- `.env` in the repo root with `ANTHROPIC_API_KEY=...` (same one used elsewhere in this repo)

## What's in here

```
trafigura-scenario/
├── src/
│   ├── system/            # the trade capture system under test
│   │   ├── Trade.java
│   │   ├── Tranche.java
│   │   ├── TradeValuation.java
│   │   ├── JupiterValuationClient.java   # mock external pricing system
│   │   └── TradeCaptureSystem.java
│   ├── actions/            # reusable action building blocks (their vocabulary)
│   │   ├── CreateTradeAction.java
│   │   ├── AddTrancheAction.java
│   │   ├── ConfirmTradeAction.java
│   │   ├── GetJupiterValuationAction.java
│   │   └── CompareBaselineAction.java
│   └── scenarios/
│       └── CopperConcentrateTradeScenario.java   # end-to-end regression scenario
├── TestRunner.java          # tiny dependency-free test runner (no JUnit/Maven needed)
├── simulate_dev_change.py   # makes a REAL code change + REAL git commit (adds a handling fee)
├── ai_qa/
│   ├── heal.py              # UC1 — self-healing (PRIORITY)
│   ├── impact.py            # UC2 — impact analysis from real git diff
│   ├── make_ticket.py       # UC4 — ticket drafting from real failure output
│   └── migrate_wpf_action.py # BONUS — WPF C# action -> Playwright TS action
└── legacy_wpf_actions/
    └── ConfirmTradeAction.cs # sample legacy WPF action for the migration bonus
```

## The story

1. Real scenario runs — 2 passed, 0 failed
2. A developer adds a 1.5% port handling fee to the Jupiter valuation calculation
   (a real, common kind of change) — real code change, real git commit
3. Suite re-run — genuinely fails: `expected=8500000.0 actual=8627500.0`
4. **Self-healing (priority):** AI reads the real failure + the real diff, proposes
   an updated baseline in the scenario file, shows the diff, **you approve**, it
   applies the fix, recompiles, re-runs — green again
5. Impact analysis: AI reads the same diff and predicts which scenarios are affected
   — this can run *before* step 3, proactively
6. Ticket drafting: AI drafts a ticket from the real failure, noting it looks like
   a stale baseline rather than a genuine defect

## Run order

```bash
cd trafigura-scenario

# 0. Baseline — compile and confirm green
find src -name "*.java" > sources.txt
javac -d out @sources.txt TestRunner.java
java -cp out:. TestRunner
# -> 2 passed, 0 failed

# 1. Developer makes a real change (adds handling fee) + real commit
python3 simulate_dev_change.py

# 2. UC2 — AI predicts impact from the diff alone (no test run yet)
python3 ai_qa/impact.py

# 3. Recompile and re-run — confirms it's genuinely broken
javac -d out @sources.txt TestRunner.java
java -cp out:. TestRunner
# -> 1 passed, 1 failed: Baseline mismatch on 'valuation.totalValueUsd'

# 4. UC4 — AI drafts a ticket from the real failure
python3 ai_qa/make_ticket.py

# 5. UC1 — self-healing (the priority case): propose -> approve -> apply -> green
python3 ai_qa/heal.py
# review the proposed diff, type 'y' to approve

# BONUS — WPF to Playwright action migration
python3 ai_qa/migrate_wpf_action.py
```

## Reset

```bash
git reset --hard origin/main
```

## Why this maps to what was described on the call

- **Actions** are separate reusable classes (`CreateTradeAction`, `AddTrancheAction`,
  etc.) exactly like their action library concept — steps as building blocks
- **Baseline comparison** (`CompareBaselineAction`) mirrors their evidence-check
  pattern: record expected values once, compare on every run
- **The break** (handling fee change) is deliberately the kind of change they
  described causing real problems — a legitimate business logic change that
  makes recorded baseline evidence stale, not a bug
- **Self-healing** fixes the *scenario's* baseline, not the system — matching
  the brief's exact wording: "propose/apply code fixes... to the automated
  scenarios in accordance to the impact analysis"
- **WPF migration bonus** answers your own idea from the call: since business
  logic and controls stay the same during the React migration, only the UI
  interaction layer changes — a natural AI migration task
