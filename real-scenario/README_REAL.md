# Real working scenario (all 4 use cases, live)

A real mini QA environment: `shop_api.py` is the system under test, `tests/` is a
real pytest regression suite, and `ai_qa/` contains the AI agents that operate on
REAL failures, REAL git diffs, and REAL files.

## One-time setup
```bash
pip install pytest
```
(.env with ANTHROPIC_API_KEY must exist in the repo root, as before)

## Live demo run-order (from the real-scenario/ folder)

```bash
cd real-scenario

# 1. Baseline: real suite is green
python3 -m pytest tests/ -q

# 2. UC3 - AI writes a new test from a Fiddler-style capture, and it passes
python3 ai_qa/gen_api_test.py
python3 -m pytest tests/test_generated_from_capture.py -q

# 3. A developer refactors the API (real code change + real git commit)
python3 simulate_dev_change.py

# 4. UC2 - AI reads the REAL git diff and predicts which tests are impacted
python3 ai_qa/impact.py

# 5. Suite is now really broken
python3 -m pytest tests/ -q

# 6. UC4 - AI drafts a real ticket file from the real failures
python3 ai_qa/make_ticket.py

# 7. UC1 - AI heals the suite: proposes fix, you approve, it applies + re-runs
python3 ai_qa/heal.py
```

## Reset (to run the demo again)
```bash
git reset --hard origin/main
```
