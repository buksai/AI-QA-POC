"""USE CASE 3 - API test generation: reads a captured request/response
(Fiddler-style) and generates a REAL runnable pytest file, then you run it
against the live app."""
import os
import re
from dotenv import load_dotenv, find_dotenv
from anthropic import Anthropic

load_dotenv(find_dotenv())
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

with open("captures/checkout_capture.txt") as f:
    capture = f.read()

with open("shop_api.py") as f:
    api_src = f.read()

with open("tests/test_shop_api.py") as f:
    style_ref = f.read()

print("Generating a runnable pytest file from the captured traffic...")

resp = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1500,
    messages=[{"role": "user", "content": f"""You are an AI tool that generates
automated API tests from captured HTTP traffic. Generate a pytest test file that
tests the captured endpoint using Flask's test client, exactly in the style of the
reference test file. Cover: status code, response fields, and one negative case
(empty items list should give itemCount 0 and total 0.0).

Return ONLY the complete Python file content. No markdown fences, no explanation.

CAPTURED TRAFFIC (Fiddler-style):
{capture}

APPLICATION SOURCE (for accurate imports and behavior):
{api_src}

REFERENCE TEST FILE (match this style):
{style_ref}"""}]
)

code = resp.content[0].text.strip()
code = re.sub(r"^```(?:python)?\s*", "", code)
code = re.sub(r"\s*```$", "", code)

path = "tests/test_generated_from_capture.py"
with open(path, "w") as f:
    f.write(code + "\n")

print(f">> Generated: {path}")
print(">> Now run it:  python3 -m pytest tests/test_generated_from_capture.py -q")
