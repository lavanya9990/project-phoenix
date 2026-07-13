"""Validated, locked, atomic JSON persistence for appointment leads."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping
from uuid import uuid4

from filelock import FileLock

from business_config import APPOINTMENT_FIELDS


class LeadStorageError(RuntimeError):
    """Raised when lead data cannot be validated or persisted safely."""


class LeadManager:
    def __init__(self, leads_file: Path) -> None:
        self.leads_file = leads_file.resolve()
        self.lock = FileLock(f"{self.leads_file}.lock")

    def save_completed_lead(
        self,
        appointment: Mapping[str, str],
        *,
        call_sid: str,
        caller_phone: str = "",
    ) -> dict[str, str]:
        missing = [
            field_name
            for field_name in APPOINTMENT_FIELDS
            if not str(appointment.get(field_name, "")).strip()
        ]
        if missing:
            raise LeadStorageError(
                f"Cannot save an incomplete lead; missing: {', '.join(missing)}"
            )

        record = {
            "id": str(uuid4()),
            **{
                field_name: str(appointment[field_name]).strip()
                for field_name in APPOINTMENT_FIELDS
            },
            "call_sid": call_sid,
            "incoming_caller_phone": caller_phone,
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "status": "new",
        }

        self.leads_file.parent.mkdir(parents=True, exist_ok=True)
        with self.lock:
            leads = self._read_existing_leads()
            leads.append(record)
            self._atomic_write(leads)
        return record

    def _read_existing_leads(self) -> list[dict]:
        if not self.leads_file.exists():
            return []
        try:
            with self.leads_file.open("r", encoding="utf-8") as source:
                data = json.load(source)
        except (OSError, json.JSONDecodeError) as exc:
            raise LeadStorageError("Existing lead storage is unreadable") from exc

        if not isinstance(data, list) or not all(
            isinstance(item, dict) for item in data
        ):
            raise LeadStorageError("Existing lead storage must contain a JSON list")
        return data

    def _atomic_write(self, leads: list[dict]) -> None:
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.leads_file.parent,
                prefix=f".{self.leads_file.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                json.dump(leads, temporary_file, indent=2, ensure_ascii=False)
                temporary_file.write("\n")
                temporary_file.flush()
                os.fsync(temporary_file.fileno())
            os.replace(temporary_path, self.leads_file)
        except OSError as exc:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            raise LeadStorageError("Could not persist lead storage") from exc

