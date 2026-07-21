# Trafigura POC — V2

**V1** (`trafigura-scenario/`) proved the four use cases work against a real Java
suite, one click per step. **V2** goes further in three ways:

1. **A real running backend** — an actual HTTP API (`backend/`), not just a CLI
   test runner. Both UIs below call it live.
2. **Two real, functioning UIs** side by side — a legacy WPF-styled desktop
   client (`ui-legacy/`) and a new web client (`ui-web/`) styled for the React
   migration, both driving the *same* backend and business logic. This is a
   working demonstration of exactly the migration the manager described: same
   controls, same content, only the UI technology changes.
3. **An autonomous AI agent** (`agent/`) — not a fixed sequence of buttons.
   Given a small toolset (check the suite, read the git diff, read/write
   scenario files, draft tickets, read legacy actions for migration) and one
   open-ended instruction, the agent decides for itself what to investigate,
   in what order, and what to fix. Every reasoning step and tool call streams
   live to a web dashboard — you watch it think, not just see a final answer.

## Requirements

- JDK 21+ (`javac -version`)
- Python 3, `pip install -r requirements.txt`
- `.env` in the **repo root** (`AI-QA-POC/.env`) with `ANTHROPIC_API_KEY=...`
  — same key used by V1

## One-time setup

```bash
cd trafigura-scenario-v2
./setup.sh
```

This creates an isolated git history inside `agent/workspace/` — the agent's
own sandbox copy of the codebase, kept separate from your main repo history
so its investigate/fix cycle never pollutes `AI-QA-POC`'s actual commits.

## Running it

### 1. The backend (start this first — both UIs depend on it)

```bash
cd backend
find src -name "*.java" > sources.txt
javac -d out @sources.txt
java -cp out api.TradeApiServer 5100
```

Leave this running. It's a real HTTP server — check it:
```bash
curl http://127.0.0.1:5100/api/health
```

### 2. The two UIs — open both, side by side

Just open these two files directly in your browser (no server needed, they're
static HTML that calls the backend over CORS):

- `ui-legacy/index.html` — the old WPF-styled desktop client
- `ui-web/index.html` — the new web client, using the same `data-testid`
  attributes as the Playwright migration in V1

Create a trade in one, and you can look it up via the other (they share the
same backend state) — proving the migration preserves business behavior.

### 3. The autonomous agent dashboard

```bash
cd agent
python3 dashboard.py
```
Open `localhost:5101`.

- **"Apply dev change"** — breaks the suite (same 1.5% handling fee change as V1)
- **"Run autonomous agent"** — the agent independently investigates and fixes,
  streaming its reasoning live
- **"Reset workspace"** — back to clean baseline

The agent is not told anything is broken. It decides on its own whether to
check the suite, whether to look at the diff, whether the failure is a stale
baseline (fix it) or a genuine defect (ticket it), and when it's done.

## Why this is the stronger pitch for "vision"

V1 answers: *"can AI do these four things?"* — yes, shown one at a time.

V2 answers a harder, more senior question: *"can this be an actual system,
not a script?"* — a live backend proving business logic is UI-agnostic (the
exact migration problem they have), and an agent architecture that
investigates and acts with judgment rather than following a fixed runbook.
That's the difference between a POC and a product direction.
