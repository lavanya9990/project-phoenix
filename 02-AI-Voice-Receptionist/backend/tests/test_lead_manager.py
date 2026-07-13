import json

import pytest

from business_config import APPOINTMENT_FIELDS
from lead_manager import LeadManager, LeadStorageError


def complete_appointment() -> dict[str, str]:
    return {
        "caller_name": "Test Caller",
        "phone_number": "+1 555 0100",
        "preferred_date": "Next Monday",
        "preferred_time": "10 AM",
        "requested_service": "Consultation",
    }


def test_completed_leads_are_appended_safely(tmp_path) -> None:
    destination = tmp_path / "leads.json"
    manager = LeadManager(destination)

    first = manager.save_completed_lead(
        complete_appointment(), call_sid="CA-first", caller_phone="+15550001"
    )
    second = manager.save_completed_lead(
        complete_appointment(), call_sid="CA-second", caller_phone="+15550002"
    )

    saved = json.loads(destination.read_text(encoding="utf-8"))
    assert [lead["id"] for lead in saved] == [first["id"], second["id"]]
    assert saved[0]["call_sid"] == "CA-first"
    assert saved[1]["status"] == "new"


def test_incomplete_lead_is_rejected(tmp_path) -> None:
    appointment = complete_appointment()
    appointment.pop(APPOINTMENT_FIELDS[-1])

    with pytest.raises(LeadStorageError, match="incomplete"):
        LeadManager(tmp_path / "leads.json").save_completed_lead(
            appointment, call_sid="CA-incomplete"
        )


def test_corrupt_existing_storage_is_not_overwritten(tmp_path) -> None:
    destination = tmp_path / "leads.json"
    destination.write_text("not-json", encoding="utf-8")

    with pytest.raises(LeadStorageError, match="unreadable"):
        LeadManager(destination).save_completed_lead(
            complete_appointment(), call_sid="CA-corrupt"
        )

    assert destination.read_text(encoding="utf-8") == "not-json"

