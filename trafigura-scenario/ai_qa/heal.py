"""USE CASE 1 - Self-healing (priority use case). Runs the REAL Java test suite.
On failure, AI reads the real failure output + the real git diff of the system
change, and proposes a corrected scenario file (updated baseline). Shows a diff,
asks for human approval, applies it, recompiles, and re-runs until green."""
import os
import re
import subprocess
import difflib
from dotenv import load_dotenv, find_dotenv
from anthropic import Anthropic

load_dotenv(find_dotenv())
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SCENARIO_PATH = "src/scenarios/CopperConcentrateTradeScenario.java"
MAX_ROUNDS = 3


def compile_and_run():
    with open("sources.txt") as f:
        pass
    subprocess.run(["find", "src", "-name", "*.java"], stdout=open("sources.txt", "w"))
    compile_res = subprocess.run(
        ["javac", "-d", "out", "@sources.txt", "TestRunner.java"],
        capture_output=True, text=True
    )
    if compile_res.returncode != 0:
        return "COMPILE_ERROR", compile_res.stdout + compile_res.stderr
    run_res = subprocess.run(["java", "-cp", "out:.", "TestRunner"], capture_output=True, text=True)
    return run_res.returncode, run_res.stdout + run_res.stderr


def ask_for_fix(test_src, failure_output, diff):
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": f"""You are a self-healing test agent for a
Java-based trade capture test framework. The scenario file below is failing after a
recent change to the system under test (a commodity trading platform). Analyze the
real test output and the real git diff of the system change, then produce the
corrected scenario file with an updated baseline value that reflects the new
expected business behavior.

Return ONLY the complete corrected Java file content. No markdown fences, no explanation.

FAILING SCENARIO FILE ({SCENARIO_PATH}):
{test_src}

TEST RUNNER OUTPUT:
{failure_output}

RECENT SYSTEM CHANGE (git diff):
{diff}"""}]
    )
    fixed = resp.content[0].text.strip()
    fixed = re.sub(r"^```(?:java)?\s*", "", fixed)
    fixed = re.sub(r"\s*```$", "", fixed)
    return fixed + "\n"


code, out = compile_and_run()
if code == 0:
    print("Suite is green - nothing to heal.")
    raise SystemExit(0)

print("=" * 70)
print("TEST RUN FAILED - starting self-healing analysis")
print("=" * 70)
print(out)

diff = subprocess.run(
    ["git", "diff", "HEAD~1", "--", "src/system/"],
    capture_output=True, text=True
).stdout[:6000]

for round_no in range(1, MAX_ROUNDS + 1):
    print(f"\n[Round {round_no}] Healing: {SCENARIO_PATH}")

    with open(SCENARIO_PATH) as f:
        original = f.read()

    fixed = ask_for_fix(original, out, diff)

    print("\nProposed fix (diff):")
    print("-" * 70)
    for line in difflib.unified_diff(
        original.splitlines(), fixed.splitlines(),
        fromfile=SCENARIO_PATH + " (current)",
        tofile=SCENARIO_PATH + " (proposed)", lineterm=""
    ):
        print(line)
    print("-" * 70)

    answer = input("\nApply this fix? [y/N] ").strip().lower()
    if answer != "y":
        print("Fix rejected by human reviewer. Stopping.")
        raise SystemExit(0)

    with open(SCENARIO_PATH, "w") as f:
        f.write(fixed)
    print(f">> Fix applied to {SCENARIO_PATH}. Recompiling and re-running...")

    code, out = compile_and_run()
    if code == 0:
        print("\n" + "=" * 70)
        print("SELF-HEALED: test suite is GREEN again.")
        print("=" * 70)
        raise SystemExit(0)
    else:
        print(out)

print("\nSuite still failing after max healing rounds - flagging for human review.")
