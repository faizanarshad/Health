"""SQLite persistence layer for the clinic admin agent.

Tables:
    doctors      - clinic staff and their specialty
    patients     - patient records (name + contact only, no clinical data)
    appointments - bookings linking a patient to a doctor at a date/time
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "clinic.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS doctors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    specialty TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT
);

CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_name TEXT NOT NULL,
    doctor_name TEXT NOT NULL,
    date TEXT NOT NULL,   -- YYYY-MM-DD
    time TEXT NOT NULL,   -- HH:MM (24h)
    reason TEXT,
    status TEXT NOT NULL DEFAULT 'booked',  -- booked | cancelled
    FOREIGN KEY (doctor_name) REFERENCES doctors (name)
);
"""

SAMPLE_DOCTORS = [
    ("Dr. Amara Chen", "General Practice"),
    ("Dr. Luis Ferreira", "Pediatrics"),
    ("Dr. Priya Nandan", "Cardiology"),
    ("Dr. Sam O'Rourke", "Dermatology"),
]

# Clinic operates 09:00-17:00 in 30-minute slots, Mon-Fri.
CLINIC_HOURS = [f"{h:02d}:{m:02d}" for h in range(9, 17) for m in (0, 30)]


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


def init_db(seed: bool = True) -> None:
    """Create tables and, on first run, seed sample doctors."""
    with get_connection() as conn:
        conn.executescript(SCHEMA)
        if seed:
            existing = conn.execute("SELECT COUNT(*) AS c FROM doctors").fetchone()["c"]
            if existing == 0:
                conn.executemany(
                    "INSERT INTO doctors (name, specialty) VALUES (?, ?)",
                    SAMPLE_DOCTORS,
                )


def reset_db() -> None:
    """Delete the database file (useful for tests)."""
    if DB_PATH.exists():
        DB_PATH.unlink()
