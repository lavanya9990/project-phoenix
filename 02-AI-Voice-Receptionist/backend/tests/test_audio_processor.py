import audioop
import base64
import io
import math
import struct
import wave

import pytest

from audio_processor import (
    AudioProcessingError,
    CallerTurnBuffer,
    decode_twilio_media,
    encode_mulaw_base64,
    pcm16_to_wav,
    wav_to_mulaw_8khz,
)


def make_pcm_tone(sample_rate: int, seconds: float, channels: int = 1) -> bytes:
    frames = []
    for index in range(int(sample_rate * seconds)):
        sample = int(8_000 * math.sin(2 * math.pi * 440 * index / sample_rate))
        frames.append(struct.pack("<h", sample) * channels)
    return b"".join(frames)


def make_wav(pcm: bytes, sample_rate: int, channels: int = 1) -> bytes:
    output = io.BytesIO()
    with wave.open(output, "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm)
    return output.getvalue()


def test_twilio_base64_mulaw_decodes_to_pcm16() -> None:
    pcm = make_pcm_tone(8_000, 0.02)
    mulaw = audioop.lin2ulaw(pcm, 2)
    decoded = decode_twilio_media(encode_mulaw_base64(mulaw))

    assert decoded == audioop.ulaw2lin(mulaw, 2)
    assert len(decoded) == len(pcm)


def test_invalid_base64_is_rejected() -> None:
    with pytest.raises(AudioProcessingError):
        decode_twilio_media("not valid base64!")


def test_stereo_16khz_wav_converts_to_raw_8khz_mulaw() -> None:
    wav_audio = make_wav(make_pcm_tone(16_000, 1.0, channels=2), 16_000, 2)
    mulaw = wav_to_mulaw_8khz(wav_audio)

    assert 7_990 <= len(mulaw) <= 8_010
    assert not mulaw.startswith(b"RIFF")


def test_caller_turn_buffer_emits_wav_after_silence() -> None:
    speech_pcm = struct.pack("<h", 3_000) * 160
    speech_frame = audioop.lin2ulaw(speech_pcm, 2)
    silence_frame = b"\xff" * 160
    payload = base64.b64encode(
        speech_frame * 10 + silence_frame * 35
    ).decode("ascii")

    completed = CallerTurnBuffer().add_media(payload)

    assert len(completed) == 1
    with wave.open(io.BytesIO(completed[0]), "rb") as wav_file:
        assert wav_file.getframerate() == 8_000
        assert wav_file.getnchannels() == 1
        assert wav_file.getsampwidth() == 2


def test_pcm16_to_wav_has_expected_format() -> None:
    wav_audio = pcm16_to_wav(b"\x00\x00" * 160)
    with wave.open(io.BytesIO(wav_audio), "rb") as wav_file:
        assert wav_file.getparams().nchannels == 1
        assert wav_file.getparams().framerate == 8_000

