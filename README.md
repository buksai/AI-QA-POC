# AI in QA Automation — POC

Working prototype demonstrating 4 AI-assisted QA use cases (matching the client brief):

1. **Self-healing regression tests** — AI analyzes failures from test runs, identifies root cause, proposes code fixes
2. **Smart test maintenance** — AI analyzes code changes (PRs/commits) and identifies which test scenarios are impacted
3. **API test generation** — AI generates test action classes from captured HTTP traffic (Fiddler-style)
4. **Agent-based issue creation** — AI drafts ready-to-file bug tickets from test execution results

**Guardrail:** human-in-the-loop everywhere. AI proposes; engineers approve. Nothing merges or files automatically.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the root with:
```
ANTHROPIC_API_KEY=your_key_here
```

## Run — two modes

**Interactive web UI** (4 tabs, one per use case):
```bash
python app.py
```
Then open http://localhost:5000

**End-to-end simulation** (one command, plays through a full nightly QA cycle):
```bash
python simulate_day.py
```

## Next phase (full POC)

- Connect UC1 to real CI failure logs instead of pasted text
- Connect UC2 to the actual git repo (webhook on PR)
- Parse real Fiddler .saz session files for UC3
- Connect UC4 to Jira/ADO API for one-click ticket filing
