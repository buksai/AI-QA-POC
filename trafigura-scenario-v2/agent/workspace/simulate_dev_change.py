"""Simulates a developer/Ops enabling the port handling fee — but now as a
REAL runtime toggle on the LIVE backend (POST /api/admin/handling-fee),
not a source code edit. This is what makes the demo genuinely synchronized:
flipping this affects the legacy UI, the web UI, and the agent's HTTP-based
tests all at once, because they all read from the same running backend."""
import sys
import urllib.request
import json

BACKEND = "http://127.0.0.1:5100/api/admin/handling-fee"


def get_status():
    with urllib.request.urlopen(BACKEND) as resp:
        return json.loads(resp.read())["handlingFeeEnabled"]


def set_status(enabled):
    req = urllib.request.Request(
        BACKEND, data=json.dumps({"enabled": str(enabled).lower()}).encode(),
        headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())["handlingFeeEnabled"]


if __name__ == "__main__":
    try:
        current = get_status()
    except Exception as e:
        print(f"Could not reach backend at {BACKEND} - is it running on port 5100?")
        print(f"  ({e})")
        sys.exit(1)

    if current:
        print("Handling fee is already enabled. To reset: POST enabled=false, or use the dashboard's Reset button.")
        sys.exit(1)

    new_status = set_status(True)
    print(">> Ops requested a 1.5% port handling fee on Jupiter valuations (JIRA-4821).")
    print(f">> Backend runtime toggle flipped: handlingFeeEnabled = {new_status}")
    print(">> This takes effect immediately for ALL callers: legacy UI, web UI, and agent tests.")
    print(">> Baseline values in the regression suite are now stale.")
