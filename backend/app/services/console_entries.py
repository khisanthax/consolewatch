import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Select, desc, select
from sqlalchemy.orm import Session

from app.models.entities import ConsoleEntry, Printer
from app.schemas.console import MoonrakerNotificationIn
from app.services.classification import classify_message, level_for_message
from app.services.manual_sessions import copy_entry_to_active_sessions


def list_recent_entries(
    db: Session,
    *,
    printer_id: int | None = None,
    search: str | None = None,
    classification: str | None = None,
    source: str | None = None,
    level: str | None = None,
    limit: int = 100,
) -> list[ConsoleEntry]:
    bounded_limit = max(1, min(limit, 500))
    statement: Select[tuple[ConsoleEntry]] = select(ConsoleEntry)

    if printer_id is not None:
        statement = statement.where(ConsoleEntry.printer_id == printer_id)
    if search:
        statement = statement.where(ConsoleEntry.message.ilike(f"%{search}%"))
    if classification:
        statement = statement.where(ConsoleEntry.classification == classification)
    if source:
        statement = statement.where(ConsoleEntry.source == source)
    if level:
        statement = statement.where(ConsoleEntry.level == level)

    statement = statement.order_by(desc(ConsoleEntry.captured_at), desc(ConsoleEntry.id)).limit(bounded_limit)
    return list(db.scalars(statement).all())


def ingest_moonraker_notification(
    db: Session,
    *,
    printer: Printer,
    notification: MoonrakerNotificationIn,
    captured_at: datetime | None = None,
) -> list[ConsoleEntry]:
    captured_at = captured_at or datetime.now(UTC)
    raw_payload = notification.model_dump()
    entries = _entries_from_notification(printer, notification, captured_at, raw_payload)

    for entry in entries:
        db.add(entry)

    if entries:
        db.commit()
        for entry in entries:
            db.refresh(entry)
            copy_entry_to_active_sessions(db, entry)
        db.commit()

    return entries


def _entries_from_notification(
    printer: Printer,
    notification: MoonrakerNotificationIn,
    captured_at: datetime,
    raw_payload: dict[str, Any],
) -> list[ConsoleEntry]:
    method = notification.method
    params = notification.params
    raw_payload_json = json.dumps(raw_payload, separators=(",", ":"), default=str)

    if method == "notify_gcode_response" and params and isinstance(params[0], str):
        return [
            _build_entry(
                printer=printer,
                captured_at=captured_at,
                source="gcode_response",
                message=params[0],
                raw_payload_json=raw_payload_json,
            )
        ]

    if method in {"notify_klippy_ready", "notify_klippy_shutdown", "notify_klippy_disconnected"}:
        event_type = method.removeprefix("notify_klippy_")
        message = f"Klippy {event_type}"
        return [
            _build_entry(
                printer=printer,
                captured_at=captured_at,
                source="klippy_state",
                message=message,
                raw_payload_json=raw_payload_json,
                event_type=event_type,
            )
        ]

    if method == "notify_status_update" and params and isinstance(params[0], dict):
        return _status_update_entries(printer, captured_at, params[0], raw_payload_json)

    return []


def _status_update_entries(
    printer: Printer,
    captured_at: datetime,
    status: dict[str, Any],
    raw_payload_json: str,
) -> list[ConsoleEntry]:
    webhooks = status.get("webhooks")
    print_stats = status.get("print_stats")
    messages: list[tuple[str, str | None, str | None, str | None]] = []

    if isinstance(webhooks, dict) and "state" in webhooks:
        state = str(webhooks["state"])
        messages.append((f"Klippy webhooks state changed to {state}", state, state, None))

    if isinstance(print_stats, dict):
        print_state = str(print_stats["state"]) if "state" in print_stats else None
        filename = str(print_stats["filename"]) if print_stats.get("filename") else None
        if print_state or filename:
            detail = f"Print state changed to {print_state or 'unknown'}"
            if filename:
                detail = f"{detail} for {filename}"
            messages.append((detail, "print_state", print_state, filename))

    return [
        _build_entry(
            printer=printer,
            captured_at=captured_at,
            source="klippy_state",
            message=message,
            raw_payload_json=raw_payload_json,
            event_type=event_type,
            print_state=print_state,
            filename=filename,
        )
        for message, event_type, print_state, filename in messages
    ]


def _build_entry(
    *,
    printer: Printer,
    captured_at: datetime,
    source: str,
    message: str,
    raw_payload_json: str,
    event_type: str | None = None,
    print_state: str | None = None,
    filename: str | None = None,
) -> ConsoleEntry:
    classification = classify_message(message)
    return ConsoleEntry(
        printer_id=printer.id,
        captured_at=captured_at,
        source=source,
        level=level_for_message(message, classification),
        message=message,
        raw_payload_json=raw_payload_json,
        classification=classification,
        event_type=event_type,
        print_state=print_state,
        filename=filename,
    )
