"""USE CASE 2 - Smart test maintenance: reads the REAL git diff of the last
commit and asks AI which test scenarios are impacted and what updates they need."""
import os
import subprocess
from dotenv import load_dotenv, find_dotenv
from anthropic import Anthropic

load_dotenv(find_dotenv())
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

diff = subprocess.run(
    ["git", "diff", "HEAD~1", "--", "."],
    capture_output=True, text=True
).stdout[:6000]

if not diff.strip():
    print("No code changes found in the last commit.")
    raise SystemExit(0)

tests = subprocess.run(["git", "ls-files", "tests/"], capture_output=True, text=True).stdout

print("=" * 70)
print("IMPACT ANALYSIS - analyzing real git diff of last commit")
print("=" * 70)

resp = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=800,
    messages=[{"role": "user", "content": f"""You are an AI QA assistant doing impact
analysis. Below is a REAL git diff of a code change to the system under test, and the
list of automated test files. Identify which test scenarios are impacted and why, and
what updates they will need. Be concise: bullet list + one-line priority recommendation.

GIT DIFF:
{diff}

TEST FILES:
{tests}"""}]
)
print(resp.content[0].text)
