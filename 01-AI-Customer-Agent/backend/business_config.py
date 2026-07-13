"""Central configuration for the business represented by the chatbot."""

BUSINESS_NAME = "Phoenix Hospital"
BUSINESS_TYPE = "Hospital and healthcare provider"
BUSINESS_DESCRIPTION = (
    "Phoenix Hospital provides high-quality healthcare with experienced doctors "
    "and modern facilities."
)

ADDRESS = "123 Main Road, Hyderabad"

WORKING_HOURS = {
    "Monday-Friday": "9:00 AM - 7:00 PM",
    "Saturday": "9:00 AM - 2:00 PM",
    "Sunday": "Closed",
}

CONTACT = {
    "phone": "+91 9876543210",
    "email": "info@phoenixhospital.com",
    "website": "www.phoenixhospital.com",
}

SERVICES = [
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
    f"Hello! Welcome to {BUSINESS_NAME}. How can I assist you today? "
    "You can type or speak to book an appointment."
)


def format_working_hours() -> str:
    """Return business hours in a form suitable for customer-facing replies."""
    return "; ".join(
        f"{days}: {hours}" for days, hours in WORKING_HOURS.items()
    )


def format_contact_details() -> str:
    """Return all configured public contact methods."""
    return (
        f"email {CONTACT['email']}, phone {CONTACT['phone']}, "
        f"or website {CONTACT['website']}"
    )


FAQ = {
    "appointment": "Yes! I can help you book an appointment.",
    "timings": f"Our working hours are {format_working_hours()}.",
    "emergency": "Our emergency department is available 24/7.",
    "insurance": "We accept most major insurance providers.",
    "location": f"We are located at {ADDRESS}.",
}


def build_business_info() -> str:
    """Build the authoritative business context supplied to OpenAI."""
    return "\n".join(
        [
            f"Business name: {BUSINESS_NAME}",
            f"Business type: {BUSINESS_TYPE}",
            f"Description: {BUSINESS_DESCRIPTION}",
            f"Location: {ADDRESS}",
            f"Business hours: {format_working_hours()}",
            f"Support contact: {format_contact_details()}",
            f"Services: {', '.join(SERVICES)}",
            (
                "Appointments: Available. Ask the customer for their name, "
                "phone number, and preferred time."
            ),
        ]
    )


def get_public_business_config() -> dict:
    """Return business details that are safe and useful for the frontend."""
    return {
        "name": BUSINESS_NAME,
        "description": BUSINESS_DESCRIPTION,
        "address": ADDRESS,
        "working_hours": WORKING_HOURS,
        "contact": CONTACT,
        "services": SERVICES,
        "welcome_message": WELCOME_MESSAGE,
    }
