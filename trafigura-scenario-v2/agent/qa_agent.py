"""
Autonomous QA Agent — V2 centerpiece.

This is NOT a fixed pipeline where a human clicks "step 1, step 2, step 3."
The agent is given a small set of tools (investigate the suite, read the
recent code diff, read/write scenario files, draft tickets, migrate legacy
actions) and a single instruction: "the regression suite may or may not be
healthy — figure out what's going on and fix what needs fixing, using your
own judgment about the order and necessity of each step."

Claude decides, autonomously, via real tool-use (function calling):
  - whether to check the suite at all
  - whether to look at the git diff
  - whether healing is needed, and what the correct fix is
  - whether to draft a ticket
  - when it's actually done

Every tool call and the agent's own reasoning between calls is logged, so
the process is fully auditable — this is "propose, then act," not a black box.
"""
import os
import re
import json
import subprocess
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
from anthropic import Anthropic

load_dotenv(find_dotenv())
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

WORKSPACE = os.path.join(os.path.dirname(__file__), "workspace")
MODEL = "claude-sonnet-4-6"


def _run(cmd, cwd=WORKSPACE):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=120)
    return (r.stdout or "") + (r.stderr or ""), r.returncode


# ----------------------------------------------------------------------
# Tools the agent can independently choose to call
# ----------------------------------------------------------------------

def tool_check_suite(_args):
    _run(["bash", "-c", "find src -name '*.java' > sources.txt"])
    out, rc = _run(["javac", "-d", "out", "@sources.txt", "TestRunner.java"])
    if rc != 0:
        return {"compiled": False, "output": out}
    out2, rc2 = _run(["java", "-cp", "out:.", "TestRunner"])
    return {"compiled": True, "passed": rc2 == 0, "output": out2}


def tool_get_recent_diff(_args):
    out, _ = _run(["git", "diff", "HEAD~1", "--", "src/system/"])
    if not out.strip():
        return {"diff": "", "note": "No committed system change found in the last commit."}
    return {"diff": out[:6000]}


def tool_list_scenario_files(_args):
    out, _ = _run(["git", "ls-files", "src/scenarios/"])
    return {"files": out.strip().splitlines()}


def tool_read_file(args):
    path = args["path"]
    full = os.path.join(WORKSPACE, path)
    if not os.path.abspath(full).startswith(os.path.abspath(WORKSPACE)):
        return {"error": "path outside workspace"}
    with open(full) as f:
        return {"content": f.read()}


def tool_write_file(args):
    path = args["path"]
    content = args["content"]
    full = os.path.join(WORKSPACE, path)
    if not os.path.abspath(full).startswith(os.path.abspath(WORKSPACE)):
        return {"error": "path outside workspace"}
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)
    return {"written": path, "bytes": len(content)}


def tool_draft_ticket(args):
    os.makedirs(os.path.join(WORKSPACE, "tickets"), exist_ok=True)
    name = "tickets/TICKET-" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".md"
    full = os.path.join(WORKSPACE, name)
    with open(full, "w") as f:
        f.write(args["content"])
    return {"ticket_written": name}


def tool_migrate_wpf_action(args):
    path = args.get("path", "legacy_wpf_actions/ConfirmTradeAction.cs")
    full = os.path.join(WORKSPACE, path)
    with open(full) as f:
        return {"wpf_action_source": f.read()}


TOOLS = [
    {
        "name": "check_suite",
        "description": "Compile and run the real Java regression suite. Returns compile status, pass/fail, and full output. Call this whenever you need to know the current health of the suite.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_recent_diff",
        "description": "Get the real git diff of the most recent commit to the system-under-test (src/system/). Use this to understand what a developer just changed, before or after checking test results.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "list_scenario_files",
        "description": "List the real scenario files tracked in git under src/scenarios/.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "read_file",
        "description": "Read the full content of a file in the workspace by relative path (e.g. 'src/scenarios/CopperConcentrateTradeScenario.java').",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Overwrite a file in the workspace with new content. Use this to apply a fix to a scenario file after you've decided on the correct new content. This is a real file write — be precise.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
            "required": ["path", "content"],
        },
    },
    {
        "name": "draft_ticket",
        "description": "Write a bug ticket as a markdown file into tickets/. Use this if you find a failure that looks like it could be a genuine defect worth a human's attention, separate from routine baseline maintenance.",
        "input_schema": {
            "type": "object",
            "properties": {"content": {"type": "string"}},
            "required": ["content"],
        },
    },
    {
        "name": "migrate_wpf_action",
        "description": "Read a legacy WPF C# UI action so you can produce its Playwright TypeScript equivalent for the web migration. Only call this if specifically relevant to your task.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
        },
    },
]

DISPATCH = {
    "check_suite": tool_check_suite,
    "get_recent_diff": tool_get_recent_diff,
    "list_scenario_files": tool_list_scenario_files,
    "read_file": tool_read_file,
    "write_file": tool_write_file,
    "draft_ticket": tool_draft_ticket,
    "migrate_wpf_action": tool_migrate_wpf_action,
}

SYSTEM_PROMPT = """You are an autonomous senior QA engineer agent responsible for the \
Trafigura trade capture regression suite (Java, action-based test framework, \
commodity trade lifecycle scenarios with Jupiter valuation baselines).

You have NOT been told what is currently wrong, if anything. You decide, on your \
own initiative, what to investigate and in what order, using the tools available. \
A reasonable investigation usually checks the suite's health and the recent change \
history, but you are not required to follow any fixed sequence — use your judgment.

If you find failures caused by a legitimate change in business logic (a stale \
baseline), propose the corrected scenario file and write it directly with \
write_file, then re-check the suite to confirm it's green. If a failure looks like \
a genuine defect rather than routine baseline drift, draft a ticket instead of \
silently patching over it — explain your reasoning for the distinction.

Work autonomously through as many tool calls as you need. When you are done, \
respond with a final plain-text summary (no more tool calls) describing what you \
found, what you changed, and why — as if reporting to a human engineering lead."""


def run_agent(user_task, on_event=None):
    """Runs the agentic loop. on_event(kind, data) is called for each step so a
    caller (CLI or web dashboard) can stream progress live."""

    def emit(kind, data):
        if on_event:
            on_event(kind, data)

    messages = [{"role": "user", "content": user_task}]
    emit("start", {"task": user_task})

    for turn in range(12):  # hard cap so a runaway agent can't loop forever
        response = client.messages.create(
            model=MODEL,
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        # Surface any reasoning text the model produced this turn
        for block in response.content:
            if block.type == "text" and block.text.strip():
                emit("reasoning", {"text": block.text})

        if response.stop_reason != "tool_use":
            # Agent is done — final answer
            final_text = "".join(b.text for b in response.content if b.type == "text")
            emit("final", {"summary": final_text})
            return final_text

        # Execute every tool call the model requested this turn
        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            emit("tool_call", {"name": block.name, "input": block.input})
            fn = DISPATCH.get(block.name)
            try:
                result = fn(block.input) if fn else {"error": "unknown tool"}
            except Exception as e:
                result = {"error": str(e)}
            emit("tool_result", {"name": block.name, "result": result})
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result)[:4000],
            })
        messages.append({"role": "user", "content": tool_results})

    emit("final", {"summary": "Agent hit the turn limit without concluding."})
    return "Agent hit the turn limit without concluding."


if __name__ == "__main__":
    def printer(kind, data):
        if kind == "start":
            print(f"\n>>> TASK: {data['task']}\n")
        elif kind == "reasoning":
            print(f"[agent reasoning]\n{data['text']}\n")
        elif kind == "tool_call":
            print(f"[tool call] {data['name']}({json.dumps(data['input'])[:200]})")
        elif kind == "tool_result":
            print(f"[tool result] {json.dumps(data['result'])[:300]}\n")
        elif kind == "final":
            print(f"\n=== AGENT SUMMARY ===\n{data['summary']}\n")

    run_agent(
        "Investigate the current state of the regression suite and fix anything "
        "that needs fixing. Report your findings and actions when done.",
        on_event=printer,
    )
