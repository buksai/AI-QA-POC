# Trafigura POC — V2: Unified Control Center

**V1** (`../trafigura-scenario/`) proved the four use cases work, one click per
step, against an isolated test copy. **V2 is one real system**, not three
separate demos glued together:

- **One live backend** (`backend/`) — real HTTP API, real business logic
- **Three views on it, all in one browser tab** via the **Control Center**:
  1. **POC AI Engineer** — the autonomous agent, live-streaming its reasoning
  2. **Trafigura Enterprise Legacy Demo** — the legacy WPF-style desktop UI
  3. **New System** — the new web UI (React migration target)

Everything reads from and writes to the **same running backend**. Create a
trade in "New System," switch to "POC AI Engineer," flip the handling-fee
toggle, switch back — the trade's valuation has genuinely changed. This isn't
three demos that happen to share a repo; it's one system viewed three ways.

## What's genuinely different from V1

| | V1 | V2 |
|---|---|---|
| Backend | none — CLI compiles/runs a Java suite directly | real HTTP API server (JDK's HttpServer) |
| UI | none | two full UIs (legacy + web), both live |
| "Dev change" | a git commit that edits source code | a real runtime toggle via `POST /api/admin/handling-fee` — no recompile |
| Agent's tests | isolated in-memory `TradeCaptureSystem` | real HTTP calls to the live backend — same one the UIs use |
| Investigation | fixed click-through sequence | agent decides its own steps via tool-use |
| Entry point | 3 separate `python3 web_app.py` processes on 3 ports | 1 control center + 1 backend = 2 processes total |

## Requirements

- JDK 21+ (`javac -version`)
- Python 3, `pip install -r requirements.txt`
- `.env` in the **repo root** (`AI-QA-POC/.env`) with `ANTHROPIC_API_KEY=...`

## One-time setup

```bash
cd trafigura-scenario-v2
```
(no separate agent workspace git history needed anymore — the agent's suite
now calls the live backend directly, so there's nothing to isolate via a
separate git repo)

## Running it — two processes

### 1. Start the backend

```bash
cd backend
find src -name "*.java" > sources.txt
javac -d out @sources.txt
java -cp out api.TradeApiServer 5100
```

Leave this running. Every request it handles prints to this terminal — this
is "seeing the backend work."

### 2. Start the Control Center

```bash
cd control_center
python3 app.py
```

Open **`localhost:5099`**. Three tabs, one page.

## The demo flow that proves synchronization

1. Go to **"New System"** tab → create a trade → confirm it → get valuation
   (e.g. $8,500,000)
2. Go to **"POC AI Engineer"** tab → click **"Apply dev change"** — this is a
   real `POST` to the backend's runtime toggle, not a code edit
3. Go back to **"New System"** → fetch that same trade's valuation again →
   it's now $8,627,500 (+1.5%), with **zero code change, zero restart**
4. Back in **"POC AI Engineer"** → click **"Run autonomous agent"** — it
   independently checks the suite, finds 2 failures, checks the backend's
   config, recognizes the fee is the cause, patches the two stale baselines,
   confirms green — reporting its reasoning the whole way
5. The connection status badge (top right) shows the backend's live fee state
   at all times, polling every 3 seconds

## Why this is the stronger pitch

V1 answers: *"can AI do these four things?"*

V2 answers a harder question a senior hire should be able to answer: *"can
this be one coherent system instead of four scripts?"* A shared backend
proving business logic is UI-agnostic (their actual WPF→React migration
problem), a live runtime toggle instead of git-commit theater, and an agent
whose tests exercise the real system — that's a product architecture, not a
proof-of-concept script.
