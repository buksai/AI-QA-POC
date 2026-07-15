"""USE CASE 4 - Agent issue creation: runs the REAL test suite; if there are
failures, drafts a bug ticket and writes it as a real file into tickets/."""
import os
import subprocess
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
from anthropic import Anthropic

load_dotenv(find_dotenv())
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

subprocess.run(["find", "src", "-name", "*.java"], stdout=open("sources.txt", "w"))
subprocess.run(["javac", "-d", "out", "@sources.txt", "TestRunner.java"], capture_output=True, text=True)
r = subprocess.run(["java", "-cp", "out:.", "TestRunner"], capture_output=True, text=True)
out = r.stdout + r.stderr

if r.returncode == 0:
    print("Suite is green - no ticket needed.")
    raise SystemExit(0)

print("Failures detected - drafting ticket from real test output...")

resp = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1000,
    messages=[{"role": "user", "content": f"""You are an AI agent that drafts bug
tickets from automated regression test execution results in a commodity trading
test framework. Draft ONE consolidated, ready-to-file ticket in markdown with:
Title, Severity, Steps to reproduce, Expected, Actual, Environment, Note on
whether this looks like a genuine defect or a stale baseline needing update.
Real test runner output:

{out}"""}]
)

os.makedirs("tickets", exist_ok=True)
name = "tickets/TICKET-" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".md"
with open(name, "w") as f:
    f.write(resp.content[0].text)

print(f">> Ticket written: {name}")
print("-" * 70)
print(resp.content[0].text[:800])
