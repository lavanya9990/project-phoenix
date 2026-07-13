"""Single source of truth for all customer-facing business information."""

BUSINESS_NAME = "Phoenix Hospital"
BUSINESS_TYPE = "Hospital and healthcare provider"
BUSINESS_DESCRIPTION = (
    "Phoenix Hospital provides high-quality healthcare with experienced doctors "
    "and modern facilities."
)
BUSINESS_LOCATION = "123 Main Road, Hyderabad"

BUSINESS_HOURS = {
    "Monday-Friday": "9:00 AM - 7:00 PM",
    "Saturday": "9:00 AM - 2:00 PM",
    "Sunday": "Closed",
}

BUSINESS_CONTACT = {
    "phone": "+91 9876543210",
    "email": "info@phoenixhospital.com",
    "website": "www.phoenixhospital.com",
}

BUSINESS_SERVICES = [
    "General Physician",
    "Cardiology",
    "Orthopedics",
    "Dermatology",
    "Pediatrics",
    "Neurology",
    "ENT",
    "Emergency Care",
]

WELCOME_MESSAGE = (
    f"Hello, thank you for calling {BUSINESS_NAME}. "
    "How may I help you today?"
)

APPOINTMENT_FIELDS = (
    "caller_name",
    "phone_number",
    "preferred_date",
    "preferred_time",
    "requested_service",
)

APPOINTMENT_PROMPTS = {
    "caller_name": "May I have your name, please?",
    "phone_number": "What phone number should our team use to contact you?",
    "preferred_date": "What date would you prefer for the appointment?",
    "preferred_time": "What time would you prefer?",
    "requested_service": "Which service would you like to book?",
}

APPOINTMENT_CONFIRMATION = (
    "Thank you. Your appointment request has been recorded, and our team "
    "will contact you to confirm it."
)
APPOINTMENT_SAVE_ERROR = (
    "I am sorry, but I could not save the appointment request. "
    "Please contact our team directly."
)


def format_business_hours() -> str:
    return "; ".join(
        f"{days}: {hours}" for days, hours in BUSINESS_HOURS.items()
    )


def format_business_contact() -> str:
    return (
        f"phone {BUSINESS_CONTACT['phone']}, "
        f"email {BUSINESS_CONTACT['email']}, "
        f"website {BUSINESS_CONTACT['website']}"
    )


def build_system_prompt() -> str:
    """Build the business-grounded prompt used by the configured chat model."""
    return f"""
You are the concise, friendly voice receptionist for {BUSINESS_NAME}.

Business type: {BUSINESS_TYPE}
Description: {BUSINESS_DESCRIPTION}
Location: {BUSINESS_LOCATION}
Hours: {format_business_hours()}
Contact: {format_business_contact()}
Services: {', '.join(BUSINESS_SERVICES)}

Rules:
- Use only the business information above.
- Keep answers brief and natural because they will be spoken over a phone call.
- Do not use markdown, lists, or URLs unless the caller specifically asks for one.
- Do not invent prices, availability, medical advice, or business policies.
- The application handles appointment field collection. If a caller asks to book,
  acknowledge that the receptionist can collect an appointment request.
- If the answer is unknown, offer to have the business team follow up.
""".strip()

