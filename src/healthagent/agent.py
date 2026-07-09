"""Claude-powered clinic admin agent.

Wraps the Anthropic Messages API tool-use loop around the plain functions
in `tools.py`. The model decides which tool to call based on the user's
natural-language request; this module executes the call and feeds the
result back until the model produces a final text reply.
"""
from __future__ import annotations

import json
import os

from anthropic import Anthropic

from . import tools

MODEL = "claude-sonnet-4-5"

SYSTEM_PROMPT = """You are Clara, the front-desk admin assistant for Ridgeview Family Clinic.

Scope: scheduling, availability, cancellations, and answering clinic FAQs
(hours, location, insurance, cancellation policy, new-patient info).

Hard rules:
- You are NOT a medical professional. Never diagnose, interpret symptoms,
  or give medical/treatment advice. If asked, say you can't help with
  that and suggest the patient speak to a clinician or call the clinic
  directly for urgent concerns.
- If a request sounds like a medical emergency, tell the person to call
  their local emergency number immediately.
- Always confirm key details (patient name, doctor, date, time) back to
  the user before booking, and confirm again after a tool call succeeds.
- If a tool call returns an error, explain it plainly and suggest a fix
  (e.g. propose checking availability again).
- Be concise and friendly.
"""

TOOL_DEFINITIONS = [
    {
        "name": "list_doctors",
        "description": "List all doctors at the clinic with their specialties.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "check_availability",
        "description": "List open appointment slots for a doctor on a given date.",
        "input_schema": {
            "type": "object",
            "properties": {
                "doctor_name": {"type": "string", "description": "Full doctor name, e.g. 'Dr. Amara Chen'"},
                "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
            },
            "required": ["doctor_name", "date"],
        },
    },
    {
        "name": "book_appointment",
        "description": "Book an appointment for a patient with a doctor at a specific date and time.",
        "input_schema": {
            "type": "object",
            "properties": {
                "patient_name": {"type": "string"},
                "doctor_name": {"type": "string"},
                "date": {"type": "string", "description": "YYYY-MM-DD"},
                "time": {"type": "string", "description": "HH:MM, 24-hour, e.g. 14:30"},
                "reason": {"type": "string", "description": "Brief reason for visit, optional"},
            },
            "required": ["patient_name", "doctor_name", "date", "time"],
        },
    },
    {
        "name": "cancel_appointment",
        "description": "Cancel an existing appointment by its ID.",
        "input_schema": {
            "type": "object",
            "properties": {"appointment_id": {"type": "integer"}},
            "required": ["appointment_id"],
        },
    },
    {
        "name": "list_appointments",
        "description": "List a patient's upcoming booked appointments.",
        "input_schema": {
            "type": "object",
            "properties": {"patient_name": {"type": "string"}},
            "required": ["patient_name"],
        },
    },
    {
        "name": "answer_faq",
        "description": "Answer a common clinic question.",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "enum": ["hours", "location", "insurance", "cancellation", "new_patient"],
                }
            },
            "required": ["topic"],
        },
    },
]

TOOL_IMPLEMENTATIONS = {
    "list_doctors": lambda **kwargs: tools.list_doctors(),
    "check_availability": lambda **kwargs: tools.check_availability(**kwargs),
    "book_appointment": lambda **kwargs: tools.book_appointment(**kwargs),
    "cancel_appointment": lambda **kwargs: tools.cancel_appointment(**kwargs),
    "list_appointments": lambda **kwargs: tools.list_appointments(**kwargs),
    "answer_faq": lambda **kwargs: tools.answer_faq(**kwargs),
}


def format_tool_line(name: str, tool_input: dict) -> str:
    """Render a tool call as the short trace shown under chat bubbles in the
    dashboard, e.g. check_availability(doctor: "Whitfield", date: "2026-07-08")."""
    parts = []
    for key, value in tool_input.items():
        rendered = f'"{value}"' if isinstance(value, str) else str(value)
        parts.append(f"{key}: {rendered}")
    return f"→ {name}({', '.join(parts)})"


class ClinicAgent:
    def __init__(self, api_key: str | None = None, model: str = MODEL, messages: list[dict] | None = None):
        self.client = Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        self.model = model
        self.messages: list[dict] = messages or []

    def _run_tool(self, name: str, tool_input: dict) -> dict:
        impl = TOOL_IMPLEMENTATIONS.get(name)
        if impl is None:
            return {"error": f"Unknown tool '{name}'"}
        try:
            return impl(**tool_input)
        except Exception as exc:  # noqa: BLE001 - surface to the model as an error result
            return {"error": str(exc)}

    def send(self, user_message: str) -> dict:
        """Send a user message, run any tool calls, and return the final reply
        plus a trace of tool calls made along the way.

        Returns: {"reply": str, "tool_calls": [{"name": str, "input": dict, "result": dict, "trace": str}]}
        """
        self.messages.append({"role": "user", "content": user_message})
        tool_calls: list[dict] = []

        while True:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=TOOL_DEFINITIONS,
                messages=self.messages,
            )

            self.messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason != "tool_use":
                reply = "".join(block.text for block in response.content if block.type == "text")
                return {"reply": reply, "tool_calls": tool_calls}

            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                result = self._run_tool(block.name, block.input)
                tool_calls.append(
                    {
                        "name": block.name,
                        "input": block.input,
                        "result": result,
                        "trace": format_tool_line(block.name, block.input),
                    }
                )
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    }
                )

            self.messages.append({"role": "user", "content": tool_results})
