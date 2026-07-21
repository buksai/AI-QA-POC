# AI in QA Automation — Trafigura POC

**Author:** Huseynbala Gurbanli

A real, working proof of concept demonstrating AI-assisted QA automation for
Trafigura's trade capture system — a Java-based, action-driven test framework
covering commodity trade lifecycle scenarios (trade creation, tranche
shipments, external valuation via Jupiter, baseline evidence checks).

**Everything relevant is in [`trafigura-scenario/`](./trafigura-scenario/).**
See [`trafigura-scenario/README_TRAFIGURA.md`](./trafigura-scenario/README_TRAFIGURA.md)
for the full run order and rationale.

## Use cases covered

1. **Self-healing regression tests** (priority) — AI reads a real test failure
   and a real git diff, proposes a corrected scenario baseline, applies it
   after human approval, and re-runs to green
2. **Smart test maintenance** — AI reads a real code change and predicts
   which scenarios are impacted, before any test even runs
3. **Agent-based issue creation** — AI drafts a ready-to-file bug ticket from
   real test failure output
4. **Bonus: WPF → Playwright action migration** — AI migrates a legacy WPF
   desktop UI action to the equivalent Playwright web action, for the planned
   React UI migration

## Requirements

- JDK 21+ (`javac -version` to check)
- Python 3 with `pip install -r requirements.txt`
- `.env` in the repo root with `ANTHROPIC_API_KEY=...`

## Quick start

```bash
cd trafigura-scenario
python3 web_app.py
```
Open `localhost:5003` and click through the 7 steps in order.

Full details, CLI-only instructions, and the reasoning behind the design are
in `trafigura-scenario/README_TRAFIGURA.md`.

## V2 — advanced version

[`trafigura-scenario-v2/`](./trafigura-scenario-v2/) is a more advanced build:
a real running backend, two functioning UIs (legacy WPF-style + new web-style)
both driving the same live business logic, and an autonomous AI agent that
investigates and decides for itself rather than following a fixed sequence of
buttons. See [`trafigura-scenario-v2/README_V2.md`](./trafigura-scenario-v2/README_V2.md).
