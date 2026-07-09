"""Reset the clinic database and reseed it with dummy/demo data.

Useful when you want a clean slate — e.g. after testing bookings/cancellations
through the dashboard or CLI and you want the Schedule/Patients/Messages pages
back to their original demo state.

Usage:
    python seed_demo_data.py
"""
from __future__ import annotations

from src.healthagent import database as db


def main() -> None:
    db.reset_db()
    db.init_db(seed=True)
    print(f"Reseeded {db.DB_PATH} with dummy data for {db.CLINIC_NAME}.")
    print("Restart the app (python web.py or python main.py) to see the fresh data.")


if __name__ == "__main__":
    main()
