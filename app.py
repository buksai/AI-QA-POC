import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
app = Flask(__name__)


def ask(prompt):
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/heal", methods=["POST"])
def heal():
    failure_log = request.json.get("input", "")
    prompt = f"""You are an AI QA assistant doing self-healing test analysis.
Given this test failure, identify the root cause and propose a concrete
code fix for the test (e.g. updated selector). Be concise, use headers:
Root cause / Proposed fix / Confidence.

{failure_log}"""
    return jsonify({"result": ask(prompt)})


@app.route("/api/ticket", methods=["POST"])
def ticket():
    failure_result = request.json.get("input", "")
    prompt = f"""You are an AI agent that drafts bug tickets from test failure data.
Produce a ready-to-file ticket with: Title, Severity, Steps to reproduce,
Expected, Actual, Environment.

{failure_result}"""
    return jsonify({"result": ask(prompt)})


@app.route("/api/apitest", methods=["POST"])
def apitest():
    captured_traffic = request.json.get("input", "")
    prompt = f"""You are an AI tool that generates API automated test classes
from captured HTTP traffic (like a Fiddler session). Given this request/response
pair, generate a concise Java RestAssured-style test class with request builder
and key assertions.

{captured_traffic}"""
    return jsonify({"result": ask(prompt)})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
