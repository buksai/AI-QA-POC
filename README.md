# AI in QA Automation — POC

Small working prototype demonstrating 3 AI-assisted QA use cases:

1. Self-healing test analysis
2. Auto ticket drafting from test failures
3. API test class generation from captured HTTP traffic (Fiddler-style)

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the root with:
```
ANTHROPIC_API_KEY=your_key_here
```

## Run

```bash
python app.py
```

Then open http://localhost:5000
