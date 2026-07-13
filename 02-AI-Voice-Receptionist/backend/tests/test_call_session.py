from business_config import APPOINTMENT_FIELDS, APPOINTMENT_PROMPTS
from call_session import CallSession, is_booking_intent


def test_booking_intent_detection() -> None:
    assert is_booking_intent("I would like to book an appointment please")
    assert not is_booking_intent("What are your hours?")


def test_call_session_preserves_conversation_history() -> None:
    session = CallSession(call_sid="CA123", stream_sid="MZ123")
    session.add_message("user", "Hello")
    session.add_message("assistant", "How may I help?")

    messages = session.messages_for_chat("System prompt")
    assert messages == [
        {"role": "system", "content": "System prompt"},
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "How may I help?"},
    ]


def test_appointment_state_collects_every_required_field() -> None:
    session = CallSession(call_sid="CA123", stream_sid="MZ123")
    handled, prompt, completed = session.appointment_turn("Book an appointment")

    assert handled is True
    assert prompt == APPOINTMENT_PROMPTS[APPOINTMENT_FIELDS[0]]
    assert completed is None

    answers = [
        "Test Caller",
        "+1 555 0100",
        "Next Monday",
        "10 AM",
        "Requested Service",
    ]
    for answer in answers:
        handled, prompt, completed = session.appointment_turn(answer)
        assert handled is True

    assert prompt is None
    assert completed == dict(zip(APPOINTMENT_FIELDS, answers, strict=True))
    assert session.appointment.active is False


def test_blank_appointment_answer_repeats_current_prompt() -> None:
    session = CallSession(call_sid="CA123", stream_sid="MZ123")
    session.appointment_turn("Schedule an appointment")

    handled, prompt, completed = session.appointment_turn("   ")

    assert handled is True
    assert prompt == APPOINTMENT_PROMPTS[APPOINTMENT_FIELDS[0]]
    assert completed is None
