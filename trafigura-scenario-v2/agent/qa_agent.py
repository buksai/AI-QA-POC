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
  - whether to check the live backend's runtime business configuration
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


def tool_check_backend_config(_args):
    import urllib.request
    import json as _json
    try:
        result = {}
        with urllib.request.urlopen("http://127.0.0.1:5100/api/admin/handling-fee") as resp:
            result.update(_json.loads(resp.read()))
        with urllib.request.urlopen("http://127.0.0.1:5100/api/admin/pricing-cutoff") as resp:
            result.update(_json.loads(resp.read()))
        with urllib.request.urlopen("http://127.0.0.1:5100/api/admin/volume-discount") as resp:
            result.update(_json.loads(resp.read()))
        return result
    except Exception as e:
        return {"error": f"Could not reach backend: {e}"}


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


def tool_recompute_valuation_baselines(args):
    """Recalculates every valuation baseline assertion across all scenario
    files by a given multiplier - e.g. applying a newly-enabled 1.5% fee
    (multiplier=1.015) to whatever expected value is already coded, no
    matter what quantity that file uses. This is formula-based smart
    maintenance, not blind string substitution: each file's baseline is
    individually recalculated from its own current value. Handles both
    literal baselines (e.g. 8500000.00) and expression baselines
    (e.g. 2000 * 4250.0) - appends the multiplier to expressions rather
    than collapsing them to a single number, matching the codebase's style."""
    import re
    import difflib
    multiplier = args.get("multiplier")
    if multiplier is None:
        return {"error": "requires 'multiplier' argument (e.g. 1.015 for a 1.5% fee)"}
    multiplier = float(multiplier)

    scenario_dir = os.path.join(WORKSPACE, "src", "scenarios")
    # Captures: field name, the expected-value expression (anything up to the next comma), rest of args
    pattern = re.compile(
        r'(assertNumeric\("(?:[\w]+\.)?totalValueUsd",\s*)'
        r'([^,]+?)'
        r'(,\s*\w+,\s*[\d.]+\);)'
    )
    files_fixed = []
    diffs = {}

    for fname in sorted(os.listdir(scenario_dir)):
        if not fname.endswith(".java"):
            continue
        fpath = os.path.join(scenario_dir, fname)
        with open(fpath) as f:
            original = f.read()

        # SAFETY: never touch scenarios linked to an approved requirement
        # (e.g. REQ-114 volume discount) - those failures are semantically
        # distinct from a fee/date maintenance issue, and must be evaluated
        # against the requirement, not silently recalculated away.
        if "REQ-114" in original or "VolumeDiscount" in fname:
            continue

        changed = [False]
        def repl(m):
            expr = m.group(2).strip()
            already_has_multiplier = "* 1.0" in expr and expr.count("*") >= 2
            if already_has_multiplier:
                return m.group(0)  # don't double-apply
            if re.fullmatch(r"-?\d+\.?\d*", expr):
                # Pure literal - recalculate the number directly
                new_val = round(float(expr) * multiplier, 2)
                new_expr = f"{new_val}"
            else:
                # Expression (e.g. "2000 * 4250.0") - append the multiplier factor
                new_expr = f"{expr} * {multiplier}"
            changed[0] = True
            return f"{m.group(1)}{new_expr}{m.group(3)}"

        fixed = pattern.sub(repl, original)
        if changed[0] and fixed != original:
            diff_lines = list(difflib.unified_diff(
                original.splitlines(), fixed.splitlines(),
                fromfile=fname + " (before)", tofile=fname + " (after)",
                lineterm="", n=1
            ))
            with open(fpath, "w") as f:
                f.write(fixed)
            files_fixed.append(fname)
            diffs[fname] = "\n".join(diff_lines)

    diff_report = "\n\n".join(diffs[f] for f in files_fixed)
    return {
        "files_fixed": files_fixed,
        "total_fixed": len(files_fixed),
        "multiplier_applied": multiplier,
        "diff": diff_report
    }


def tool_scan_and_fix_pattern(args):
    """Scans all scenario files for a pattern and applies the same fix to all matches.
    Returns the actual before/after diff for every changed file, so the fix is
    visible - not a silent bulk edit."""
    import difflib
    pattern_text = args.get("find", "")
    replacement = args.get("replace", "")
    if not pattern_text or not replacement:
        return {"error": "requires 'find' and 'replace' arguments"}

    scenario_dir = os.path.join(WORKSPACE, "src", "scenarios")
    files_fixed = []
    files_skipped = []
    diffs = {}

    for fname in sorted(os.listdir(scenario_dir)):
        if not fname.endswith(".java"):
            continue
        fpath = os.path.join(scenario_dir, fname)
        with open(fpath) as f:
            original = f.read()
        if pattern_text in original:
            fixed = original.replace(pattern_text, replacement)
            diff_lines = list(difflib.unified_diff(
                original.splitlines(), fixed.splitlines(),
                fromfile=fname + " (before)", tofile=fname + " (after)",
                lineterm="", n=1
            ))
            with open(fpath, "w") as f:
                f.write(fixed)
            files_fixed.append(fname)
            diffs[fname] = "\n".join(diff_lines)
        else:
            files_skipped.append(fname)

    diff_report = "\n\n".join(diffs[f] for f in files_fixed)

    return {
        "files_fixed": files_fixed,
        "files_skipped": files_skipped,
        "total_fixed": len(files_fixed),
        "pattern_applied": f"'{pattern_text}' -> '{replacement}'",
        "diff": diff_report
    }


def tool_read_requirements(_args):
    import json as _json
    path = os.path.join(WORKSPACE, "knowledge_base", "requirements.json")
    if not os.path.exists(path):
        return {"error": "requirements fixture not found"}
    with open(path) as f:
        return _json.load(f)


def tool_get_scenario_inventory(_args):
    """Cross-references the last suite run's PASSED/FAILED lines against the
    scenario manifest to produce reconciled counts by category - answers
    exactly how many scenarios in each category (pricing_date, fee_drift,
    healthy, genuine_defect) passed vs failed, so totals are never left
    ambiguous or unreconciled."""
    import json as _json
    import re as _re

    manifest_path = os.path.join(WORKSPACE, "knowledge_base", "scenario_manifest.json")
    if not os.path.exists(manifest_path):
        return {"error": "scenario manifest not found"}
    with open(manifest_path) as f:
        manifest = _json.load(f)
    category_by_id = {s["id"]: s["category"] for s in manifest["scenarios"]}

    suite_result = tool_check_suite({})
    output = suite_result.get("output", "")

    status_by_id = {}
    for line in output.split("\n"):
        m = _re.match(r"(PASSED|FAILED)\s+\[[\w-]+\]\s+([\w.]+)", line)
        if m:
            status_by_id[m.group(2)] = m.group(1)

    from collections import defaultdict
    breakdown = defaultdict(lambda: {"passed": 0, "failed": 0, "total": 0})
    unreconciled = []
    for scenario_id, status in status_by_id.items():
        cat = category_by_id.get(scenario_id)
        if cat is None:
            unreconciled.append(scenario_id)
            continue
        breakdown[cat]["total"] += 1
        breakdown[cat]["passed" if status == "PASSED" else "failed"] += 1

    return {
        "total_scenarios_run": len(status_by_id),
        "total_in_manifest": len(category_by_id),
        "by_category": dict(breakdown),
        "unreconciled_scenario_ids": unreconciled,
        "raw_suite_output": output
    }


def tool_get_app_diff(args):
    """Read the REAL git diff of the most recent commit that touched a given
    application source file - safe, read-only (git diff/log only, never
    reset/checkout). Use this for genuine smart maintenance: read what
    actually changed in the application code, then reason about which
    scenarios are impacted and why, by reading their source with read_file -
    don't just apply a pre-canned pattern."""
    path = args.get("path", "backend/src/system/JupiterValuationClient.java")
    repo_root = _run(["git", "rev-parse", "--show-toplevel"])[0].strip()
    # Find the most recent commit touching this path
    commit_out, rc = _run(["git", "log", "-1", "--format=%H", "--", path], cwd=repo_root)
    commit = commit_out.strip()
    if not commit:
        return {"error": f"no commit history found for path: {path}"}
    diff_out, _ = _run(["git", "diff", commit + "~1", commit, "--", path], cwd=repo_root)
    message_out, _ = _run(["git", "log", "-1", "--format=%s%n%b", commit], cwd=repo_root)
    return {
        "path": path,
        "commit": commit,
        "commit_message": message_out.strip(),
        "diff": diff_out[:6000]
    }


def tool_read_knowledge_base(_args):
    import json as _json
    path = os.path.join(WORKSPACE, "knowledge_base", "fix_patterns.json")
    if not os.path.exists(path):
        return {"error": "knowledge base not found"}
    with open(path) as f:
        return _json.load(f)


def tool_read_fiddler_capture(args):
    path = args.get("path", "captures/create_order.saz.txt")
    full = os.path.join(WORKSPACE, path)
    if not os.path.abspath(full).startswith(os.path.abspath(WORKSPACE)):
        return {"error": "path outside workspace"}
    if not os.path.exists(full):
        return {"error": f"capture not found: {path}"}
    with open(full) as f:
        return {"capture": f.read()}


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
        "name": "check_backend_config",
        "description": "Check the LIVE backend's runtime business configuration (currently: whether the Jupiter port handling fee is enabled). The suite calls the real running backend over HTTP, so a change here is the equivalent of a code/config change a developer just made - call this to understand WHY the suite might be failing, the same way you'd read a diff.",
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
        "name": "recompute_valuation_baselines",
        "description": "Recalculate EVERY valuation baseline assertion across all scenario files by a multiplier, individually per-file (each file's current baseline is multiplied, not replaced with one fixed string). Use this for fee-type changes where different scenarios have different quantities but share the same percentage change (e.g. multiplier=1.015 for a newly-enabled 1.5% fee). This is formula-based - it reads each file's own current value and recalculates it, rather than a blind find/replace.",
        "input_schema": {
            "type": "object",
            "properties": {"multiplier": {"type": "number", "description": "e.g. 1.015 to apply a 1.5% increase"}},
            "required": ["multiplier"]
        },
    },
    {
        "name": "scan_and_fix_pattern",
        "description": "Scan ALL scenario files and apply the same fix to every file that contains the pattern. This is how you fix 50 scenarios at once — not one by one. Provide 'find' (the exact text to find, e.g. a broken date or wrong parameter) and 'replace' (what to replace it with). Returns the list of files changed AND a unified diff showing the exact before/after code change for every file — include this diff in your final report so the change is visible, not just the file count.",
        "input_schema": {
            "type": "object",
            "properties": {
                "find": {"type": "string", "description": "exact text to find across all scenario files"},
                "replace": {"type": "string", "description": "replacement text to apply in every matched file"}
            },
            "required": ["find", "replace"]
        },
    },
    {
        "name": "read_requirements",
        "description": "Read the formal, approved business requirements fixture. Each requirement has an ID, text, approval evidence, and the scenarios that test it. Before classifying ANY failure as a genuine product defect, you MUST check whether an approved requirement backs the expected behavior and cite its ID. A test expecting behavior with no backing requirement is NOT a confirmed defect - classify it as 'unsupported test expectation' instead and say so explicitly.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_scenario_inventory",
        "description": "Get a reconciled inventory of the last suite run, cross-referenced against the scenario manifest: exact pass/fail counts broken down by category (pricing_date, fee_drift, healthy, genuine_defect). Use this instead of manually counting from raw suite output - it eliminates ambiguity about which numbers belong to which category.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_app_diff",
        "description": "Read the REAL git diff of the most recent commit that changed a given application source file (safe, read-only). Use this for genuine smart maintenance: understand what actually changed in the application, then use list_scenario_files and read_file to reason about which scenarios are impacted and why - do not just apply a pre-canned pattern. Default path is backend/src/system/JupiterValuationClient.java.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "relative path from repo root, e.g. trafigura-scenario-v2/backend/src/system/JupiterValuationClient.java"}}
        },
    },
    {
        "name": "read_knowledge_base",
        "description": "Read the team's shared knowledge base of known fix patterns. Each pattern has a trigger (error signature from logs), root cause, and fix. Multiple engineers contribute patterns here — Wagner, Vera, and others. Call this when you see a failure to check if it matches a known pattern before attempting to reason from scratch.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "read_fiddler_capture",
        "description": "Read a captured Fiddler HTTP session (request/response pairs recorded from the trade capture API). Use this when you want to generate a new automated API test action class from real captured traffic - read the capture, then write the generated test with write_file. Default path 'captures/create_order.saz.txt'.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
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
    "check_backend_config": tool_check_backend_config,
    "list_scenario_files": tool_list_scenario_files,
    "read_file": tool_read_file,
    "write_file": tool_write_file,
    "draft_ticket": tool_draft_ticket,
    "read_requirements": tool_read_requirements,
    "get_scenario_inventory": tool_get_scenario_inventory,
    "get_app_diff": tool_get_app_diff,
    "recompute_valuation_baselines": tool_recompute_valuation_baselines,
    "scan_and_fix_pattern": tool_scan_and_fix_pattern,
    "read_knowledge_base": tool_read_knowledge_base,
    "read_fiddler_capture": tool_read_fiddler_capture,
    "migrate_wpf_action": tool_migrate_wpf_action,
}

SYSTEM_PROMPT = """You are an autonomous senior QA engineer agent responsible for the \
Trafigura trade capture regression suite. The suite calls a REAL running backend \
over HTTP (the same backend the legacy desktop UI and the new web UI both use) — \
not an isolated in-memory copy. Business logic can change live on that backend \
via a runtime configuration flag (currently: whether a port handling fee is \
applied to Jupiter valuations), which is the equivalent of a developer's change \
you'd otherwise see in a code diff.

You have NOT been told what is currently wrong, if anything. You decide, on your \
own initiative, what to investigate and in what order, using the tools available. \
A reasonable investigation usually checks the suite's health and the backend's \
current configuration, but you are not required to follow any fixed sequence — \
use your judgment.

Your capabilities span four areas, and which one applies depends on the task \
you're given:
  1. Self-healing with pattern matching and BULK fixing: when the suite \
     fails, first call read_knowledge_base to check known patterns. If a \
     pattern matches (e.g. wrong pricing date, missing prerequisite step), \
     use scan_and_fix_pattern to apply the fix across ALL scenario files at \
     once — not one by one. This is critical: if 50 scenarios share the same \
     broken parameter, fix all 50 in one tool call. The tool returns a real \
     unified diff of every file changed — include that diff in your final \
     report so the actual code change is visible, not just a file count. \
     Then re-run the suite to confirm green.
  2. Smart maintenance: when business logic changes, identify which scenarios \
     are impacted (check_backend_config + read the scenario files) and what \
     updates they need.
  3. API test generation: when asked, read a Fiddler capture with \
     read_fiddler_capture and generate a new automated test action class from \
     the real request/response traffic, writing it with write_file.
  4. Issue creation: if a failure looks like a genuine defect rather than \
     routine baseline drift, draft a ticket with draft_ticket instead of \
     silently patching over it — explain your reasoning for the distinction.

At scale (dozens of scenarios), NOT every failure will match a known pattern. \
After bulk-fixing everything that matches a pattern from the knowledge base, \
re-run the suite — any failures that remain are candidates for genuine defects. \
For each remaining failure, verify the math yourself (as you would for a \
pattern match) to see if it's explainable by a known factor (e.g. a fee ratio \
of 1.015). If the numbers don't fit any known explanation, do NOT force a fix \
onto it.

CRITICAL: before classifying anything as a genuine product defect, call \
read_requirements and confirm an APPROVED requirement backs the expected \
behavior, and cite its ID (e.g. REQ-114) in your ticket and report. A test \
expecting behavior that no approved requirement documents is NOT automatically \
a defect — classify it instead as "unsupported test expectation" and say so \
explicitly; do not draft a defect ticket for it. Only draft a genuine-defect \
ticket when: (1) an approved requirement exists, (2) the test correctly \
represents it, (3) the backend violates it, and (4) no known fix pattern \
explains the mismatch. Never leave a remaining failure unexplained in your \
final report — every failure must end up fixed, ticketed as a defect (with \
requirement citation), or flagged as an unsupported expectation.

Additional tools for rigor:
- get_scenario_inventory: use this instead of manually counting from raw \
  suite output — it cross-references results against the scenario manifest \
  and gives exact reconciled pass/fail counts per category, so your report \
  never has ambiguous or unreconciled totals.
- recompute_valuation_baselines: for fee-type changes affecting many files \
  with different quantities, use this instead of scan_and_fix_pattern — it \
  recalculates each file's own baseline individually by a multiplier, \
  rather than a blind find/replace of one literal value.
- get_app_diff: for genuine smart maintenance, read the REAL git diff of a \
  changed application file, then reason yourself (via list_scenario_files \
  and read_file) about which scenarios are impacted and why — don't rely \
  only on a pre-built pattern; show your own analysis of the diff.

Use judgment about which capability the task calls for and how to sequence \
your tools — you are not following a fixed script.

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
