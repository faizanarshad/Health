"""CLI entry point for the clinic admin agent.

Usage:
    python main.py

Requires ANTHROPIC_API_KEY to be set (in the environment or a .env file).
"""
from __future__ import annotations

import sys

from dotenv import load_dotenv

from src.healthagent import database as db
from src.healthagent.agent import ClinicAgent


def main() -> None:
    load_dotenv()
    db.init_db()

    try:
        agent = ClinicAgent()
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to start agent: {exc}")
        print("Make sure ANTHROPIC_API_KEY is set (see .env.example).")
        sys.exit(1)

    print("Clara - Springfield Wellness Clinic assistant")
    print("Ask about appointments, availability, or clinic info. Type 'quit' to exit.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in {"quit", "exit"}:
            print("Goodbye!")
            break

        result = agent.send(user_input)
        print(f"Clara: {result['reply']}")
        for call in result["tool_calls"]:
            print(f"  {call['trace']}")
        print()


if __name__ == "__main__":
    main()
