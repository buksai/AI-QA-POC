"""USE CASE 1 - Self-healing: runs the REAL test suite; on failure, AI reads the
real pytest output + the real code diff, produces a corrected test file, shows you
the diff, and (after your approval) APPLIES it and re-runs until green."""
import os
import re
import difflib
import subprocess
from dotenv import load_dotenv, find_dotenv
from anthropic import Anthropic

load_dotenv(find_dotenv())
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

MAX_ROUNDS = 3


def run_tests():
    r = subprocess.run(["python3", "-m", "pytest", "tests/", "-q", "--tb=short"],
                       capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr)[-5000:]


def ask_for_fix(test_path, test_src, pytest_out, diff):
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": f"""You are a self-healing test agent.
The automated test file below is failing after a recent code change. Analyze the real
pytest output and the git diff of the change, and produce the corrected test file.

Return ONLY the complete corrected Python file content. No markdown fences, no explanation.

FAILING TEST FILE ({test_path}):
{test_src}

PYTEST OUTPUT:
{pytest_out}

RECENT CODE CHANGE (git diff):
{diff}"""}]
    )
    fixed = resp.content[0].text.strip()
    fixed = re.sub(r"^```(?:python)?\s*", "", fixed)
    fixed = re.sub(r"\s*```$", "", fixed)
    return fixed + "\n"


code, out = run_tests()
if code == 0:
    print("Suite is green - nothing to heal.")
    raise SystemExit(0)

print("=" * 70)
print("TEST RUN FAILED - starting self-healing analysis")
print("=" * 70)
print(out)

diff = subprocess.run(["git", "diff", "HEAD~1", "--", "."],
                      capture_output=True, text=True).stdout[:6000]

for round_no in range(1, MAX_ROUNDS + 1):
    failing = sorted(set(re.findall(r"(tests/\S+\.py)", out)))
    if not failing:
        print("Could not identify failing test files from output.")
        break

    target = failing[0]
    print(f"\n[Round {round_no}] Healing: {target}")

    with open(target) as f:
        original = f.read()

    fixed = ask_for_fix(target, original, out, diff)

    print("\nProposed fix (diff):")
    print("-" * 70)
    for line in difflib.unified_diff(original.splitlines(), fixed.splitlines(),
                                     fromfile=target + " (current)",
                                     tofile=target + " (proposed)", lineterm=""):
        print(line)
    print("-" * 70)

    answer = input("\nApply this fix? [y/N] ").strip().lower()
    if answer != "y":
        print("Fix rejected by human reviewer. Stopping.")
        raise SystemExit(0)

    with open(target, "w") as f:
        f.write(fixed)
    print(f">> Fix applied to {target}. Re-running suite...")

    code, out = run_tests()
    if code == 0:
        print("\n" + "=" * 70)
        print("SELF-HEALED: test suite is GREEN again.")
        print("=" * 70)
        raise SystemExit(0)

print("\nSuite still failing after max healing rounds - flagging for human review.")
print(out[-2000:])
