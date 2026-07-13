"""Async-friendly wrapper around Groq STT, chat, and TTS APIs."""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Any

from groq import Groq

logger = logging.getLogger(__name__)


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
        try:
            response = client.audio.speech.create(
                model=self.settings.tts_model,
                voice=self.settings.tts_voice,
                input=text,
                response_format="wav",
            )
            if hasattr(response, "read"):
                audio = response.read()
            elif hasattr(response, "content"):
                audio = response.content
            else:
                raise GroqServiceError("TTS response did not contain audio bytes")
            if not isinstance(audio, bytes) or not audio:
                raise GroqServiceError("TTS response was empty")
            return audio
        except (GroqConfigurationError, GroqServiceError):
            raise
        except Exception as exc:
            logger.error("Groq TTS request failed (%s)", type(exc).__name__)
            raise GroqServiceError("Speech synthesis failed") from exc

