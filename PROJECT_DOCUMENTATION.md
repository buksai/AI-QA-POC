# AI in QA Automation — Project Documentation

**Author:** Huseynbala Gurbanli
**Repo:** https://github.com/buksai/AI-QA-POC
**Status:** POC complete, ready to present
**Date:** 15 July 2026

> **Purpose of this document:** full context for anyone (human or AI) picking up this project. Explains why it exists, what's in the repo, exactly what is real vs. what is next phase, how to run it, and the plan for today's manager meeting.

---

## 1. Background — why this exists

My manager (Oleksii Rudyi) sent me the client's brief. The client is a DXC customer with a large automated QA process. They identified four areas of their QA workflow where AI could be applied, and asked:

> *"Can you prepare a POC on these use cases and present to the client?"*

The four use cases, verbatim from the brief:

1. **Automated regression test scenarios "self-healing"** — proposing/applying code fixes based on the analysis of failures happened periodically during tests execution (daily/weekly cycles)
2. **"Smart" test scenarios maintenance** — analysis of the main system's code changes (back-end/front-end) → definition of the impacted test scenarios → proposing/applying code fixes to the automated scenarios in accordance to the impact analysis performed before
3. **Back-end (API) automated scenarios specific** — automatic development of test action classes based on Fiddler session captures
4. **Using agents for issues creation** based on test execution results

This repo is my answer to that request.

---

## 2. The problem, in plain terms

The client runs a large automated regression suite (order of hundreds of tests) on **daily/weekly cycles**. Every cycle produces failures. Today, a human QA engineer has to:

| Manual task today | Time cost |
|---|---|
| Open each failure, read logs, figure out *why* it broke | Hours per cycle |
| After developers change code, guess which tests are affected (or re-run everything) | Slow or risky |
| Hand-write test code for new API endpoints from recorded traffic | Hours per endpoint |
| Hand-write Jira/ADO tickets for genuine bugs | Repetitive, inconsistent quality |

Crucially, **most failures are not real bugs.** They're maintenance noise — a developer renamed a field, changed a selector, altered an enum. The test is "broken," the product is fine. Human hours get burned on triage that has a mechanical answer.

**The thesis of this POC:** an LLM can do the mechanical triage — read the failure, read what changed, and propose the fix — while humans keep the decision. That converts hours of investigation into minutes of review.

---

## 3. What's in the repo

The repo contains **two demos**, deliberately. They serve different purposes.

```
AI-QA-POC/
├── README.md                    # project overview
├── requirements.txt             # flask, pytest, anthropic, python-dotenv
├── .gitignore                   # blocks .env and venv/ from being committed
│
├── app.py                       # DEMO A: concept demo — Flask, 4 tabs (port 5000)
├── templates/index.html         #         its UI (one tab per use case)
├── simulate_day.py              # DEMO A: narrated CLI walkthrough of a QA night
│
└── real-scenario/               # DEMO B: the real working system
    ├── README_REAL.md           #   exact run-order for the live demo
    ├── shop_api.py              #   SYSTEM UNDER TEST — a real running shop API
    ├── conftest.py              #   pytest path config
    ├── tests/
    │   └── test_shop_api.py     #   REAL pytest regression suite (2 tests)
    ├── captures/
    │   └── checkout_capture.txt #   Fiddler-style captured request/response
    ├── simulate_dev_change.py   #   makes a REAL code change + REAL git commit
    ├── ai_qa/
    │   ├── heal.py              #   UC1 — self-healing agent
    │   ├── impact.py            #   UC2 — impact analysis agent
    │   ├── gen_api_test.py      #   UC3 — API test generator
    │   └── make_ticket.py       #   UC4 — ticket drafting agent
    ├── web_app.py               #   web UI wrapper for the real scenario (port 5002)
    └── templates/
        └── real_scenario.html   #   its UI — 7 clickable steps
```

### Demo A — the concept demo (`app.py`, port 5000)

Four tabs, one per use case. You paste in sample data, click a button, the AI responds live. Input is manual (pasted text).

**What it's for:** explaining each use case in isolation. Good for a client audience that wants to understand *what* each capability does before seeing it in motion.

### Demo B — the real scenario (`real-scenario/`)

A self-contained working QA environment. A real application, a real test suite, and AI agents that operate on **real failures, real git diffs, and real files** — nothing is pasted in by hand.

**What it's for:** proving it actually works. This is the one that matters.

---

## 4. How Demo B works — the narrative

This is the important part. Demo B tells one continuous story:

| Step | What happens | Use case |
|---|---|---|
| 1 | Real pytest suite runs against `shop_api.py` → **2 passed, green** | baseline |
| 2 | AI reads `captures/checkout_capture.txt` and **writes a real pytest file**. That file is then run — **it passes**. | **UC3** |
| 3 | `simulate_dev_change.py` makes a **real code change** to `shop_api.py` (renames `total` → `grandTotal`, status `created` → `CREATED`) and makes a **real git commit** | — |
| 4 | AI runs `git diff HEAD~1`, reads the **actual diff**, and predicts which test scenarios are impacted and what updates they need — **before any test has run** | **UC2** |
| 5 | Real pytest suite runs → **2 failed**, `KeyError: 'total'` — the prediction is confirmed | — |
| 6 | AI reads the **real pytest output** and writes a real ticket file into `tickets/` | **UC4** |
| 7 | AI reads the real failure + real diff, **proposes a corrected test file**, shows the diff, **asks for human approval**, applies it to the real file, re-runs the suite → **green again** | **UC1** |

The demo is resettable (`git reset --hard origin/main`) so it can be run repeatedly.

**Why this design is defensible:** the AI is never given the answer. It gets the same inputs a QA engineer gets — a stack trace and a git diff — and has to work out the rest. The failure in step 5 is a genuine `KeyError`, not a printed string.

---

## 5. Scope — what is real vs. what is next phase

**This is the most important section. Do not overclaim in the meeting. Read this before answering any question about scope.**

| Use case | What is genuinely real and working | What is NOT built (Phase 2) |
|---|---|---|
| **UC1 — Self-healing** | Runs the real suite; reads real pytest output + real git diff; proposes a fix; shows a diff; **human approves (y/n)**; **applies the fix to the real file**; re-runs until green. The "applying" half of the brief is done, human-gated. | Not connected to a real CI system (Jenkins/ADO/GitHub Actions). Doesn't open a PR. Runs locally against a sample app, not the client's application. |
| **UC2 — Smart maintenance** | Reads the **real** `git diff` of the last commit and the real test file list; predicts impacted scenarios and what updates they need. | Not triggered by a webhook on PR. Proposes scenario updates but does not auto-apply them (UC1 covers applying). No integration with an existing traceability matrix. |
| **UC3 — API test generation** | Reads a capture file, generates a **runnable pytest file**, which then **actually passes** against the live app. | Capture is a text file in Fiddler's request/response shape — **not a parsed `.saz` binary**. Generates pytest; if the client's framework is Java/RestAssured, Demo A shows that output flavour. `.saz` parsing is phase 2. |
| **UC4 — Agent issue creation** | Runs the real suite, reads real failure output, writes a real ticket file into `tickets/`. | Does not file into Jira/ADO via API. No deduplication against existing open tickets. |

### How to say this out loud

**If asked "is this production-ready?"**
> "No — and it shouldn't be. This is a POC. What it proves is that the AI reasoning layer works for all four use cases against real failures and real diffs. What's left is integration plumbing: CI logs, git webhooks, `.saz` parsing, Jira API. That's engineering work, not a feasibility question anymore."

**If asked "the brief says *apply* fixes, not just propose"**
> "It does apply them — `heal.py` writes the corrected file and re-runs the suite. But it's gated behind human approval by design. In a client environment nothing should touch the test suite without review. In phase 2, approved fixes get applied to a branch and raised as a PR."

**If asked "why didn't you use Fiddler itself?"**
> "The capture is in Fiddler's request/response shape. The agent only needs the request/response pairs — it doesn't care whether they came from Fiddler, Charles, or DevTools. Parsing real `.saz` files is a phase 2 task and it's a file format problem, not an AI problem."

---

## 6. How to run it

### One-time setup

```bash
git clone https://github.com/buksai/AI-QA-POC.git
cd AI-QA-POC
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create `.env` in the repo root:
```
ANTHROPIC_API_KEY=sk-ant-...
```
`.env` is gitignored and never committed.

### Demo A — concept demo

```bash
python app.py
```
Open **http://localhost:5000** in a browser (not the terminal).

### Demo B — real scenario, web version (recommended for the meeting)

```bash
cd real-scenario
python3 web_app.py
```
Open **http://localhost:5002** in a browser. Click the 7 steps in order. "Reset demo" restores the starting state.

### Demo B — real scenario, CLI version

```bash
cd real-scenario

python3 -m pytest tests/ -q                                # 1. green baseline
python3 ai_qa/gen_api_test.py                              # 2. UC3 — AI writes a test
python3 -m pytest tests/test_generated_from_capture.py -q  #    ...and it passes
python3 simulate_dev_change.py                             # 3. dev breaks the API
python3 ai_qa/impact.py                                    # 4. UC2 — AI predicts impact
python3 -m pytest tests/ -q                                # 5. really broken
python3 ai_qa/make_ticket.py                               # 6. UC4 — AI drafts a ticket
python3 ai_qa/heal.py                                      # 7. UC1 — approve with 'y' → green
```

### Reset the demo

```bash
git reset --hard origin/main
```

### Known gotchas

- URLs go in the **browser**, never in the terminal.
- The terminal running the server must be left alone — typing in it kills the server.
- `venv` must be activated (`source venv/bin/activate`) or `python` won't be found.
- Run the demo steps **in order** — each depends on the previous one's state.

---

## 7. Technical design

**Model:** `claude-sonnet-4-6` via the Anthropic Python SDK.

**Pattern used throughout:** each agent is a thin, single-purpose script that
1. gathers real evidence from the environment (`subprocess` → pytest output, `git diff`, source files),
2. sends that evidence to the model with a tightly scoped prompt,
3. writes the result back to a real artifact (a test file, a ticket file, a proposed diff).

No agent framework, no vector DB, no fine-tuning. It's deliberately simple — for a POC, moving parts are a liability, and every dependency is a question you have to answer.

**Self-healing loop (`heal.py`)** is the only stateful one: run → fail → propose → *human approves* → apply → re-run, up to 3 rounds. If it can't reach green in 3 rounds it stops and flags for human review rather than thrashing.

**Guardrails built in:**
- Human approval before any file is modified (`heal.py` prints a unified diff and waits for `y`)
- Bounded retry loop — no infinite healing attempts
- Agents write to the working tree only; nothing is pushed or merged
- API key in `.env`, gitignored, never committed

---

## 8. Plan for today's meeting

### Suggested flow (~6 minutes)

1. **Frame the problem (30s).** "Every cycle, hundreds of tests run and some fail. Most failures aren't bugs — they're maintenance noise from a renamed field or selector. Engineers burn hours triaging things that have a mechanical answer."

2. **State what I built (15s).** "Two things: a concept demo showing each of the four use cases in isolation, and a real working environment where all four run against a live test suite. I'll show the real one."

3. **Run Demo B live, narrating each step:**
   - *Step 1:* "Real pytest suite. Green."
   - *Step 2:* "That's UC3. The AI just wrote that test file from a captured request — and it passes."
   - *Step 3:* "Now a developer refactors the API. Real code change, real commit."
   - *Step 4:* "**This is the interesting one.** No test has run yet. The AI is reading the git diff alone and predicting what will break."
   - *Step 5:* "And it's right. Real failures."
   - *Step 6:* "UC4 — ticket drafted from the actual failure output."
   - *Step 7:* "UC1 — it proposes the fix, **I approve it**, it applies and re-runs. Green."

4. **Land the guardrail (15s).** "Nothing moves without human approval. AI proposes, engineers decide."

5. **Close with scope (30s).** "Feasibility is proven for all four. Phase 2 is integration: CI logs, git webhooks, `.saz` parsing, Jira API. That's about 4–5 weeks."

### The one line that carries the demo

> "No test has run yet — the AI is predicting the damage from the code change alone."

That's step 4, and it's the moment that separates this from a chatbot wrapper.

### Q&A prep

| Question | Answer |
|---|---|
| How long is the full POC? | 4–5 weeks: 1 setup, 2–3 build, 1 measure, then demo. |
| What do you need from us? | Access to the test repo, CI execution results, sample Fiddler captures, tracker access (Jira/ADO). |
| Will AI change our tests without us knowing? | No. Human approval on every change, full audit trail, no auto-merge. |
| What if the AI proposes a wrong fix? | It's shown as a diff and rejected in review — same as any PR. Bounded to 3 attempts, then it escalates to a human. |
| Why is this better than just re-running everything? | Re-running tells you *that* something broke. This tells you *why*, and proposes the fix. UC2 tells you *before* you even run. |
| What data leaves our environment? | For the POC, test logs and diffs go to the model API. For a client rollout that's a deployment decision — this needs to be agreed with their security team before real code touches it. |
| What if it doesn't work? | That's why it's a POC. Small scope, low cost, and we know before committing. |

### Success criteria to propose for the full POC

- **UC1:** majority of locator/schema-drift failures fixed automatically without rework
- **UC2:** impact analysis catches everything QA re-tested manually (recall matters more than precision)
- **UC3:** meaningful time reduction vs. hand-writing test classes
- **UC4:** ticket quality comparable to manual, no duplicates

---

## 9. Phase 2 — what integration actually means

| Use case | Integration work |
|---|---|
| UC1 | Hook into the real CI pipeline; pull failures from run artifacts; apply approved fixes to a branch and open a PR |
| UC2 | Webhook on PR open; map changed modules to test coverage using the existing traceability matrix; post the impact report as a PR comment |
| UC3 | Parse real `.saz` session files; generate in the client's actual framework and coding standards |
| UC4 | Jira/ADO API integration; dedup against open tickets before filing; attach real evidence (logs, screenshots) |

Cross-cutting: audit logging of every AI-proposed change, and a data-handling agreement covering what leaves the client environment.

---

## 10. Honest self-assessment

**What's genuinely strong here:**
- All four use cases work against real evidence, not pasted mock text
- UC1 closes the full loop — propose, approve, apply, verify green
- The demo is resettable and repeatable, so it can be run live without fear
- Guardrails are built in, not bolted on as talking points

**What a sharp reviewer will push on, and they'd be right:**
- The system under test is a toy app I wrote, not the client's application. Their real suite has scale, flakiness, and coupling this doesn't
- `.saz` parsing isn't implemented
- No metrics yet — no baseline of how long manual triage actually takes at this client, so "time saved" is a claim, not a measurement. **Establishing that baseline should be week 1 of the real POC**
- Self-healing on a 2-test suite proves the mechanism; it doesn't prove the accuracy rate at 500 tests. That's exactly what the POC measurement phase is for

Say these before they're asked. Naming your own gaps is what makes the rest of the claims credible.
