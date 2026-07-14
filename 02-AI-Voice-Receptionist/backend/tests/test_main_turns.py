import asyncio
import json

import main
from audio_processor import CallerTurnBuffer, pcm16_to_wav
from business_config import APPOINTMENT_FIELDS
from call_session import CallSession
from lead_manager import LeadManager


class FakeWebSocket:
    def __init__(self) -> None:
        self.messages: list[dict] = []

    async def send_json(self, message: dict) -> None:
        self.messages.append(message)


class FakeGroqService:
    def __init__(self, transcripts: list[str]) -> None:
        self.transcripts = iter(transcripts)

    async def transcribe(self, wav_audio: bytes) -> str:
        return next(self.transcripts)

    async def chat(self, messages: list[dict]) -> str:
        return "A normal chat response."

    async def synthesize(self, text: str) -> bytes:
        return pcm16_to_wav(b"\x00\x00" * 160)


def test_dtmf_does_not_advance_appointment_state() -> None:
    session = CallSession(call_sid="CA-test", stream_sid="MZ-test")
    session.appointment.begin()
    session.appointment.record("Test Caller")
    before_values = session.appointment.values.copy()
    before_field = session.appointment.current_field

    main._handle_dtmf_event(CallerTurnBuffer(), session)

    assert session.appointment.values == before_values
    assert session.appointment.current_field == before_field


def test_phone_numbers_are_redacted_from_logs() -> None:
    redacted = main._redact_phone_numbers(
        "Please call me on +1 (555) 123-4567."
    )

    assert "555" not in redacted
    assert "4567" not in redacted
    assert "ending 67" in redacted


def test_completed_appointment_is_written_once(tmp_path, monkeypatch) -> None:
    answers = [
        "Book an appointment",
        "Test Caller",
        "+1 555 0100",
        "Next Monday",
        "10 AM",
        "Requested Service",
        "What are your hours?",
    ]
    fake_groq = FakeGroqService(answers)
    destination = tmp_path / "leads.json"
    monkeypatch.setattr(main, "groq_service", fake_groq)
    monkeypatch.setattr(main, "lead_manager", LeadManager(destination))
    session = CallSession(call_sid="CA-test", stream_sid="MZ-test")
    websocket = FakeWebSocket()

    async def process_all_turns() -> None:
        for _ in answers:
            await main._process_caller_turn(websocket, session, b"test-wav")

    asyncio.run(process_all_turns())

    saved = json.loads(destination.read_text(encoding="utf-8"))
    assert len(saved) == 1
    assert all(saved[0][field] for field in APPOINTMENT_FIELDS)
    assert session.appointment.active is False
