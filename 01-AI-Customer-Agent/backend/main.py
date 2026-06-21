from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


app = FastAPI(title="AI Customer Support Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


def get_bot_reply(user_input: str) -> str:
    message = user_input.lower()

    if "hour" in message or "open" in message:
        return "We are open Monday to Saturday from 9:00 AM to 7:00 PM. We are closed on Sundays."

    if "location" in message or "where" in message:
        return "We are located in Hyderabad. I can also help you get directions if needed."

    if "appointment" in message or "book" in message or "schedule" in message:
        return "Yes, we offer appointments. Please share your name, phone number, and preferred time."

    if "contact" in message or "support" in message or "phone" in message:
        return "You can contact our support team at support@example.com or call +91 98765 43210."

    return "Thanks for your question. I can help with business hours, location, appointments, and support contact details."


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    reply = get_bot_reply(request.message)
    return {"reply": reply}