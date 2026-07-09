"""SQLite persistence layer for the clinic admin agent.

Tables:
    doctors          - clinic staff, specialty, and dashboard profile stats
    patients         - patient directory (name + contact + insurance/status)
    appointments     - bookings linking a patient to a doctor at a date/time
    message_threads  - patient-initiated conversation threads (e.g. SMS)
    thread_messages  - individual messages within a thread
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date, timedelta
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "clinic.db"

CLINIC_NAME = "Ridgeview Family Clinic"

SCHEMA = """
CREATE TABLE IF NOT EXISTS doctors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    specialty TEXT NOT NULL,
    bio TEXT NOT NULL DEFAULT '',
    experience_years INTEGER NOT NULL DEFAULT 0,
    rating REAL NOT NULL DEFAULT 0,
    patients_per_week INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    sex TEXT,
    age INTEGER,
    phone TEXT,
    insurance TEXT,
    status TEXT NOT NULL DEFAULT 'Active'  -- Active | New patient | Cancelled visit
);

CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_name TEXT NOT NULL,
    doctor_name TEXT NOT NULL,
    date TEXT NOT NULL,   -- YYYY-MM-DD
    time TEXT NOT NULL,   -- HH:MM (24h)
    reason TEXT,
    status TEXT NOT NULL DEFAULT 'booked',  -- booked | pending | cancelled
    FOREIGN KEY (doctor_name) REFERENCES doctors (name)
);

CREATE TABLE IF NOT EXISTS message_threads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_name TEXT NOT NULL,
    channel TEXT NOT NULL DEFAULT 'SMS'
);

CREATE TABLE IF NOT EXISTS thread_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id INTEGER NOT NULL,
    sender TEXT NOT NULL,          -- 'patient' | 'clara'
    text TEXT NOT NULL,
    tool_line TEXT,                -- optional "→ tool_name(...)" trace shown in the UI
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (thread_id) REFERENCES message_threads (id)
);
"""

SAMPLE_DOCTORS = [
    # name, specialty, bio, experience_years, rating, patients_per_week
    (
        "Dr. Whitfield",
        "Family Medicine",
        "Sees patients of all ages for check-ups, chronic condition management, "
        "and general follow-ups. Prefers morning slots for new patients.",
        11,
        4.9,
        32,
    ),
    (
        "Dr. Osei",
        "Internal Medicine",
        "Handles new patient intakes and complex cases requiring longer visits. "
        "Runs slightly behind schedule on Mondays.",
        7,
        4.8,
        24,
    ),
    (
        "Dr. Chen",
        "Pediatrics",
        "Focuses on vaccinations, growth check-ups, and pediatric care. Parents "
        "can request her directly for children under 12.",
        5,
        5.0,
        28,
    ),
]

SAMPLE_PATIENTS = [
    # name, sex, age, phone, insurance, status
    ("Hassan Iqbal", "M", 42, "+92-300-0000001", "Bupa", "Active"),
    ("Sara Malik", "F", 29, "+92-300-0000002", "Cigna", "New patient"),
    ("Amina Raza", "F", 35, "+92-300-0000003", "Self-pay", "Active"),
    ("Yusuf Tariq", "M", 8, "+92-300-0000004", "Bupa", "Active"),
    ("Bilal Khan", "M", 51, "+92-300-0000005", "Cigna", "Cancelled visit"),
    ("Noor Fatima", "F", 31, "+92-300-0000006", "Bupa", "Active"),
]

# Clinic operates 09:00-17:00 in 30-minute slots, Mon-Fri.
CLINIC_HOURS = [f"{h:02d}:{m:02d}" for h in range(9, 17) for m in (0, 30)]


def _next_weekday(d: date) -> date:
    """Roll a date forward to the nearest Mon-Fri (clinic is closed weekends)."""
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


@contextmanager
def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _seed_demo_data(conn: sqlite3.Connection) -> None:
    """Populate doctors/patients/appointments/threads with data mirroring the
    dashboard mockup, anchored on the real current date so the schedule page
    isn't empty on first run."""
    conn.executemany(
        "INSERT INTO doctors (name, specialty, bio, experience_years, rating, patients_per_week) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        SAMPLE_DOCTORS,
    )
    conn.executemany(
        "INSERT INTO patients (name, sex, age, phone, insurance, status) VALUES (?, ?, ?, ?, ?, ?)",
        SAMPLE_PATIENTS,
    )

    today = _next_weekday(date.today())
    today_s = today.isoformat()

    demo_appointments = [
        ("Hassan Iqbal", "Dr. Whitfield", today_s, "09:00", "Annual check-up", "booked"),
        ("Sara Malik", "Dr. Osei", today_s, "10:00", "New patient", "booked"),
        ("Bilal Khan", "Dr. Whitfield", today_s, "10:00", "Follow-up", "cancelled"),
        ("Waiting on confirmation", "Dr. Osei", today_s, "13:00", "Requested by phone", "pending"),
        ("Amina Raza", "Dr. Whitfield", today_s, "14:00", "Follow-up", "booked"),
        ("Yusuf Tariq", "Dr. Chen", today_s, "15:00", "Vaccination", "booked"),
    ]
    conn.executemany(
        "INSERT INTO appointments (patient_name, doctor_name, date, time, reason, status) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        demo_appointments,
    )

    # Patient message threads (mirrors the Messages page in the mockup).
    threads = [
        ("Noor Fatima", "SMS"),
        ("Ahmed Raza", "SMS"),
        ("Zainab Sheikh", "SMS"),
        ("Omar Farooq", "SMS"),
    ]
    thread_ids = {}
    for patient_name, channel in threads:
        cur = conn.execute(
            "INSERT INTO message_threads (patient_name, channel) VALUES (?, ?)",
            (patient_name, channel),
        )
        thread_ids[patient_name] = cur.lastrowid

    demo_messages = [
        (thread_ids["Noor Fatima"], "patient", "Can I cancel my 3pm with Dr. Chen today?", None),
        (
            thread_ids["Noor Fatima"],
            "clara",
            "Of course — I've cancelled your 3:00 PM vaccination appointment with Dr. Chen. "
            "Would you like to rebook for another day?",
            'cancel_appointment(patient: "Noor Fatima", slot: "15:00")',
        ),
        (thread_ids["Noor Fatima"], "patient", "Next Tuesday if possible", None),
        (
            thread_ids["Noor Fatima"],
            "clara",
            "Dr. Chen has 10:30 AM or 1:15 PM open next Tuesday. Which works better?",
            None,
        ),
        (thread_ids["Ahmed Raza"], "patient", "Thanks, see you Thursday!", None),
        (thread_ids["Zainab Sheikh"], "patient", "Do you have parking on site?", None),
        (thread_ids["Omar Farooq"], "patient", "Rescheduled to next week, thank you", None),
    ]
    conn.executemany(
        "INSERT INTO thread_messages (thread_id, sender, text, tool_line) VALUES (?, ?, ?, ?)",
        demo_messages,
    )


def init_db(seed: bool = True) -> None:
    """Create tables and, on first run, seed demo data."""
    with get_connection() as conn:
        conn.executescript(SCHEMA)
        if seed:
            existing = conn.execute("SELECT COUNT(*) AS c FROM doctors").fetchone()["c"]
            if existing == 0:
                _seed_demo_data(conn)


def reset_db() -> None:
    """Delete the database file (useful for tests)."""
    if DB_PATH.exists():
        DB_PATH.unlink()
