"""Live-streaming web dashboard for the autonomous QA agent. Runs the real
agent loop and streams every reasoning step, tool call, and tool result to
the browser as it happens via Server-Sent Events — you watch the agent think,
not just see a final answer."""
import json
import queue
import subprocess
import threading
from flask import Flask, Response, render_template, request

import qa_agent

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("dashboard.html")


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


@app.route("/api/reset", methods=["POST"])
def reset():
    log = subprocess.run(
        ["git", "log", "--oneline", "--reverse"], cwd=qa_agent.WORKSPACE,
        capture_output=True, text=True
    ).stdout.strip().splitlines()
    if not log:
        return {"output": "No commits found in workspace."}
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


if __name__ == "__main__":
    app.run(port=5101, debug=True, threaded=True)
