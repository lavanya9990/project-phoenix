"""Async-friendly wrapper around Groq STT, chat, and TTS APIs."""

from __future__ import annotations

import asyncio
import io
import json
import logging
import os
import re
import wave
from dataclasses import dataclass
from typing import Any

from groq import APIStatusError, Groq

logger = logging.getLogger(__name__)

MAX_TTS_INPUT_CHARACTERS = 200


class GroqConfigurationError(RuntimeError):
    """Raised when a required Groq environment setting is absent."""


class GroqServiceError(RuntimeError):
    """Raised when a Groq operation fails without exposing provider details."""


@dataclass(frozen=True)
class GroqSettings:
    api_key: str
    stt_model: str
    chat_model: str
    tts_model: str
    tts_voice: str

    @classmethod
    def from_environment(cls) -> "GroqSettings":
        return cls(
            api_key=os.getenv("GROQ_API_KEY", "").strip(),
            stt_model=os.getenv(
                "GROQ_STT_MODEL", "whisper-large-v3-turbo"
            ).strip(),
            chat_model=os.getenv("GROQ_CHAT_MODEL", "").strip(),
            tts_model=os.getenv(
                "GROQ_TTS_MODEL", "canopylabs/orpheus-v1-english"
            ).strip(),
            tts_voice=os.getenv("GROQ_TTS_VOICE", "").strip(),
        )

    @property
    def is_complete(self) -> bool:
        return all(
            (
                self.api_key,
                self.stt_model,
                self.chat_model,
                self.tts_model,
                self.tts_voice,
            )
        )

    def validate(self) -> None:
        missing = [
            variable
            for variable, value in (
                ("GROQ_API_KEY", self.api_key),
                ("GROQ_STT_MODEL", self.stt_model),
                ("GROQ_CHAT_MODEL", self.chat_model),
                ("GROQ_TTS_MODEL", self.tts_model),
                ("GROQ_TTS_VOICE", self.tts_voice),
            )
            if not value
        ]
        if missing:
            raise GroqConfigurationError(
                f"Missing required Groq configuration: {', '.join(missing)}"
            )


class GroqService:
    def __init__(
        self,
        settings: GroqSettings | None = None,
        *,
        client: Any | None = None,
    ) -> None:
        self.settings = settings or GroqSettings.from_environment()
        self._client = client
        if self._client is None and self.settings.api_key:
            self._client = Groq(api_key=self.settings.api_key)

    async def transcribe(self, wav_audio: bytes) -> str:
        return await asyncio.to_thread(self._transcribe_sync, wav_audio)

    async def chat(self, messages: list[dict[str, Any]]) -> str:
        return await asyncio.to_thread(self._chat_sync, messages)

    async def synthesize(self, text: str) -> bytes:
        return await asyncio.to_thread(self._synthesize_sync, text)

    def _require_client(self) -> Any:
        self.settings.validate()
        if self._client is None:
            raise GroqConfigurationError("Groq client is not initialized")
        return self._client

    def _transcribe_sync(self, wav_audio: bytes) -> str:
        client = self._require_client()
        try:
            response = client.audio.transcriptions.create(
                file=("caller-turn.wav", wav_audio),
                model=self.settings.stt_model,
                response_format="json",
                temperature=0.0,
            )
            return response.text.strip()
        except GroqConfigurationError:
            raise
        except Exception as exc:
            logger.error("Groq STT request failed (%s)", type(exc).__name__)
            raise GroqServiceError("Speech transcription failed") from exc

    def _chat_sync(self, messages: list[dict[str, Any]]) -> str:
        client = self._require_client()
        try:
            response = client.chat.completions.create(
                model=self.settings.chat_model,
                messages=messages,
                temperature=0.2,
                max_completion_tokens=180,
            )
            content = response.choices[0].message.content
            if not content:
                raise GroqServiceError("Chat model returned an empty response")
            return content.strip()
        except (GroqConfigurationError, GroqServiceError):
            raise
        except Exception as exc:
            logger.error("Groq chat request failed (%s)", type(exc).__name__)
            raise GroqServiceError("Chat generation failed") from exc

    def _synthesize_sync(self, text: str) -> bytes:
        client = self._require_client()
        wav_parts: list[bytes] = []
        try:
            for text_chunk in _split_tts_input(text):
                response = client.audio.speech.create(
                    model=self.settings.tts_model,
                    voice=self.settings.tts_voice,
                    input=text_chunk,
                    response_format="wav",
                )
                wav_parts.append(_read_binary_response(response))
            return _merge_wav_parts(wav_parts)
        except (GroqConfigurationError, GroqServiceError):
            raise
        except APIStatusError as exc:
            logger.error(
                "Groq TTS request failed status=%s response_body=%s",
                exc.status_code,
                _format_provider_response_body(exc.body),
            )
            raise GroqServiceError("Speech synthesis failed") from exc
        except Exception as exc:
            logger.error("Groq TTS request failed (%s)", type(exc).__name__)
            raise GroqServiceError("Speech synthesis failed") from exc


def _split_tts_input(text: str) -> list[str]:
    """Split spoken text to satisfy Groq Orpheus's 200-character limit."""
    remaining = " ".join(text.split())
    if not remaining:
        raise GroqServiceError("TTS input was empty")

    chunks: list[str] = []
    while len(remaining) > MAX_TTS_INPUT_CHARACTERS:
        candidate = remaining[: MAX_TTS_INPUT_CHARACTERS + 1]
        split_at = max(
            candidate.rfind(boundary)
            for boundary in (". ", "? ", "! ", "; ", ", ", " ")
        )
        if split_at <= 0:
            split_at = MAX_TTS_INPUT_CHARACTERS
        else:
            split_at += 1
        chunks.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()

    if remaining:
        chunks.append(remaining)
    return chunks


def _read_binary_response(response: Any) -> bytes:
    if hasattr(response, "read"):
        audio = response.read()
    elif hasattr(response, "content"):
        audio = response.content
    else:
        raise GroqServiceError("TTS response did not contain audio bytes")
    if not isinstance(audio, bytes) or not audio:
        raise GroqServiceError("TTS response was empty")
    return audio


def _merge_wav_parts(wav_parts: list[bytes]) -> bytes:
    if not wav_parts:
        raise GroqServiceError("TTS did not produce any WAV audio")
    if len(wav_parts) == 1:
        return wav_parts[0]

    output = io.BytesIO()
    expected_format: tuple[int, int, int, str] | None = None
    with wave.open(output, "wb") as destination:
        for wav_part in wav_parts:
            try:
                with wave.open(io.BytesIO(wav_part), "rb") as source:
                    audio_format = (
                        source.getnchannels(),
                        source.getsampwidth(),
                        source.getframerate(),
                        source.getcomptype(),
                    )
                    if expected_format is None:
                        expected_format = audio_format
                        destination.setnchannels(audio_format[0])
                        destination.setsampwidth(audio_format[1])
                        destination.setframerate(audio_format[2])
                        destination.setcomptype(audio_format[3], "not compressed")
                    elif audio_format != expected_format:
                        raise GroqServiceError(
                            "Groq returned inconsistent WAV formats"
                        )
                    destination.writeframes(
                        source.readframes(source.getnframes())
                    )
            except wave.Error as exc:
                raise GroqServiceError("Groq returned invalid WAV audio") from exc
    return output.getvalue()


def _format_provider_response_body(body: Any) -> str:
    """Serialize the complete provider body while redacting secret-like fields."""
    def redact(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: (
                    "[REDACTED]"
                    if any(
                        marker in key.casefold()
                        for marker in ("api_key", "authorization", "token", "secret")
                    )
                    else redact(item)
                )
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [redact(item) for item in value]
        return value

    try:
        serialized = json.dumps(redact(body), ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        serialized = str(body)
    return re.sub(r"gsk_[A-Za-z0-9_-]+", "[REDACTED]", serialized)

