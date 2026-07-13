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
        "Dr. Amina Javed",
        "Family Medicine",
        "Provides comprehensive care for families and chronic conditions with a calm, patient-centered approach.",
        14,
        4.9,
        38,
    ),
    (
        "Dr. Saad Ahmed",
        "Cardiology",
        "Expert in heart health, hypertension, and preventive cardiology for adult patients.",
        12,
        4.8,
        30,
    ),
    (
        "Dr. Zainab Bashir",
        "Pediatrics",
        "Specializes in pediatric wellness, immunizations, and developmental care for children and teens.",
        9,
        4.9,
        26,
    ),
    (
        "Dr. Omar Nazir",
        "General Surgery",
        "Balances clinic consultations with procedural care, focusing on timely referrals and surgical planning.",
        16,
        4.8,
        22,
    ),
    (
        "Dr. Nadia Hussain",
        "Dermatology",
        "Offers skin care, acne management, and cosmetic dermatology recommendations with clear follow-up plans.",
        11,
        4.7,
        20,
    ),
    (
        "Dr. Khalid Raza",
        "Neurology",
        "Provides diagnostic assessments for headaches, neuropathy, and movement disorders in adults.",
        13,
        4.8,
        18,
    ),
    (
        "Dr. Mariam Siddiqui",
        "Obstetrics & Gynecology",
        "Dedicated to women’s health, prenatal care, and reproductive wellness with supportive bedside care.",
        10,
        4.9,
        24,
    ),
    (
        "Dr. Tahir Qureshi",
        "ENT",
        "Treats sinus, ear, and throat conditions with same-day follow-up planning for persistent symptoms.",
        8,
        4.6,
        16,
    ),
    (
        "Dr. Fatima Noor",
        "Endocrinology",
        "Manages diabetes, thyroid conditions, and hormonal health with personalized care plans.",
        12,
        4.8,
        20,
    ),
    (
        "Dr. Bilal Javed",
        "Gastroenterology",
        "Treats digestive health, IBS, and liver concerns using evidence-based evaluation and follow-up.",
        15,
        4.7,
        18,
    ),
    (
        "Dr. Hassan Rizvi",
        "Orthopedics",
        "Focused on joint pain, sports injuries, and rehabilitation planning for active patients.",
        13,
        4.8,
        22,
    ),
    (
        "Dr. Saira Khan",
        "Psychiatry",
        "Supports mental health, anxiety, and mood care with a thoughtful, confidential approach.",
        11,
        4.7,
        14,
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
    """Populate doctors/patients/appointments/threads with demo data.
    The seed mirrors the original dashboard mockup but uses the Pakistani
    doctor profiles defined in SAMPLE_DOCTORS and the SAMPLE_PATIENTS list.
    """
    # Insert doctors and patients
    conn.executemany(
        "INSERT INTO doctors (name, specialty, bio, experience_years, rating, patients_per_week) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        SAMPLE_DOCTORS,
    )
    conn.executemany(
        "INSERT INTO patients (name, sex, age, phone, insurance, status) VALUES (?, ?, ?, ?, ?, ?)",
        SAMPLE_PATIENTS,
    )

    # Anchor demo appointments on the next weekday so the schedule page isn't empty
    today = _next_weekday(date.today())
    today_s = today.isoformat()

    demo_appointments = [
        ("Hassan Iqbal", "Dr. Amina Javed", today_s, "09:00", "Annual check-up", "booked"),
        ("Sara Malik", "Dr. Saad Ahmed", today_s, "10:00", "New patient", "booked"),
        ("Bilal Khan", "Dr. Amina Javed", today_s, "10:00", "Follow-up", "cancelled"),
        ("Waiting on confirmation", "Dr. Saad Ahmed", today_s, "13:00", "Requested by phone", "pending"),
        ("Amina Raza", "Dr. Amina Javed", today_s, "14:00", "Follow-up", "booked"),
        ("Yusuf Tariq", "Dr. Zainab Bashir", today_s, "15:00", "Vaccination", "booked"),
    ]
    conn.executemany(
        "INSERT INTO appointments (patient_name, doctor_name, date, time, reason, status) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        demo_appointments,
    )

    # Patient message threads
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
        (thread_ids["Noor Fatima"], "patient", "Can I cancel my 3pm with Dr. Amina Javed today?", None),
        (
            thread_ids["Noor Fatima"],
            "clara",
            "Of course — I've cancelled your 3:00 PM vaccination appointment. Would you like to rebook for another day?",
            'cancel_appointment(patient: "Noor Fatima", slot: "15:00")',
        ),
        (thread_ids["Noor Fatima"], "patient", "Next Tuesday if possible", None),
        (thread_ids["Noor Fatima"], "clara", "Dr. Zainab has 10:30 AM or 1:15 PM open next Tuesday.", None),
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
