"""BONUS - Action migration: reads a real legacy WPF UI action (C#, UIAutomation)
and generates the equivalent Playwright TypeScript action for the new React-based
web UI. Same business logic and controls, different UI technology - exactly the
migration path discussed for the WPF -> web UI transition."""
import os
from dotenv import load_dotenv, find_dotenv
from anthropic import Anthropic

load_dotenv(find_dotenv())
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

with open("legacy_wpf_actions/ConfirmTradeAction.cs") as f:
    wpf_action = f.read()

print("Migrating legacy WPF action to Playwright (React web UI)...")

resp = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1200,
    messages=[{"role": "user", "content": f"""You are an AI tool that migrates legacy
WPF desktop UI test actions (C#, UIAutomation) to Playwright TypeScript actions for
an equivalent React web UI. The business logic and control purpose stay identical -
only the UI technology changes. Assume the React app exposes similar controls via
data-testid attributes (txtTradeId -> trade-id-input, btnConfirmTrade -> confirm-trade-button,
lblTradeStatus -> trade-status-label), following standard React testing conventions.

Return a complete, runnable Playwright TypeScript action function with the same
business assertion (trade status must be CONFIRMED after the action runs).

LEGACY WPF ACTION:
{wpf_action}"""}]
)
print(resp.content[0].text)
