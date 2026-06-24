import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel


load_dotenv()

app = FastAPI(title="AI Customer Support Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI() if OPENAI_API_KEY else None


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


def get_demo_reply(user_input: str) -> str:
    message = user_input.lower()

    if "hour" in message or "open" in message:
        return "Demo mode: We are open Monday to Saturday from 9:00 AM to 7:00 PM. We are closed on Sundays."

    if "location" in message or "where" in message:
        return "Demo mode: We are located in Hyderabad, India."

    if "appointment" in message or "book" in message or "schedule" in message:
        return "Demo mode: Yes, appointments are available. Please share your name, phone number, and preferred time."

    if "contact" in message or "support" in message or "phone" in message:
        return "Demo mode: You can contact support at support@example.com or call +91 98765 43210."

    return "Demo mode: I can help with business hours, location, appointments, and support contact details."


def get_ai_reply(user_input: str) -> str:
    if client is None:
        return get_demo_reply(user_input)

    try:
        response = client.responses.create(
            model=MODEL_NAME,
            instructions=f"""
You are a friendly AI customer support assistant for a business.

Use only the business information below to answer customer questions.

{BUSINESS_INFO}

Rules:
- Keep replies short and helpful.
- If the user wants to book an appointment, ask for name, phone number, and preferred time.
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


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    reply = get_ai_reply(request.message)
    return {"reply": reply}