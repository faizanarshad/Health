# Clara — Clinic Admin Agent

An AI agent for clinic front-desk work: checking doctor availability, booking
and cancelling appointments, and answering common questions (hours, location,
insurance, cancellation policy). Built with the Anthropic API (Claude) using
tool use, backed by a small SQLite database.

**Scope:** administrative/scheduling only. Clara does not diagnose, interpret
symptoms, or give medical advice — the system prompt enforces this, and she'll
redirect medical questions to a clinician or emergency services.

## Project structure

```
healthagent/
├── main.py                     # CLI chat loop
├── requirements.txt
├── .env.example
├── data/                       # SQLite DB lives here (gitignored)
└── src/healthagent/
    ├── database.py             # schema, connection, seed data
    ├── tools.py                # plain Python functions: booking, availability, FAQs
    ├── agent.py                # Claude tool-use loop wrapping tools.py
    └── __init__.py
└── tests/
    └── test_tools.py           # unit tests for tools.py (no API key needed)
```

## Setup

```bash
cd healthagent
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then add your ANTHROPIC_API_KEY
```

## Run

```bash
python main.py
```

Example session:

```
You: What doctors do you have?
Clara: We have Dr. Amara Chen (General Practice), Dr. Luis Ferreira (Pediatrics), ...

You: Book me with Dr. Chen next Monday at 10am, I'm Jane Doe
Clara: Confirming: Jane Doe with Dr. Amara Chen on 2026-07-13 at 10:00. Shall I book it?

You: yes
Clara: Booked! Appointment #1 confirmed for Jane Doe with Dr. Amara Chen on 2026-07-13 at 10:00.
```

## Tests

```bash
pytest tests/ -v
```

Tests cover the booking logic directly (double-booking prevention, invalid
times/dates, cancellation, FAQ lookup) and don't require an API key.

## How it works

`agent.py` defines a set of tools (`list_doctors`, `check_availability`,
`book_appointment`, `cancel_appointment`, `list_appointments`, `answer_faq`)
and hands them to the Claude Messages API. When the model decides it needs
data or needs to perform an action, it emits a `tool_use` block; `ClinicAgent`
executes the matching function from `tools.py` against the SQLite database in
`data/clinic.db` and returns the result, looping until Claude produces a
final natural-language reply.

## Extending

- Swap SQLite for Postgres by changing `database.py`'s connection layer.
- Add a `send_reminder` tool (e.g. email/SMS) — stub it first, wire a
  provider later.
- Add authentication/patient verification before exposing this over a
  real phone or web channel.
- If you want clinical features (symptom intake, triage), treat that as a
  separate, more carefully reviewed component — do not fold it into this
  admin agent's scope without clinical and compliance review (HIPAA, etc.).
