"""Web UI wrapper around the real scenario. Same engine as the CLI scripts —
real pytest runs, real git commits, real AI calls — just triggered by buttons
and streamed to the browser instead of the terminal."""
import subprocess
from flask import Flask, render_template, jsonify

app = Flask(__name__)


def run(cmd, input_text=None):
    r = subprocess.run(
        cmd, capture_output=True, text=True, input=input_text, timeout=120
    )
    return (r.stdout or "") + (r.stderr or "")


@app.route("/")
def home():
    return render_template("real_scenario.html")


@app.route("/api/step/baseline", methods=["POST"])
def baseline():
    out = run(["python3", "-m", "pytest", "tests/", "-q"])
    return jsonify({"output": out})


@app.route("/api/step/gen_test", methods=["POST"])
def gen_test():
    out = run(["python3", "ai_qa/gen_api_test.py"])
    out += "\n\n--- running the generated test ---\n\n"
    out += run(["python3", "-m", "pytest", "tests/test_generated_from_capture.py", "-q"])
    return jsonify({"output": out})


@app.route("/api/step/dev_change", methods=["POST"])
def dev_change():
    out = run(["python3", "simulate_dev_change.py"])
    return jsonify({"output": out})


@app.route("/api/step/impact", methods=["POST"])
def impact():
    out = run(["python3", "ai_qa/impact.py"])
    return jsonify({"output": out})


@app.route("/api/step/rerun", methods=["POST"])
def rerun():
    out = run(["python3", "-m", "pytest", "tests/", "-q", "--tb=short"])
    return jsonify({"output": out})


@app.route("/api/step/ticket", methods=["POST"])
def ticket():
    out = run(["python3", "ai_qa/make_ticket.py"])
    return jsonify({"output": out})


@app.route("/api/step/heal", methods=["POST"])
def heal():
    # auto-approve the fix for the web demo (types "y" for the CLI prompt)
    out = run(["python3", "ai_qa/heal.py"], input_text="y\n")
    return jsonify({"output": out})


@app.route("/api/step/reset", methods=["POST"])
def reset():
    out = run(["git", "reset", "--hard", "origin/main"])
    return jsonify({"output": out})


if __name__ == "__main__":
    app.run(port=5002, debug=True)
