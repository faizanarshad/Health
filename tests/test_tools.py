"""Unit tests for tools.py. No API key or network access required."""
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from src.healthagent import database as db
from src.healthagent import tools


@pytest.fixture(autouse=True)
def fresh_db(monkeypatch, tmp_path):
    """Point the DB at a temp file for each test and seed it."""
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test_clinic.db")
    db.init_db()
    yield
    db.reset_db()


def test_list_doctors_seeded():
    doctors = tools.list_doctors()
    names = {d["name"] for d in doctors}
    assert "Dr. Whitfield" in names
    assert len(doctors) == 3


def test_check_availability_full_day():
    result = tools.check_availability("Dr. Whitfield", "2026-07-13")  # a Monday, unrelated to seeded "today" data
    assert result["doctor"] == "Dr. Whitfield"
    assert len(result["available_slots"]) == len(db.CLINIC_HOURS)


def test_check_availability_unknown_doctor():
    result = tools.check_availability("Dr. Nobody", "2026-07-13")
    assert "error" in result


def test_check_availability_weekend_rejected():
    with pytest.raises(ValueError):
        tools.check_availability("Dr. Whitfield", "2026-07-11")  # a Saturday


def test_book_and_prevent_double_booking():
    booked = tools.book_appointment(
        "Jane Doe", "Dr. Whitfield", "2026-07-13", "09:00", reason="checkup"
    )
    assert booked["status"] == "booked"

    clash = tools.book_appointment("John Roe", "Dr. Whitfield", "2026-07-13", "09:00")
    assert "error" in clash


def test_book_rejects_invalid_time():
    with pytest.raises(ValueError):
        tools.book_appointment("Jane Doe", "Dr. Whitfield", "2026-07-13", "09:15")


def test_cancel_appointment_frees_slot():
    booked = tools.book_appointment("Jane Doe", "Dr. Whitfield", "2026-07-13", "10:00")
    appointment_id = booked["appointment_id"]

    cancelled = tools.cancel_appointment(appointment_id)
    assert cancelled["status"] == "cancelled"

    availability = tools.check_availability("Dr. Whitfield", "2026-07-13")
    assert "10:00" in availability["available_slots"]


def test_cancel_unknown_appointment():
    result = tools.cancel_appointment(9999)
    assert "error" in result


def test_list_appointments_only_shows_booked():
    b1 = tools.book_appointment("Jane Doe", "Dr. Whitfield", "2026-07-13", "09:00")
    tools.book_appointment("Jane Doe", "Dr. Osei", "2026-07-14", "11:00")
    tools.cancel_appointment(b1["appointment_id"])

    appts = tools.list_appointments("Jane Doe")
    assert len(appts) == 1
    assert appts[0]["doctor_name"] == "Dr. Osei"


def test_answer_faq_known_and_unknown():
    known = tools.answer_faq("hours")
    assert "answer" in known

    unknown = tools.answer_faq("parking")
    assert "error" in unknown


# ---------------------------------------------------------------------------
# Dashboard query helpers
# ---------------------------------------------------------------------------

def test_list_patients_seeded_and_shaped():
    patients = tools.list_patients()
    assert len(patients) == 6
    names = {p["name"] for p in patients}
    assert "Noor Fatima" in names
    for p in patients:
        assert "last_visit" in p
        assert "next_appointment" in p


def test_doctor_directory_has_profile_and_availability():
    today = datetime.now().strftime("%Y-%m-%d")
    directory = tools.doctor_directory(today)
    assert len(directory) == 3
    whitfield = next(d for d in directory if d["name"] == "Dr. Whitfield")
    assert whitfield["specialty"] == "Family Medicine"
    assert len(whitfield["availability_preview"]) == 6


def test_schedule_for_date_counts_seeded_appointments():
    today = datetime.now().strftime("%Y-%m-%d")
    schedule = tools.schedule_for_date(today)
    assert schedule["counts"]["booked"] >= 1
    assert schedule["counts"]["pending"] >= 1
    assert schedule["counts"]["cancelled"] >= 1


def test_thread_lifecycle():
    threads = tools.list_threads()
    noor = next(t for t in threads if t["patient_name"] == "Noor Fatima")
    detail = tools.get_thread(noor["id"])
    assert detail is not None
    assert len(detail["messages"]) >= 2

    tools.add_thread_message(noor["id"], "patient", "Test message")
    updated = tools.get_thread(noor["id"])
    assert updated["messages"][-1]["text"] == "Test message"

    assert tools.get_thread(999999) is None


def test_settings_snapshot_shape():
    settings = tools.settings_snapshot()
    assert settings["clinic_name"] == db.CLINIC_NAME
    assert len(settings["hours"]) == 3
    assert len(settings["guardrails"]) == 3
