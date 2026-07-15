"""Web UI for the Trafigura-specific POC. Same real engine underneath -
real javac compile, real test runs, real git commits, real AI calls -
triggered by buttons instead of terminal commands. Port 5003."""
import subprocess
from flask import Flask, render_template, jsonify

app = Flask(__name__)


def sh(cmd, input_text=None, timeout=180):
    r = subprocess.run(cmd, capture_output=True, text=True, input=input_text, timeout=timeout)
    return (r.stdout or "") + (r.stderr or ""), r.returncode


def compile_and_run():
    subprocess.run(["bash", "-c", "find src -name '*.java' > sources.txt"])
    out, rc = sh(["javac", "-d", "out", "@sources.txt", "TestRunner.java"])
    if rc != 0:
        return "COMPILE ERROR:\n" + out
    out2, _ = sh(["java", "-cp", "out:.", "TestRunner"])
    return out + out2


@app.route("/")
def home():
    return render_template("trafigura_scenario.html")


@app.route("/api/step/baseline", methods=["POST"])
def baseline():
    return jsonify({"output": compile_and_run()})


@app.route("/api/step/dev_change", methods=["POST"])
def dev_change():
    out, _ = sh(["python3", "simulate_dev_change.py"])
    return jsonify({"output": out})


@app.route("/api/step/impact", methods=["POST"])
def impact():
    out, _ = sh(["python3", "ai_qa/impact.py"])
    return jsonify({"output": out})


@app.route("/api/step/rerun", methods=["POST"])
def rerun():
    return jsonify({"output": compile_and_run()})


@app.route("/api/step/ticket", methods=["POST"])
def ticket():
    out, _ = sh(["python3", "ai_qa/make_ticket.py"])
    return jsonify({"output": out})


@app.route("/api/step/heal", methods=["POST"])
def heal():
    # auto-approves the proposed fix (sends 'y' to the CLI prompt)
    out, _ = sh(["python3", "ai_qa/heal.py"], input_text="y\n")
    return jsonify({"output": out})


@app.route("/api/step/migrate", methods=["POST"])
def migrate():
    out, _ = sh(["python3", "ai_qa/migrate_wpf_action.py"])
    return jsonify({"output": out})


@app.route("/api/step/reset", methods=["POST"])
def reset():
    out, _ = sh(["git", "reset", "--hard", "origin/main"])
    return jsonify({"output": out})


if __name__ == "__main__":
    app.run(port=5003, debug=True)
