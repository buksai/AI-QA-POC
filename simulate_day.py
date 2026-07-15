import os
import time
from datetime import datetime
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def ask(prompt):
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text


def typewriter(text, delay=0.01):
    print(text)
    time.sleep(delay)


def divider():
    print("\n" + "-" * 70 + "\n")


def timestamp():
    return datetime.now().strftime("%H:%M:%S")


def scene(title):
    divider()
    print(f"[{timestamp()}]  {title}")
    divider()
    time.sleep(0.5)


# ============================================================
# SCENE 1 — Nightly regression run kicks off
# ============================================================
scene("NIGHTLY REGRESSION RUN — dxc-checkout-suite")
print("Running 500 automated test scenarios...")
time.sleep(1)
print("...")
time.sleep(0.5)
print("496 PASSED")
print("4 FAILED\n")
print("Failed tests:")
print("  - test_checkout_submit")
print("  - test_login_with_valid_credentials")
print("  - test_add_to_cart_api")
print("  - test_search_autocomplete")
time.sleep(1)


# ============================================================
# SCENE 2 — Use Case 1: Self-healing analysis on failure #1
# ============================================================
scene("USE CASE 1 — Self-Healing Analysis: test_checkout_submit")

failure_log = """
AssertionError: Element not found: //button[@id='submit-btn-old']
Test: test_checkout_submit
Last passed: 3 days ago
Recent commit: "renamed submit button id to submit-btn-v2 for A/B test"
"""
print("Feeding failure log + recent commit history to AI agent...\n")
time.sleep(1)

result = ask(f"""You are an AI QA assistant doing self-healing test analysis.
Given this test failure, identify the root cause and propose a concrete code fix.
Be concise. Use headers: Root cause / Proposed fix / Confidence.

{failure_log}""")
print(result)
print("\n>> Status: Fix proposed. Awaiting human approval before merge.")
time.sleep(1)


# ============================================================
# SCENE 3 — Use Case 2: Smart impact analysis from a code change
# ============================================================
scene("USE CASE 2 — Smart Test Maintenance: recent code change impact")

code_change = """
Recent PR #482: "Refactored checkout API response schema — added 'discountApplied' field,
removed deprecated 'legacyTotal' field, changed 'status' enum values from
[pending, complete] to [PENDING, COMPLETE, FAILED]"

Affected modules: checkout-service (backend), checkout-summary (frontend component)
"""
print("Analyzing code diff for potential impact on test suite...\n")
time.sleep(1)

result = ask(f"""You are an AI QA assistant doing impact analysis for a code change.
Given this PR description, identify which categories of automated test scenarios
are likely impacted and why. Be concise, use a short bullet list, then a one-line
recommendation on priority.

{code_change}""")
print(result)
time.sleep(1)


# ============================================================
# SCENE 4 — Use Case 3: API test generation from captured traffic
# ============================================================
scene("USE CASE 3 — API Test Generation: new add-to-cart endpoint")

captured_traffic = """
POST /api/v2/cart/add
Request body: {"userId": 4821, "sku": "A100", "qty": 2}
Response 200: {"cartId": "CART-5521", "itemCount": 2, "subtotal": 39.98}
"""
print("Captured traffic (Fiddler-style) received. Generating test class...\n")
time.sleep(1)

result = ask(f"""You are an AI tool that generates API automated test classes
from captured HTTP traffic. Given this request/response pair, generate a concise
Java RestAssured-style test class with request builder and key assertions.

{captured_traffic}""")
print(result)
time.sleep(1)


# ============================================================
# SCENE 5 — Use Case 4: Auto ticket drafting for a genuine bug
# ============================================================
scene("USE CASE 4 — Auto Ticket Drafting: test_login_with_valid_credentials")

failure_result = """
Test: test_login_with_valid_credentials
Status: FAILED
Expected: redirect to /dashboard
Actual: stayed on /login, error toast "Invalid session token"
Environment: staging, Chrome 126
Timestamp: 2026-07-15 09:12 UTC
"""
print("This failure looks like a real bug, not a broken test. Drafting ticket...\n")
time.sleep(1)

result = ask(f"""You are an AI agent that drafts bug tickets from test failure data.
Produce a ready-to-file ticket with: Title, Severity, Steps to reproduce,
Expected, Actual, Environment.

{failure_result}""")
print(result)
time.sleep(1)


# ============================================================
# SCENE 6 — Summary
# ============================================================
scene("END OF CYCLE SUMMARY")
print("4 failures processed automatically by AI:")
print("  1. Self-healing fix proposed  -> pending human approval")
print("  2. Impact analysis complete   -> 2 test categories flagged for review")
print("  3. New API test generated     -> ready for code review")
print("  4. Bug ticket drafted         -> ready to file in Jira")
print("\nHuman time saved tonight: estimated 2-3 hours of manual triage.")
divider()
