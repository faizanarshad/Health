"""Business logic for the clinic admin agent.

Functions in this module fall into two groups:

1. Agent tools (`list_doctors`, `check_availability`, `book_appointment`,
   `cancel_appointment`, `list_appointments`, `answer_faq`) - plain,
   testable Python that `agent.py` exposes to Claude via tool use.
2. Dashboard query helpers (`list_patients`, `doctor_directory`,
   `schedule_for_date`, thread helpers) - read/write functions used
   directly by the web API layer (`web.py`), not by the model.

Scope note: this agent handles scheduling/admin tasks only. It does not
diagnose, triage, or give medical advice.
"""
from __future__ import annotations

from datetime import datetime

from . import database as db

FAQ = {
    "hours": "The clinic is open Monday-Friday, 8:00 AM to 6:00 PM, and Saturday 9:00 AM to 1:00 PM. Closed Sundays.",
    "location": "Ridgeview Family Clinic — front desk can share the exact address and directions.",
    "insurance": "We accept Blue Cross, UnitedHealthcare, Aetna, and Cigna. Please bring your insurance card to your first visit.",
    "cancellation": "Cancellations are free up to 24 hours before your appointment. Late cancellations incur a USD 5 fee; no-shows incur a USD 10 fee.",
    "new_patient": "New patients should arrive 15 minutes early to complete intake paperwork, or fill it out online beforehand.",
}


def _validate_date(date: str) -> None:
    try:
        parsed = datetime.strptime(date, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"Invalid date '{date}'. Use YYYY-MM-DD.") from exc
    if parsed.weekday() >= 5:
        raise ValueError(f"'{date}' is a weekend. The clinic is open Monday-Friday only.")


def _validate_time(time: str) -> None:
    if time not in db.CLINIC_HOURS:
        raise ValueError(
            f"'{time}' is not a valid slot. Clinic hours are 09:00-17:00 in 30-minute "
            f"increments (e.g. 09:00, 09:30, ... 16:30)."
        )


# ---------------------------------------------------------------------------
# Agent tools
# ---------------------------------------------------------------------------

def list_doctors() -> list[dict]:
    """Return all doctors and their specialties."""
    with db.get_connection() as conn:
        rows = conn.execute("SELECT name, specialty FROM doctors ORDER BY name").fetchall()
    return [dict(r) for r in rows]


def check_availability(doctor_name: str, date: str) -> dict:
    """List open time slots for a doctor on a given date (YYYY-MM-DD)."""
    _validate_date(date)
    with db.get_connection() as conn:
        doctor = conn.execute(
            "SELECT name FROM doctors WHERE name = ?", (doctor_name,)
        ).fetchone()
        if doctor is None:
            return {"error": f"No doctor named '{doctor_name}' found. Use list_doctors to see options."}

        booked = conn.execute(
            "SELECT time FROM appointments WHERE doctor_name = ? AND date = ? AND status IN ('booked', 'pending')",
            (doctor_name, date),
        ).fetchall()
    booked_times = {r["time"] for r in booked}
    available = [t for t in db.CLINIC_HOURS if t not in booked_times]
    return {"doctor": doctor_name, "date": date, "available_slots": available}


def book_appointment(patient_name: str, doctor_name: str, date: str, time: str, reason: str = "") -> dict:
    """Book an appointment. Fails if the slot is already taken or invalid."""
    _validate_date(date)
    _validate_time(time)

    with db.get_connection() as conn:
        doctor = conn.execute(
            "SELECT name FROM doctors WHERE name = ?", (doctor_name,)
        ).fetchone()
        if doctor is None:
            return {"error": f"No doctor named '{doctor_name}' found. Use list_doctors to see options."}

        clash = conn.execute(
            "SELECT id FROM appointments WHERE doctor_name = ? AND date = ? AND time = ? AND status IN ('booked', 'pending')",
            (doctor_name, date, time),
        ).fetchone()
        if clash is not None:
            return {"error": f"{doctor_name} is already booked at {time} on {date}. Try another slot."}

        cursor = conn.execute(
            "INSERT INTO appointments (patient_name, doctor_name, date, time, reason, status) "
            "VALUES (?, ?, ?, ?, ?, 'booked')",
            (patient_name, doctor_name, date, time, reason),
        )
        appointment_id = cursor.lastrowid

    return {
        "status": "booked",
        "appointment_id": appointment_id,
        "patient_name": patient_name,
        "doctor_name": doctor_name,
        "date": date,
        "time": time,
        "reason": reason,
    }


def cancel_appointment(appointment_id: int) -> dict:
    """Cancel an existing appointment by its ID."""
    with db.get_connection() as conn:
        existing = conn.execute(
            "SELECT id, status FROM appointments WHERE id = ?", (appointment_id,)
        ).fetchone()
        if existing is None:
            return {"error": f"No appointment with id {appointment_id}."}
        if existing["status"] == "cancelled":
            return {"error": f"Appointment {appointment_id} is already cancelled."}

        conn.execute(
            "UPDATE appointments SET status = 'cancelled' WHERE id = ?", (appointment_id,)
        )
    return {"status": "cancelled", "appointment_id": appointment_id}


def list_appointments(patient_name: str) -> list[dict]:
    """List all active (booked or pending) appointments for a patient."""
    with db.get_connection() as conn:
        rows = conn.execute(
            "SELECT id, doctor_name, date, time, reason, status FROM appointments "
            "WHERE patient_name = ? AND status IN ('booked', 'pending') ORDER BY date, time",
            (patient_name,),
        ).fetchall()
    return [dict(r) for r in rows]


def answer_faq(topic: str) -> dict:
    """Answer a common clinic question. topic is one of: hours, location, insurance, cancellation, new_patient."""
    if topic not in FAQ:
        return {"error": f"Unknown topic '{topic}'. Known topics: {', '.join(FAQ)}."}
    return {"topic": topic, "answer": FAQ[topic]}


# ---------------------------------------------------------------------------
# Dashboard query helpers (used by web.py, not exposed to the model)
# ---------------------------------------------------------------------------

# Representative hours shown as dots on each doctor's "Available today" card.
_AVAILABILITY_PREVIEW_HOURS = ["09:00", "10:00", "11:00", "13:00", "15:00", "16:00"]


def doctor_directory(date: str) -> list[dict]:
    """Doctors with dashboard profile stats and a today-availability preview."""
    with db.get_connection() as conn:
        doctors = conn.execute(
            "SELECT name, specialty, bio, experience_years, rating, patients_per_week "
            "FROM doctors ORDER BY name"
        ).fetchall()
        booked = conn.execute(
            "SELECT doctor_name, time FROM appointments WHERE date = ? AND status IN ('booked', 'pending')",
            (date,),
        ).fetchall()

    busy = {(r["doctor_name"], r["time"]) for r in booked}
    result = []
    for d in doctors:
        preview = [
            {"hour": h.split(":")[0], "available": (d["name"], h) not in busy}
            for h in _AVAILABILITY_PREVIEW_HOURS
        ]
        result.append({**dict(d), "availability_preview": preview})
    return result


def list_patients() -> list[dict]:
    """Patients with last visit and next appointment derived from bookings."""
    with db.get_connection() as conn:
        patients = conn.execute(
            "SELECT name, sex, age, insurance, status FROM patients ORDER BY name"
        ).fetchall()
        appts = conn.execute(
            "SELECT patient_name, doctor_name, date, time, status FROM appointments ORDER BY date, time"
        ).fetchall()

    today = datetime.now().strftime("%Y-%m-%d")
    by_patient: dict[str, list] = {}
    for a in appts:
        by_patient.setdefault(a["patient_name"], []).append(a)

    result = []
    for p in patients:
        history = by_patient.get(p["name"], [])
        past = [a for a in history if a["date"] < today and a["status"] == "booked"]
        upcoming = [a for a in history if a["date"] >= today and a["status"] in ("booked", "pending")]
        last_visit = max(past, key=lambda a: (a["date"], a["time"]), default=None)
        next_appt = min(upcoming, key=lambda a: (a["date"], a["time"]), default=None)
        result.append(
            {
                **dict(p),
                "last_visit": f"{last_visit['date']} {last_visit['time']}" if last_visit else None,
                "next_appointment": (
                    f"{next_appt['date']} {next_appt['time']} · {next_appt['doctor_name']}"
                    if next_appt
                    else None
                ),
            }
        )
    return result


def schedule_for_date(date: str) -> dict:
    """All appointments for a date, grouped by hour, plus booked/pending/cancelled counts."""
    with db.get_connection() as conn:
        rows = conn.execute(
            "SELECT id, patient_name, doctor_name, time, reason, status FROM appointments "
            "WHERE date = ? ORDER BY time",
            (date,),
        ).fetchall()

    appointments = [dict(r) for r in rows]
    counts = {"booked": 0, "pending": 0, "cancelled": 0}
    for a in appointments:
        counts[a["status"]] = counts.get(a["status"], 0) + 1

    return {"date": date, "appointments": appointments, "counts": counts}


def list_threads() -> list[dict]:
    """Message threads with a preview of the most recent message."""
    with db.get_connection() as conn:
        threads = conn.execute("SELECT id, patient_name, channel FROM message_threads").fetchall()
        result = []
        for t in threads:
            last = conn.execute(
                "SELECT text, sender, created_at FROM thread_messages "
                "WHERE thread_id = ? ORDER BY id DESC LIMIT 1",
                (t["id"],),
            ).fetchone()
            result.append(
                {
                    "id": t["id"],
                    "patient_name": t["patient_name"],
                    "channel": t["channel"],
                    "preview": last["text"] if last else "",
                    "last_sender": last["sender"] if last else None,
                }
            )
    return result


def get_thread(thread_id: int) -> dict | None:
    """Full message history for a thread."""
    with db.get_connection() as conn:
        thread = conn.execute(
            "SELECT id, patient_name, channel FROM message_threads WHERE id = ?", (thread_id,)
        ).fetchone()
        if thread is None:
            return None
        messages = conn.execute(
            "SELECT sender, text, tool_line, created_at FROM thread_messages "
            "WHERE thread_id = ? ORDER BY id ASC",
            (thread_id,),
        ).fetchall()
    return {**dict(thread), "messages": [dict(m) for m in messages]}


def add_thread_message(thread_id: int, sender: str, text: str, tool_line: str | None = None) -> dict:
    """Append a message to a thread (used for both patient replies and Clara's responses)."""
    with db.get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO thread_messages (thread_id, sender, text, tool_line) VALUES (?, ?, ?, ?)",
            (thread_id, sender, text, tool_line),
        )
    return {"id": cursor.lastrowid, "thread_id": thread_id, "sender": sender, "text": text, "tool_line": tool_line}


def settings_snapshot() -> dict:
    """Static clinic configuration shown on the Settings page."""
    return {
        "clinic_name": db.CLINIC_NAME,
        "hours": [
            {"label": "Mon – Fri", "value": "8:00 AM – 6:00 PM"},
            {"label": "Saturday", "value": "9:00 AM – 1:00 PM"},
            {"label": "Sunday", "value": "Closed"},
        ],
        "insurance": [
            {"label": "Blue Cross", "accepted": True},
            {"label": "UnitedHealthcare", "accepted": True},
            {"label": "Aetna", "accepted": True},
            {"label": "Cigna", "accepted": True},
            {"label": "Self-pay", "accepted": True},
        ],
        "cancellation_policy": [
            {"label": "Notice required", "value": "24 hours"},
            {"label": "Late cancel fee", "value": "USD 5"},
            {"label": "No-show fee", "value": "USD 10"},
        ],
        "guardrails": [
            {
                "title": "No diagnosis or symptom interpretation",
                "detail": "Routed to a clinician every time",
            },
            {
                "title": "No medication advice",
                "detail": "Includes dosage, interactions, or substitutions",
            },
            {
                "title": "Emergency language",
                "detail": "Immediately flagged and directed to call emergency services",
            },
        ],
    }
