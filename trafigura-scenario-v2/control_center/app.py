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
    log = subprocess.run(
        ["git", "log", "--oneline", "--reverse"], cwd=qa_agent.WORKSPACE,
        capture_output=True, text=True
    ).stdout.strip().splitlines()
    if not log:
        return {"output": "No commits found in agent workspace."}
    first_commit = log[0].split()[0]
    r = subprocess.run(["git", "reset", "--hard", first_commit], cwd=qa_agent.WORKSPACE,
                       capture_output=True, text=True)
    return {"output": r.stdout + r.stderr}


@app.route("/api/apply-dev-change", methods=["POST"])
def apply_dev_change():
    r = subprocess.run(
        ["python3", "simulate_dev_change.py"], cwd=qa_agent.WORKSPACE,
        capture_output=True, text=True
    )
    return {"output": r.stdout + r.stderr}


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
