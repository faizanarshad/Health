"""Business logic for the clinic admin agent.

Every function here is plain, testable Python with no dependency on the
Anthropic client. `agent.py` exposes these as tools the model can call.

Scope note: this agent handles scheduling/admin tasks only. It does not
diagnose, triage, or give medical advice.
"""
from __future__ import annotations

from datetime import datetime

from . import database as db

FAQ = {
    "hours": "The clinic is open Monday-Friday, 9:00 AM to 5:00 PM. Closed on weekends and public holidays.",
    "location": "123 Wellness Ave, Suite 200, Springfield.",
    "insurance": "We accept most major insurance plans. Please bring your insurance card to your first visit.",
    "cancellation": "Cancellations are free up to 24 hours before your appointment. Late cancellations may incur a $25 fee.",
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
            "SELECT time FROM appointments WHERE doctor_name = ? AND date = ? AND status = 'booked'",
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
            "SELECT id FROM appointments WHERE doctor_name = ? AND date = ? AND time = ? AND status = 'booked'",
            (doctor_name, date, time),
        ).fetchone()
        if clash is not None:
            return {"error": f"{doctor_name} is already booked at {time} on {date}. Try another slot."}

        cursor = conn.execute(
            "INSERT INTO appointments (patient_name, doctor_name, date, time, reason) "
            "VALUES (?, ?, ?, ?, ?)",
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
    """List all active (booked) appointments for a patient."""
    with db.get_connection() as conn:
        rows = conn.execute(
            "SELECT id, doctor_name, date, time, reason FROM appointments "
            "WHERE patient_name = ? AND status = 'booked' ORDER BY date, time",
            (patient_name,),
        ).fetchall()
    return [dict(r) for r in rows]


def answer_faq(topic: str) -> dict:
    """Answer a common clinic question. topic is one of: hours, location, insurance, cancellation, new_patient."""
    if topic not in FAQ:
        return {"error": f"Unknown topic '{topic}'. Known topics: {', '.join(FAQ)}."}
    return {"topic": topic, "answer": FAQ[topic]}
