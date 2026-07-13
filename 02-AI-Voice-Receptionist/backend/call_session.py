"""Per-call conversation history and deterministic appointment state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from business_config import APPOINTMENT_FIELDS, APPOINTMENT_PROMPTS

BOOKING_INTENT_PHRASES = (
    "book an appointment",
    "book appointment",
    "schedule an appointment",
    "make an appointment",
    "appointment booking",
    "i need an appointment",
    "i want an appointment",
)


def is_booking_intent(transcript: str) -> bool:
    normalized = transcript.casefold().strip()
    return any(phrase in normalized for phrase in BOOKING_INTENT_PHRASES)


@dataclass
class AppointmentCapture:
    active: bool = False
    field_index: int = 0
    values: dict[str, str] = field(default_factory=dict)

    @property
    def current_field(self) -> str | None:
        if not self.active or self.field_index >= len(APPOINTMENT_FIELDS):
            return None
        return APPOINTMENT_FIELDS[self.field_index]

    def begin(self) -> str:
        self.active = True
        self.field_index = 0
        self.values = {}
        return APPOINTMENT_PROMPTS[APPOINTMENT_FIELDS[0]]

    def record(self, answer: str) -> tuple[str | None, dict[str, str] | None]:
        field_name = self.current_field
        if field_name is None:
            raise RuntimeError("Appointment capture is not active")

        cleaned_answer = answer.strip()
        if not cleaned_answer:
            return APPOINTMENT_PROMPTS[field_name], None

        self.values[field_name] = cleaned_answer
        self.field_index += 1

        if self.field_index == len(APPOINTMENT_FIELDS):
            completed = self.values.copy()
            self.active = False
            return None, completed

        next_field = APPOINTMENT_FIELDS[self.field_index]
        return APPOINTMENT_PROMPTS[next_field], None


@dataclass
class CallSession:
    call_sid: str
    stream_sid: str
    caller_phone: str = ""
    conversation_history: list[dict[str, str]] = field(default_factory=list)
    appointment: AppointmentCapture = field(default_factory=AppointmentCapture)

    def add_message(self, role: str, content: str) -> None:
        if role not in {"user", "assistant"}:
            raise ValueError("Conversation role must be user or assistant")
        self.conversation_history.append({"role": role, "content": content})

    def appointment_turn(
        self, transcript: str
    ) -> tuple[bool, str | None, dict[str, str] | None]:
        """Handle booking state after the transcript is added to history."""
        if self.appointment.active:
            prompt, completed = self.appointment.record(transcript)
            return True, prompt, completed

        if is_booking_intent(transcript):
            return True, self.appointment.begin(), None

        return False, None, None

    def messages_for_chat(self, system_prompt: str) -> list[dict[str, Any]]:
        return [
            {"role": "system", "content": system_prompt},
            *self.conversation_history,
        ]

