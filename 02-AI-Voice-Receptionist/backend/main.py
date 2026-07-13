"""FastAPI entrypoint for the Twilio bidirectional voice receptionist."""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response, WebSocket
from fastapi.websockets import WebSocketDisconnect
from twilio.request_validator import RequestValidator
from twilio.twiml.voice_response import VoiceResponse

from audio_processor import (
    AudioProcessingError,
    CallerTurnBuffer,
    TWILIO_CHANNELS,
    TWILIO_SAMPLE_RATE,
    wav_to_twilio_payload,
)
from business_config import (
    APPOINTMENT_CONFIRMATION,
    APPOINTMENT_SAVE_ERROR,
    WELCOME_MESSAGE,
    build_system_prompt,
)
from call_session import CallSession
from groq_service import (
    GroqConfigurationError,
    GroqService,
    GroqServiceError,
    GroqSettings,
)
from lead_manager import LeadManager, LeadStorageError

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Phoenix AI Voice Receptionist")
groq_settings = GroqSettings.from_environment()
groq_service = GroqService(groq_settings)
lead_manager = LeadManager(BASE_DIR / "leads.json")


def _public_base_url() -> str:
    return os.getenv("PUBLIC_BASE_URL", "").strip().rstrip("/")


def _twilio_auth_token() -> str:
    return os.getenv("TWILIO_AUTH_TOKEN", "").strip()


def _public_http_url(path: str) -> str:
    return f"{_public_base_url()}{path}"


def _media_stream_url() -> str:
    base_url = _public_base_url()
    if not base_url:
        raise ValueError("PUBLIC_BASE_URL is not configured")

    parsed = urlsplit(base_url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("PUBLIC_BASE_URL must be a public HTTPS URL")

    stream_path = f"{parsed.path.rstrip('/')}/media-stream"
    return urlunsplit(("wss", parsed.netloc, stream_path, "", ""))


def _validate_signature(url: str, parameters: dict, signature: str) -> bool:
    auth_token = _twilio_auth_token()
    if not auth_token:
        logger.warning(
            "TWILIO_AUTH_TOKEN is unset; Twilio request validation is disabled"
        )
        return True
    if not signature:
        return False
    return RequestValidator(auth_token).validate(url, parameters, signature)


async def _validate_incoming_call(request: Request, form_data: dict) -> bool:
    signature = request.headers.get("x-twilio-signature", "")
    return _validate_signature(
        _public_http_url(request.url.path), form_data, signature
    )


def _validate_media_websocket(websocket: WebSocket) -> bool:
    signature = websocket.headers.get("x-twilio-signature", "")
    try:
        stream_url = _media_stream_url()
    except ValueError:
        return not _twilio_auth_token()

    if _validate_signature(stream_url, {}, signature):
        return True
    # Some proxy configurations preserve a trailing slash in Twilio's signed URL.
    return _validate_signature(f"{stream_url}/", {}, signature)


@app.get("/health")
async def health() -> dict[str, object]:
    return {
        "status": "ok",
        "groq_configured": groq_settings.is_complete,
        "public_url_configured": bool(_public_base_url()),
        "twilio_validation_enabled": bool(_twilio_auth_token()),
    }


@app.post("/incoming-call")
async def incoming_call(request: Request) -> Response:
    form = await request.form()
    form_data = {key: str(value) for key, value in form.multi_items()}
    if not await _validate_incoming_call(request, form_data):
        logger.warning("Rejected an incoming call with an invalid Twilio signature")
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    try:
        stream_url = _media_stream_url()
    except ValueError as exc:
        logger.error("Cannot create TwiML because PUBLIC_BASE_URL is invalid")
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    caller_phone = form_data.get("From", "")
    response = VoiceResponse()
    stream = response.connect().stream(url=stream_url)
    stream.parameter(name="callerPhone", value=caller_phone)
    return Response(content=str(response), media_type="application/xml")


async def _send_assistant_audio(
    websocket: WebSocket,
    session: CallSession,
    reply: str,
) -> None:
    wav_audio = await groq_service.synthesize(reply)
    payload = wav_to_twilio_payload(wav_audio)
    await websocket.send_json(
        {
            "event": "media",
            "streamSid": session.stream_sid,
            "media": {"payload": payload},
        }
    )
    await websocket.send_json(
        {
            "event": "mark",
            "streamSid": session.stream_sid,
            "mark": {"name": f"assistant-{len(session.conversation_history)}"},
        }
    )
    session.add_message("assistant", reply)


async def _process_caller_turn(
    websocket: WebSocket,
    session: CallSession,
    wav_audio: bytes,
) -> None:
    transcript = await groq_service.transcribe(wav_audio)
    if not transcript:
        logger.info("Ignoring an empty transcription for call %s", session.call_sid)
        return

    session.add_message("user", transcript)
    handled, prompt, completed = session.appointment_turn(transcript)

    if completed is not None:
        try:
            await asyncio.to_thread(
                lead_manager.save_completed_lead,
                completed,
                call_sid=session.call_sid,
                caller_phone=session.caller_phone,
            )
            reply = APPOINTMENT_CONFIRMATION
        except LeadStorageError:
            logger.error("Lead persistence failed for call %s", session.call_sid)
            reply = APPOINTMENT_SAVE_ERROR
    elif handled:
        if prompt is None:
            raise RuntimeError("Appointment flow did not produce a prompt")
        reply = prompt
    else:
        reply = await groq_service.chat(
            session.messages_for_chat(build_system_prompt())
        )

    await _send_assistant_audio(websocket, session, reply)


async def _turn_worker(
    websocket: WebSocket,
    session: CallSession,
    queue: asyncio.Queue[bytes | str | None],
) -> None:
    while True:
        item = await queue.get()
        try:
            if item is None:
                return
            if isinstance(item, str):
                await _send_assistant_audio(websocket, session, item)
            else:
                await _process_caller_turn(websocket, session, item)
        except (
            AudioProcessingError,
            GroqConfigurationError,
            GroqServiceError,
            RuntimeError,
        ) as exc:
            logger.error(
                "Voice turn failed for call %s (%s)",
                session.call_sid,
                type(exc).__name__,
            )
        finally:
            queue.task_done()


def _validate_start_format(start: dict) -> bool:
    media_format = start.get("mediaFormat", {})
    return (
        media_format.get("encoding") == "audio/x-mulaw"
        and int(media_format.get("sampleRate", 0)) == TWILIO_SAMPLE_RATE
        and int(media_format.get("channels", 0)) == TWILIO_CHANNELS
    )


@app.websocket("/media-stream")
async def media_stream(websocket: WebSocket) -> None:
    if not _validate_media_websocket(websocket):
        logger.warning("Rejected a media stream with an invalid Twilio signature")
        await websocket.close(code=1008)
        return

    await websocket.accept()
    turn_buffer = CallerTurnBuffer()
    queue: asyncio.Queue[bytes | str | None] = asyncio.Queue(maxsize=8)
    session: CallSession | None = None
    worker: asyncio.Task[None] | None = None
    received_stop = False

    try:
        while True:
            message = await websocket.receive_json()
            event = message.get("event")

            if event == "connected":
                logger.info("Twilio media WebSocket connected")
                continue

            if event == "start":
                start = message.get("start", {})
                if not _validate_start_format(start):
                    logger.warning("Closing stream with an unsupported audio format")
                    await websocket.close(code=1003)
                    return

                stream_sid = str(start.get("streamSid", ""))
                call_sid = str(start.get("callSid", ""))
                if not stream_sid or not call_sid:
                    logger.warning("Closing stream without required Twilio identifiers")
                    await websocket.close(code=1008)
                    return

                parameters = start.get("customParameters", {})
                session = CallSession(
                    call_sid=call_sid,
                    stream_sid=stream_sid,
                    caller_phone=str(parameters.get("callerPhone", "")),
                )
                worker = asyncio.create_task(
                    _turn_worker(websocket, session, queue)
                )
                queue.put_nowait(WELCOME_MESSAGE)
                logger.info("Started media stream for call %s", call_sid)
                continue

            if event == "media":
                if session is None:
                    logger.warning("Ignoring media received before the start event")
                    continue
                payload = str(message.get("media", {}).get("payload", ""))
                if not payload:
                    continue
                try:
                    completed_turns = turn_buffer.add_media(payload)
                except AudioProcessingError:
                    logger.warning("Ignoring an invalid media payload")
                    continue
                for completed_turn in completed_turns:
                    try:
                        queue.put_nowait(completed_turn)
                    except asyncio.QueueFull:
                        logger.warning("Dropping a caller turn because the queue is full")
                continue

            if event == "stop":
                received_stop = True
                flushed_turn = turn_buffer.flush()
                if flushed_turn is not None and not queue.full():
                    queue.put_nowait(flushed_turn)
                logger.info(
                    "Twilio media stream stopped for call %s",
                    session.call_sid if session else "unknown",
                )
                break

            if event in {"mark", "dtmf"}:
                logger.debug("Received Twilio %s event", event)
                continue

            logger.debug("Ignoring unsupported Twilio event: %s", event)

    except WebSocketDisconnect:
        logger.info(
            "Twilio media WebSocket disconnected for call %s",
            session.call_sid if session else "unknown",
        )
    except ValueError:
        logger.warning("Closing media stream after receiving invalid JSON")
    finally:
        if worker is not None:
            if received_stop:
                try:
                    queue.put_nowait(None)
                except asyncio.QueueFull:
                    worker.cancel()
                if not worker.cancelled():
                    try:
                        await asyncio.wait_for(worker, timeout=10)
                    except (asyncio.TimeoutError, WebSocketDisconnect):
                        worker.cancel()
            else:
                worker.cancel()
            await asyncio.gather(worker, return_exceptions=True)

