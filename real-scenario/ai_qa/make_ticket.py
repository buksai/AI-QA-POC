"""USE CASE 4 - Agent issue creation: runs the REAL suite; if there are failures,
drafts a bug ticket and writes it as a real file into tickets/."""
import os
import subprocess
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
from anthropic import Anthropic

load_dotenv(find_dotenv())
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

r = subprocess.run(["python3", "-m", "pytest", "tests/", "-q", "--tb=short"],
                   capture_output=True, text=True)
out = (r.stdout + r.stderr)[-5000:]

if r.returncode == 0:
    print("Suite is green - no ticket needed.")
    raise SystemExit(0)

print("Failures detected - drafting ticket from real test output...")

resp = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1000,
    messages=[{"role": "user", "content": f"""You are an AI agent that drafts bug
tickets from automated test execution results. Draft ONE consolidated, ready-to-file
ticket in markdown with: Title, Severity, Steps to reproduce, Expected, Actual,
Environment, Attachments note. Real pytest output:

{out}"""}]
)

os.makedirs("tickets", exist_ok=True)
name = "tickets/TICKET-" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".md"
with open(name, "w") as f:
    f.write(resp.content[0].text)

print(f">> Ticket written: {name}")
print("-" * 70)
print(resp.content[0].text[:800])
