"""Twilio audio decoding, caller-turn buffering, VAD, and TTS conversion."""

from __future__ import annotations

import audioop
import base64
import binascii
import io
import wave
from collections import deque

TWILIO_SAMPLE_RATE = 8_000
TWILIO_CHANNELS = 1
PCM_SAMPLE_WIDTH = 2
FRAME_DURATION_MS = 20
FRAME_BYTES_MULAW = TWILIO_SAMPLE_RATE * FRAME_DURATION_MS // 1_000


class AudioProcessingError(ValueError):
    """Raised when an audio payload cannot be decoded or converted safely."""


def decode_base64_mulaw(payload: str) -> bytes:
    """Decode a Twilio media payload into raw, headerless mu-law bytes."""
    try:
        return base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise AudioProcessingError("Invalid base64 media payload") from exc


def mulaw_to_pcm16(mulaw_audio: bytes) -> bytes:
    return audioop.ulaw2lin(mulaw_audio, PCM_SAMPLE_WIDTH)


def decode_twilio_media(payload: str) -> bytes:
    """Decode a base64 Twilio payload into 8 kHz, mono, 16-bit PCM."""
    return mulaw_to_pcm16(decode_base64_mulaw(payload))


def encode_mulaw_base64(mulaw_audio: bytes) -> str:
    """Encode raw, headerless mu-law bytes for a Twilio media message."""
    return base64.b64encode(mulaw_audio).decode("ascii")


def pcm16_to_wav(pcm_audio: bytes, sample_rate: int = TWILIO_SAMPLE_RATE) -> bytes:
    output = io.BytesIO()
    with wave.open(output, "wb") as wav_file:
        wav_file.setnchannels(TWILIO_CHANNELS)
        wav_file.setsampwidth(PCM_SAMPLE_WIDTH)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_audio)
    return output.getvalue()


def wav_to_mulaw_8khz(wav_audio: bytes) -> bytes:
    """Convert PCM WAV returned by TTS into Twilio-compatible raw mu-law."""
    try:
        with wave.open(io.BytesIO(wav_audio), "rb") as wav_file:
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            sample_rate = wav_file.getframerate()
            pcm_audio = wav_file.readframes(wav_file.getnframes())
    except (wave.Error, EOFError) as exc:
        raise AudioProcessingError("TTS response is not a readable PCM WAV") from exc

    if channels == 2:
        pcm_audio = audioop.tomono(pcm_audio, sample_width, 0.5, 0.5)
    elif channels != 1:
        raise AudioProcessingError("Only mono or stereo WAV audio is supported")

    if sample_width != PCM_SAMPLE_WIDTH:
        try:
            pcm_audio = audioop.lin2lin(
                pcm_audio, sample_width, PCM_SAMPLE_WIDTH
            )
        except audioop.error as exc:
            raise AudioProcessingError("Unsupported WAV sample width") from exc

    if sample_rate != TWILIO_SAMPLE_RATE:
        pcm_audio, _ = audioop.ratecv(
            pcm_audio,
            PCM_SAMPLE_WIDTH,
            TWILIO_CHANNELS,
            sample_rate,
            TWILIO_SAMPLE_RATE,
            None,
        )

    return audioop.lin2ulaw(pcm_audio, PCM_SAMPLE_WIDTH)


def wav_to_twilio_payload(wav_audio: bytes) -> str:
    return encode_mulaw_base64(wav_to_mulaw_8khz(wav_audio))


class CallerTurnBuffer:
    """Energy-based VAD that emits complete caller turns as 8 kHz PCM WAV."""

    def __init__(
        self,
        *,
        speech_threshold: int = 450,
        end_silence_ms: int = 400,
        minimum_speech_ms: int = 120,
        pre_roll_ms: int = 200,
        maximum_turn_ms: int = 15_000,
    ) -> None:
        self.speech_threshold = speech_threshold
        self.end_silence_frames = max(1, end_silence_ms // FRAME_DURATION_MS)
        self.minimum_speech_frames = max(1, minimum_speech_ms // FRAME_DURATION_MS)
        self.maximum_turn_frames = max(1, maximum_turn_ms // FRAME_DURATION_MS)
        self._pre_roll = deque(maxlen=max(1, pre_roll_ms // FRAME_DURATION_MS))
        self._pending = bytearray()
        self._active = bytearray()
        self._speaking = False
        self._speech_frames = 0
        self._silence_frames = 0
        self._suppressed_frames = 0

    def add_media(self, payload: str) -> list[bytes]:
        """Add one Twilio media payload and return zero or more completed WAVs."""
        self._pending.extend(decode_base64_mulaw(payload))
        completed: list[bytes] = []

        while len(self._pending) >= FRAME_BYTES_MULAW:
            frame = bytes(self._pending[:FRAME_BYTES_MULAW])
            del self._pending[:FRAME_BYTES_MULAW]
            if self._suppressed_frames > 0:
                self._suppressed_frames -= 1
                continue
            utterance = self._process_frame(frame)
            if utterance is not None:
                completed.append(utterance)

        return completed

    def ignore_dtmf(self, suppression_ms: int = 300) -> None:
        """Discard a current turn and briefly suppress keypad-tone audio."""
        self._pending.clear()
        self._reset_turn()
        self._suppressed_frames = max(
            1, suppression_ms // FRAME_DURATION_MS
        )

    def flush(self) -> bytes | None:
        """Flush a sufficiently long active turn when a stream stops."""
        self._pending.clear()
        if not self._speaking:
            self._reset_turn()
            return None
        return self._finish_turn()

    def _process_frame(self, mulaw_frame: bytes) -> bytes | None:
        pcm_frame = mulaw_to_pcm16(mulaw_frame)
        is_speech = audioop.rms(pcm_frame, PCM_SAMPLE_WIDTH) >= self.speech_threshold

        if not self._speaking:
            if not is_speech:
                self._pre_roll.append(mulaw_frame)
                return None

            self._speaking = True
            for frame in self._pre_roll:
                self._active.extend(frame)
            self._pre_roll.clear()
            self._active.extend(mulaw_frame)
            self._speech_frames = 1
            self._silence_frames = 0
            return None

        self._active.extend(mulaw_frame)
        if is_speech:
            self._speech_frames += 1
            self._silence_frames = 0
        else:
            self._silence_frames += 1

        active_frames = len(self._active) // FRAME_BYTES_MULAW
        if (
            self._silence_frames >= self.end_silence_frames
            or active_frames >= self.maximum_turn_frames
        ):
            return self._finish_turn()
        return None

    def _finish_turn(self) -> bytes | None:
        mulaw_audio = bytes(self._active)
        has_enough_speech = self._speech_frames >= self.minimum_speech_frames
        self._reset_turn()
        if not has_enough_speech:
            return None
        return pcm16_to_wav(mulaw_to_pcm16(mulaw_audio))

    def _reset_turn(self) -> None:
        self._active.clear()
        self._pre_roll.clear()
        self._speaking = False
        self._speech_frames = 0
        self._silence_frames = 0
