"""
Control Center — the single unified entry point for the whole V2 demo.

One Flask app, one port, three tabs:
  1. POC AI Engineer   — the autonomous agent, live-streaming its reasoning
  2. Trafigura Enterprise Legacy Demo — the legacy WPF-style desktop UI
  3. New System        — the new web UI (React migration target)

All three genuinely share ONE source of truth: the real Java backend running
on port 5100. Toggling the handling-fee business rule from the agent tab
immediately affects what the legacy and web UI tabs will show for any trade,
because they're all reading the same live server - not three disconnected demos.
"""
import json
import os
import queue
import subprocess
import sys
import threading

from flask import Flask, Response, render_template, request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agent"))
import qa_agent  # noqa: E402

V2_ROOT = os.path.join(os.path.dirname(__file__), "..")
BACKEND_DIR = os.path.join(V2_ROOT, "backend")

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("control_center.html")


# ----------------------------------------------------------------------
# Agent tab
# ----------------------------------------------------------------------

@app.route("/api/run-agent")
def run_agent_stream():
    task = request.args.get(
        "task",
        "Investigate the current state of the regression suite and fix anything "
        "that needs fixing. Report your findings and actions when done."
    )
    event_queue = queue.Queue()

    def on_event(kind, data):
        event_queue.put({"kind": kind, "data": data})

    def worker():
        try:
            qa_agent.run_agent(task, on_event=on_event)
        except Exception as e:
            event_queue.put({"kind": "error", "data": {"message": str(e)}})
        finally:
            event_queue.put({"kind": "__done__", "data": {}})

    threading.Thread(target=worker, daemon=True).start()

    def stream():
        while True:
            item = event_queue.get()
            if item["kind"] == "__done__":
                yield "event: done\ndata: {}\n\n"
                break
            yield f"data: {json.dumps(item)}\n\n"

    return Response(stream(), mimetype="text/event-stream")


@app.route("/api/reset-agent-workspace", methods=["POST"])
def reset_agent_workspace():
    # SAFETY: agent/workspace has no git repo of its own - it's tracked as
    # plain files inside the main repo. A full `git reset --hard` here would
    # blow away the ENTIRE repository back to its first commit, deleting
    # unrelated work like control_center/ itself. Every git operation below
    # is explicitly scoped to the workspace path only, via `-- <path>`, so it
    # can never touch anything outside this folder.
    repo_root = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], cwd=qa_agent.WORKSPACE,
        capture_output=True, text=True
    ).stdout.strip()
    rel_path = os.path.relpath(qa_agent.WORKSPACE, repo_root)

    restore = subprocess.run(
        ["git", "checkout", "HEAD", "--", rel_path],
        cwd=repo_root, capture_output=True, text=True
    )
    clean = subprocess.run(
        ["git", "clean", "-fd", "--", rel_path],
        cwd=repo_root, capture_output=True, text=True
    )
    files_output = (restore.stdout + restore.stderr + clean.stdout + clean.stderr).strip() or "Workspace files restored to last committed state."

    # Reset must also restore ALL THREE backend runtime toggles to their
    # healthy defaults - they're in-memory flags on the running Java
    # process, so resetting test files alone does not touch them.
    import urllib.request
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:5100/api/admin/reset-all",
            data=b'{}', headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            import json as _json
            status = _json.loads(resp.read())
        backend_output = f"Backend fully reset: {status}"
    except Exception as e:
        backend_output = f"Could not reset backend (is it running?): {e}"
    return {"output": files_output + "\n" + backend_output}


@app.route("/api/apply-dev-change", methods=["POST"])
def apply_dev_change():
    import urllib.request, json as _json
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:5100/api/admin/regression-event",
            data=b'{}', headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            status = _json.loads(resp.read())
        output = (
            ">> Ops shipped a bad release affecting Jupiter valuations:\n"
            f">>   - 1.5% port handling fee enabled: {status['handlingFeeEnabled']}\n"
            f">>   - Pricing data cutoff advanced to: {status['pricingDataAvailableFrom']}\n"
            f">>   - REQ-114 volume discount honored: {status['volumeDiscountEnabled']}\n"
            ">> This takes effect immediately for ALL callers: legacy UI, web UI, and agent tests.\n"
            ">> The regression suite is now stale for some scenarios, and genuinely violates\n"
            ">> REQ-114 for others."
        )
    except Exception as e:
        output = f"Could not reach backend (is it running?): {e}"
    return {"output": output}


@app.route("/api/backend-status")
def backend_status():
    return qa_agent.tool_check_backend_config({})


# ----------------------------------------------------------------------
# Static UI tabs — served from this same app/port so everything is genuinely
# "one localhost." Both call the Java backend on 5100 directly from the browser.
# ----------------------------------------------------------------------

@app.route("/legacy")
def legacy_ui():
    with open(os.path.join(V2_ROOT, "ui-legacy", "index.html")) as f:
        return f.read()


@app.route("/web")
def web_ui():
    with open(os.path.join(V2_ROOT, "ui-web", "index.html")) as f:
        return f.read()


if __name__ == "__main__":
    app.run(port=5099, debug=True, threaded=True)
