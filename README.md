# Clara — Clinic Admin Agent

A modern AI assistant for clinic front-desk workflows. Clara helps with:
- checking doctor availability
- booking and cancelling appointments
- answering common clinic questions (hours, location, insurance, policy)
- voice-enabled booking when running the web interface

Clara is built with the Anthropic API and a small SQLite database. The agent
uses tool-based reasoning to map natural language to deterministic booking
and lookup operations without providing medical diagnosis or clinical advice.

## Key features

- CLI chat experience via `main.py`
- Web UI with chat, quick actions, and voice booking via `web.py`
- Appointment management and availability checking
- FAQ-style clinic support queries
- SQLite-backed persistence in `data/clinic.db`

## Repository structure

```
.
├── .env.example          # example configuration file for API key
├── README.md
├── main.py               # CLI entrypoint
├── web.py                # Flask web application
├── requirements.txt
├── data/                 # local SQLite database file
├── src/
│   └── healthagent/
│       ├── __init__.py
│       ├── agent.py      # Claude tool-use orchestration and prompt handling
│       ├── database.py   # SQLite schema, connection, and seed/init logic
│       └── tools.py      # booking, availability, cancellation, and FAQ helpers
├── templates/
│   └── index.html        # web UI for chat and voice booking
└── tests/
    └── test_tools.py     # unit tests for booking and helper logic
```

## Prerequisites

- Python 3.11+ (recommended)
- `ANTHROPIC_API_KEY`

## Setup

```bash
cd /Users/MuhammadUsman/Documents/GitHub/Health
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Then open `.env` and set:

```env
ANTHROPIC_API_KEY=your-api-key-here
```

## Run the CLI

```bash
python main.py
```

The CLI accepts natural language requests and responds with booking,
availability, and FAQ results.

## Run the web app

```bash
python web.py
```

Then visit:

```text
http://127.0.0.1:5000
```

The web interface includes quick action buttons, a chat conversation panel, and
voice-first booking controls.

## Testing

```bash
pytest tests/ -v
```

The tests exercise the core booking and scheduling helpers without requiring an
Anthropic API key.

## Architecture overview

- `src/healthagent/agent.py` constructs the conversation flow and tool schema.
- `src/healthagent/tools.py` contains the concrete booking, availability, and
  FAQ functions the agent invokes.
- `src/healthagent/database.py` manages SQLite persistence and initial seed data.
- `main.py` starts a terminal chat loop.
- `web.py` starts a Flask app and serves `templates/index.html`.

## Deployment

For a production-ready deployment, consider:
- securing environment variables and removing any secrets from source control
- using a production WSGI server such as Gunicorn or uWSGI for `web.py`
- adding authentication and authorization before exposing the app externally
- moving SQLite to a managed database if you need concurrency and durability
- enforcing HTTPS and appropriate security headers

## Notes

- This project is scoped to clinic administrative workflows only.
- Clara is not a diagnostic tool and should not provide clinical advice.
- For production deployment, add authentication, secure API handling, and
  compliance controls.
