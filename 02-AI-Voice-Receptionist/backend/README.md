# Phoenix AI Voice Receptionist

Standalone FastAPI foundation for a Twilio Programmable Voice receptionist using
bidirectional Media Streams and Groq speech, chat, and text-to-speech APIs.

## Current scope

Implemented:

- `GET /health`
- `POST /incoming-call`, returning `<Connect><Stream>` TwiML
- `WebSocket /media-stream`
- Twilio `connected`, `start`, `media`, `mark`, `dtmf`, and `stop` handling
- Twilio request-signature validation when `TWILIO_AUTH_TOKEN` is configured
- Base64, 8 kHz mu-law decoding and 16-bit PCM WAV construction
- Energy-based voice activity detection and caller-turn buffering
- Groq speech-to-text, chat, and WAV text-to-speech service calls
- WAV resampling and conversion to raw 8 kHz mu-law for Twilio playback
- Conversation history isolated to each WebSocket call
- Deterministic appointment capture for name, phone, date, time, and service
- File-locked, validated, atomic JSON lead persistence

This is a foundation, not a claim of a production-tested live voice agent. Unit
tests cover local conversion and state logic. A real Twilio call and real Groq
requests must still be exercised with your own accounts before deployment.

## Architecture

```text
Twilio caller audio (base64 mu-law/8000)
  -> CallerTurnBuffer and energy VAD
  -> completed 8 kHz PCM WAV caller turn
  -> Groq speech-to-text
  -> appointment state or Groq chat with per-call history
  -> Groq text-to-speech as WAV
  -> mono/resample/8 kHz mu-law conversion
  -> base64 Twilio media WebSocket message
  -> caller
```

## Setup

From `02-AI-Voice-Receptionist/backend`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

On macOS or Linux, activate with `source .venv/bin/activate` and copy the file
with `cp .env.example .env`.

Fill in `.env`. All model IDs are environment-controlled. Select a currently
supported Groq chat model and TTS voice for the configured TTS model. Do not
commit `.env`.

Run the API:

```powershell
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Check the local health endpoint:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

The health response reports only whether configuration is present; it never
returns credentials.

## Local ngrok and Twilio setup

1. Install ngrok and authenticate its CLI.
2. Keep FastAPI running on port 8000.
3. Start a tunnel:

   ```powershell
   ngrok http 8000
   ```

4. Copy the generated HTTPS forwarding URL, without a trailing slash, into:

   ```dotenv
   PUBLIC_BASE_URL=https://your-subdomain.ngrok-free.app
   ```

5. Restart FastAPI after changing `.env`.
6. In the Twilio Console, open the configured voice-capable phone number.
7. Under the incoming voice-call configuration, set:

   - Webhook method: `POST`
   - Webhook URL: `https://your-subdomain.ngrok-free.app/incoming-call`

8. Call the Twilio number and watch the FastAPI and ngrok logs.

The webhook generates a secure
`wss://your-subdomain.ngrok-free.app/media-stream` URL. Twilio Media Streams
requires secure WebSockets. If `TWILIO_AUTH_TOKEN` is populated, both the HTTP
webhook and WebSocket handshake must have a valid `X-Twilio-Signature`.

## Tests

```powershell
pytest -q
```

The tests do not contact Twilio or Groq and do not write to the included
`leads.json`.

## Lead storage

Completed appointment requests are written to `leads.json`. Writes use a
cross-process file lock, schema checks, a same-directory temporary file,
`fsync`, and atomic replacement. The runtime file and lock are ignored by Git
because leads contain personal information.

JSON storage is appropriate only for this foundation. A database with access
control, encryption, retention rules, and audit logging is needed before
handling production customer data.

## Known real-time limitations

- No live Twilio-to-Groq-to-Twilio phone call has been executed in this workspace.
- STT is turn-based, not a streaming transcription API. VAD waits for trailing
  silence before uploading a WAV utterance.
- The energy threshold is a starting value and must be tuned against real phone
  audio, background noise, accents, and carrier behavior.
- There is no barge-in yet. Caller speech does not send Twilio's `clear` event to
  interrupt already-buffered assistant audio.
- TTS audio is sent as one media payload and buffered by Twilio. Chunk pacing,
  playback marks, cancellation, retries, and latency metrics need live testing.
- Provider timeouts, retry policies, call-duration limits, rate limits, and
  production observability are not yet implemented.
- Appointment answers are collected sequentially as spoken text. Date, time,
  service, and phone normalization still require business-specific validation.

## Official protocol references

- Twilio Media Streams messages:
  https://www.twilio.com/docs/voice/media-streams/websocket-messages
- Twilio `<Stream>` TwiML:
  https://www.twilio.com/docs/voice/twiml/stream
- Twilio request validation:
  https://www.twilio.com/docs/usage/security
- Groq speech-to-text:
  https://console.groq.com/docs/speech-to-text
- Groq text-to-speech:
  https://console.groq.com/docs/text-to-speech

