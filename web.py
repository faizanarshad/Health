"""Flask backend for the Clara dashboard.

Serves the dashboard UI (templates/dashboard.html) and a small JSON API that
the dashboard's JavaScript calls to render the Schedule, Messages, Patients,
Doctors, and Settings pages, and to talk to the Clara agent.

Run with:  python web.py   (then open http://localhost:5000)
Requires ANTHROPIC_API_KEY for the chat endpoints; the read-only dashboard
pages work without it.
"""
from __future__ import annotations

import os
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from src.healthagent import database as db
from src.healthagent import tools
from src.healthagent.agent import ClinicAgent

load_dotenv()
db.init_db()

app = Flask(__name__)

# Single in-memory conversation for the front-desk "Ask Clara" console
# (Schedule page). Resets when the server restarts.
_console_agent: ClinicAgent | None = None


def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _require_api_key():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return jsonify(
            {
                "error": "ANTHROPIC_API_KEY is not set. Add it to your .env file to enable Clara's chat.",
            }
        ), 503
    return None


@app.route("/")
def index():
    return render_template("dashboard.html", clinic_name=db.CLINIC_NAME)


@app.route("/api/clinic")
def api_clinic():
    return jsonify({"name": db.CLINIC_NAME, "status": "Clara is online — handling front desk"})


@app.route("/api/doctors")
def api_doctors():
    date = request.args.get("date", _today())
    return jsonify(tools.doctor_directory(date))


@app.route("/api/patients")
def api_patients():
    return jsonify(tools.list_patients())


@app.route("/api/schedule")
def api_schedule():
    date = request.args.get("date", _today())
    return jsonify(tools.schedule_for_date(date))


@app.route("/api/settings")
def api_settings():
    return jsonify(tools.settings_snapshot())


@app.route("/api/messages/threads")
def api_threads():
    return jsonify(tools.list_threads())


@app.route("/api/messages/threads/<int:thread_id>")
def api_thread_detail(thread_id: int):
    thread = tools.get_thread(thread_id)
    if thread is None:
        return jsonify({"error": f"No thread with id {thread_id}"}), 404
    return jsonify(thread)


@app.route("/api/messages/threads/<int:thread_id>/reply", methods=["POST"])
def api_thread_reply(thread_id: int):
    err = _require_api_key()
    if err:
        return err

    thread = tools.get_thread(thread_id)
    if thread is None:
        return jsonify({"error": f"No thread with id {thread_id}"}), 404

    body = request.get_json(silent=True) or {}
    text = (body.get("text") or "").strip()
    if not text:
        return jsonify({"error": "Missing 'text' in request body."}), 400

    tools.add_thread_message(thread_id, "patient", text)

    # Rebuild a lightweight conversation from the thread history so Clara has
    # context, then get her reply for the new message.
    history = [
        {"role": "user" if m["sender"] == "patient" else "assistant", "content": m["text"]}
        for m in thread["messages"]
    ]
    agent = ClinicAgent(messages=history)
    result = agent.send(text)

    tool_line = result["tool_calls"][0]["trace"] if result["tool_calls"] else None
    saved = tools.add_thread_message(thread_id, "clara", result["reply"], tool_line)

    return jsonify({"reply": result["reply"], "tool_calls": result["tool_calls"], "message": saved})


@app.route("/api/chat", methods=["POST"])
def api_chat():
    err = _require_api_key()
    if err:
        return err

    global _console_agent
    body = request.get_json(silent=True) or {}
    text = (body.get("text") or "").strip()
    if not text:
        return jsonify({"error": "Missing 'text' in request body."}), 400

    if _console_agent is None:
        _console_agent = ClinicAgent()

    result = _console_agent.send(text)
    return jsonify(result)


@app.route("/api/chat/reset", methods=["POST"])
def api_chat_reset():
    global _console_agent
    _console_agent = None
    return jsonify({"status": "reset"})


@app.route("/api/book", methods=["POST"])
def api_book():
    """Direct booking endpoint used by the dashboard/clients.

    Expects JSON: { patient_name, doctor_name, date, time, reason }
    Returns the result of `tools.book_appointment`.
    """
    err = _require_api_key()
    if err:
        return err

    body = request.get_json(silent=True) or {}
    patient_name = (body.get("patient_name") or "").strip()
    doctor_name = (body.get("doctor_name") or "").strip()
    date = (body.get("date") or "").strip()
    time = (body.get("time") or "").strip()
    reason = (body.get("reason") or "").strip()

    if not (patient_name and doctor_name and date and time):
        return jsonify({"error": "Missing required fields: patient_name, doctor_name, date, time"}), 400

    try:
        result = tools.book_appointment(patient_name, doctor_name, date, time, reason)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

    return jsonify(result)


@app.route("/api/quick_book", methods=["POST"])
def api_quick_book():
    """Minimal booking endpoint for fast UI flows.

    Expects JSON: { patient_name, doctor_name, date, time, reason }
    Returns concise confirmation or error.
    """
    body = request.get_json(silent=True) or {}
    patient_name = (body.get("patient_name") or "").strip()
    doctor_name = (body.get("doctor_name") or "").strip()
    date = (body.get("date") or "").strip()
    time = (body.get("time") or "").strip()
    reason = (body.get("reason") or "").strip()

    if not (patient_name and doctor_name and date and time):
        return jsonify({"error": "Missing required fields: patient_name, doctor_name, date, time"}), 400

    try:
        result = tools.book_appointment(patient_name, doctor_name, date, time, reason)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

    if "error" in result:
        return jsonify(result), 400

    message = f"Booked: {patient_name} with {doctor_name} on {date} at {time}."
    return jsonify({"status": "ok", "message": message, "appointment": result})


if __name__ == "__main__":
    # Allow overriding host/port via environment (useful when port 5000
    # is occupied by system services like AirPlay). Example:
    # PORT=5001 HOST=127.0.0.1 python web.py
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5000"))
    app.run(debug=True, host=host, port=port)
