import io
import struct
import wave

from groq_service import (
    MAX_TTS_INPUT_CHARACTERS,
    GroqService,
    GroqSettings,
    _format_provider_response_body,
)


def make_wav(frame_count: int = 80) -> bytes:
    output = io.BytesIO()
    with wave.open(output, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(24_000)
        wav_file.writeframes(struct.pack("<h", 1_000) * frame_count)
    return output.getvalue()


class FakeBinaryResponse:
    def __init__(self, audio: bytes) -> None:
        self.audio = audio

    def read(self) -> bytes:
        return self.audio


class FakeSpeech:
    def __init__(self) -> None:
        self.requests: list[dict] = []

    def create(self, **kwargs):
        self.requests.append(kwargs)
        return FakeBinaryResponse(make_wav())


class FakeAudio:
    def __init__(self) -> None:
        self.speech = FakeSpeech()


class FakeClient:
    def __init__(self) -> None:
        self.audio = FakeAudio()


def make_service() -> tuple[GroqService, FakeClient]:
    client = FakeClient()
    settings = GroqSettings(
        api_key="test-key",
        stt_model="test-stt",
        chat_model="test-chat",
        tts_model="canopylabs/orpheus-v1-english",
        tts_voice="autumn",
    )
    return GroqService(settings, client=client), client


def test_tts_uses_current_groq_payload_fields() -> None:
    service, client = make_service()

    result = service._synthesize_sync("A short receptionist reply.")

    assert result.startswith(b"RIFF")
    assert client.audio.speech.requests == [
        {
            "model": "canopylabs/orpheus-v1-english",
            "voice": "autumn",
            "input": "A short receptionist reply.",
            "response_format": "wav",
        }
    ]


def test_tts_splits_long_input_and_returns_one_wav() -> None:
    service, client = make_service()
    long_reply = "This is a sentence for the caller. " * 12

    result = service._synthesize_sync(long_reply)

    requests = client.audio.speech.requests
    assert len(requests) > 1
    assert all(
        0 < len(request["input"]) <= MAX_TTS_INPUT_CHARACTERS
        for request in requests
    )
    with wave.open(io.BytesIO(result), "rb") as wav_file:
        assert wav_file.getnframes() == 80 * len(requests)


def test_provider_body_logging_redacts_secrets_but_keeps_error() -> None:
    body = {
        "error": {"message": "model decommissioned", "code": "invalid_model"},
        "api_key": "placeholder-sensitive-value",
    }

    formatted = _format_provider_response_body(body)

    assert "model decommissioned" in formatted
    assert "invalid_model" in formatted
    assert "placeholder-sensitive-value" not in formatted
    assert "[REDACTED]" in formatted
