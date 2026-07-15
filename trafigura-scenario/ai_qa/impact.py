"""USE CASE 2 - Smart test maintenance: reads the REAL git diff of the last
commit to the system under test and asks AI which scenarios are impacted and
what updates they will need - before any test has even run."""
import os
import subprocess
from dotenv import load_dotenv, find_dotenv
from anthropic import Anthropic

load_dotenv(find_dotenv())
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

diff = subprocess.run(
    ["git", "diff", "HEAD~1", "--", "src/system/"],
    capture_output=True, text=True
).stdout[:6000]

if not diff.strip():
    print("No system changes found in the last commit.")
    raise SystemExit(0)

scenario_files = subprocess.run(
    ["git", "ls-files", "src/scenarios/"], capture_output=True, text=True
).stdout

print("=" * 70)
print("IMPACT ANALYSIS - analyzing real git diff of last commit to system/")
print("=" * 70)

resp = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=800,
    messages=[{"role": "user", "content": f"""You are an AI QA assistant doing impact
analysis for a Java-based trade capture test framework (commodity trading domain).
Below is a REAL git diff of a change to the system under test, and the list of
automated regression scenario files. Identify which scenarios are impacted and why,
and what updates they will need. Be concise: bullet list + one-line priority
recommendation.

GIT DIFF:
{diff}

SCENARIO FILES:
{scenario_files}"""}]
)
print(resp.content[0].text)
