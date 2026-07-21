# AI in QA Automation — Trafigura POC

**Author:** Huseynbala Gurbanli

A real, working proof of concept demonstrating AI-assisted QA automation for
a Trafigura-style trade capture system: a live Java backend, two synchronized
front-ends (legacy desktop-style and modern web), and an autonomous AI agent
that investigates and heals a 54-scenario regression suite running on 50
concurrent workers — all real, nothing simulated.

**Everything is in [`trafigura-scenario-v2/`](./trafigura-scenario-v2/).**
See [`trafigura-scenario-v2/README_V2.md`](./trafigura-scenario-v2/README_V2.md)
for full setup and run instructions.

## Use cases covered

1. **Self-healing regression tests** — the agent investigates real failures,
   checks a shared team knowledge base and approved requirements, then
   proposes and applies fixes at scale (one call can fix 30+ files at once)
2. **Smart test maintenance** — impact analysis from real backend
   configuration changes and real git diffs
3. **API test generation from Fiddler captures** — the agent reads a real
   captured HTTP session and generates a runnable test action class from it
4. **Agent-based issue creation** — genuine product defects (backed by an
   approved requirement) get a well-evidenced ticket; stale tests get fixed
   instead — the agent never confuses the two

## Requirements

- JDK 21+ (`javac -version` to check)
- Python 3 with `pip install -r requirements.txt`
- `.env` in the repo root with `ANTHROPIC_API_KEY=...`

## Quick start

See [`trafigura-scenario-v2/README_V2.md`](./trafigura-scenario-v2/README_V2.md)
for the full backend + control-center startup sequence and demo flow.
