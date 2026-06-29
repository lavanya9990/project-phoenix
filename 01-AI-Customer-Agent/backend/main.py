import json
import os
import re
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel


load_dotenv()

app = FastAPI(title="AI Customer Support Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

# If API key is empty, app will directly use demo mode.
client = OpenAI() if OPENAI_API_KEY else None

LEADS_FILE = Path("leads.json")


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


BUSINESS_INFO = """
Business name: Phoenix Demo Business
Business type: Small service business
Location: Hyderabad, India
Business hours: Monday to Saturday, 9:00 AM to 7:00 PM
Closed: Sunday
Support email: support@example.com
Phone: +91 98765 43210
Appointments: Available. Ask customer for name, phone number, and preferred time.
"""


booking_state = {
    "active": False,
    "offered_booking": False,
    "step": None,
    "lead": {},
}


def load_leads() -> list[dict]:
    if not LEADS_FILE.exists():
        return []

    try:
        with open(LEADS_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError:
        return []


def save_leads(leads_data: list[dict]) -> None:
    with open(LEADS_FILE, "w", encoding="utf-8") as file:
        json.dump(leads_data, file, indent=2)


leads = load_leads()


def is_start_booking_intent(user_input: str) -> bool:
    message = user_input.lower().strip()

    start_phrases = [
        "i want to book",
        "book an appointment",
        "book appointment",
        "book now",
        "appointment booking",
        "schedule an appointment",
        "reserve appointment",
        "book meeting",
        "schedule meeting",
        "i need an appointment",
        "i want appointment",
    ]

    return any(phrase in message for phrase in start_phrases)


def is_appointment_faq(user_input: str) -> bool:
    message = user_input.lower().strip()

    faq_phrases = [
        "do you offer appointments",
        "appointments available",
        "do you have appointments",
        "can i get an appointment",
        "are appointments available",
    ]

    return any(phrase in message for phrase in faq_phrases)


def is_booking_confirmation(user_input: str) -> bool:
    message = user_input.lower().strip()

    confirmation_words = [
        "yes",
        "yeah",
        "yep",
        "ok",
        "okay",
        "sure",
        "book",
        "book now",
        "appointment",
        "start",
        "continue",
    ]

    return message in confirmation_words


def is_booking_rejection(user_input: str) -> bool:
    message = user_input.lower().strip()

    rejection_words = [
        "no",
        "nope",
        "not now",
        "later",
        "cancel",
    ]

    return message in rejection_words


def looks_like_faq(user_input: str) -> bool:
    message = user_input.lower().strip()

    faq_words = [
        "where",
        "location",
        "hour",
        "hours",
        "open",
        "contact",
        "support",
        "phone",
        "email",
        "business",
        "appointment",
    ]

    return "?" in message or any(word in message for word in faq_words)


def is_valid_name(name: str) -> bool:
    cleaned_name = name.strip()

    invalid_names = [
        "yes",
        "no",
        "ok",
        "okay",
        "sure",
        "book",
        "appointment",
        "hi",
        "hello",
    ]

    if cleaned_name.lower() in invalid_names:
        return False

    if looks_like_faq(cleaned_name):
        return False

    if len(cleaned_name) < 2:
        return False

    if len(cleaned_name.split()) > 4:
        return False

    return bool(re.search(r"[A-Za-z]", cleaned_name))


def normalize_phone(phone: str) -> str:
    return re.sub(r"\D", "", phone)


def is_valid_phone(phone: str) -> bool:
    cleaned_phone = normalize_phone(phone)
    return len(cleaned_phone) >= 10


def reset_booking_state() -> None:
    booking_state["active"] = False
    booking_state["offered_booking"] = False
    booking_state["step"] = None
    booking_state["lead"] = {}


def handle_booking_flow(user_input: str) -> str:
    message = user_input.strip()

    if message.lower() in ["cancel", "stop", "exit"]:
        reset_booking_state()
        return "Appointment booking cancelled. How else can I help you?"

    if not booking_state["active"]:
        booking_state["active"] = True
        booking_state["offered_booking"] = False
        booking_state["step"] = "name"
        booking_state["lead"] = {}
        return "Sure, I can help you book an appointment. Please share your name."

    if booking_state["step"] == "name":
        if not is_valid_name(message):
            return "You are currently booking an appointment. Please share your name, or type cancel."

        booking_state["lead"]["name"] = message
        booking_state["step"] = "phone"
        return f"Thanks {message}. Please share your phone number."

    if booking_state["step"] == "phone":
        if not is_valid_phone(message):
            return "Please enter a valid phone number with at least 10 digits."

        booking_state["lead"]["phone"] = normalize_phone(message)
        booking_state["step"] = "preferred_time"
        return "Great. What is your preferred appointment time?"

    if booking_state["step"] == "preferred_time":
        if looks_like_faq(message):
            return (
                "Please share your preferred appointment time, like "
                "'tomorrow evening' or 'Monday 2 PM'. You can type cancel to stop booking."
            )

        if len(message) < 3:
            return "Please enter a valid preferred time, like 'tomorrow evening' or 'Monday 2 PM'."

        booking_state["lead"]["preferred_time"] = message
        booking_state["lead"]["created_at"] = datetime.now().isoformat(timespec="seconds")
        booking_state["lead"]["status"] = "new"

        leads.append(booking_state["lead"].copy())
        save_leads(leads)

        customer_name = booking_state["lead"].get("name", "there")
        reset_booking_state()

        return (
            f"Thank you, {customer_name}. Your appointment request has been recorded. "
            "Our team will contact you soon."
        )

    reset_booking_state()
    return "Something went wrong while booking the appointment. Please try again."


def get_demo_reply(user_input: str) -> str:
    message = user_input.lower().strip()

    if "hour" in message or "open" in message:
        return "Demo mode: We are open Monday to Saturday from 9:00 AM to 7:00 PM. We are closed on Sundays."

    if "location" in message or "where" in message:
        return "Demo mode: We are located in Hyderabad, India."

    if "contact" in message or "support" in message or "phone" in message or "email" in message:
        return "Demo mode: You can contact support at support@example.com or call +91 98765 43210."

    return "Demo mode: I can help with business hours, location, appointments, and support contact details."


def get_ai_reply(user_input: str) -> str:
    # If booking is already active, continue only booking flow.
    if booking_state["active"]:
        return handle_booking_flow(user_input)

    # If bot offered appointment booking, user can reply yes/book/no.
    if booking_state["offered_booking"]:
        if is_booking_confirmation(user_input):
            booking_state["offered_booking"] = False
            return handle_booking_flow("book appointment")

        if is_booking_rejection(user_input):
            reset_booking_state()
            return "No problem. I can also help with business hours, location, and contact details."

        # If user asks another FAQ instead of saying yes/no, answer normally.
        booking_state["offered_booking"] = False
        return get_demo_reply(user_input)

    # Appointment FAQ should not directly start booking.
    if is_appointment_faq(user_input):
        booking_state["offered_booking"] = True
        return "Yes, appointments are available. Would you like to book one now? Reply Yes or Book."

    # Direct booking request should start booking.
    if is_start_booking_intent(user_input):
        return handle_booking_flow(user_input)

    # If no API key is available, use demo reply directly.
    if client is None:
        return get_demo_reply(user_input)

    # Try OpenAI if API key is available.
    try:
        response = client.responses.create(
            model=MODEL_NAME,
            instructions=f"""
You are a friendly AI customer support assistant for a business.

Use only the business information below to answer customer questions.

{BUSINESS_INFO}

Rules:
- Keep replies short and helpful.
- If the user wants to book an appointment, tell them you can help with appointment booking.
- If you do not know the answer, say you will connect them to a human support team.
- Do not make up business details.
""",
            input=user_input,
        )

        return response.output_text

    except Exception as error:
        print("AI error:", error)
        return get_demo_reply(user_input)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/leads")
def get_leads():
    return {
        "count": len(leads),
        "leads": leads,
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    reply = get_ai_reply(request.message)
    return {"reply": reply}