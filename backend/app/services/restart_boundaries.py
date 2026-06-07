from datetime import timedelta

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.entities import ConsoleEntry, RestartBoundary

SUPPRESSION_WINDOW = timedelta(seconds=30)


def detect_boundary_type(entry: ConsoleEntry) -> tuple[str, str | None] | None:
    message = entry.message.lower()

    if entry.source == "klippy_state" and entry.event_type in {"ready", "shutdown", "disconnected"}:
        return f"klippy_{entry.event_type}", entry.event_type
    if "firmware_restart" in message:
        return "firmware_restart", "restart_requested"
    if "restart" in message and "print state" not in message:
        return "restart", "restart_requested"
    if entry.classification == "disconnect":
        return "disconnect", "disconnected"
    if entry.classification == "reconnect":
        return "reconnect", "ready"
    if "mcu" in message and "reconnect" in message:
        return "mcu_reconnect", "ready"

    return None


def create_boundary_for_entry(db: Session, entry: ConsoleEntry) -> RestartBoundary | None:
    detected = detect_boundary_type(entry)
    if detected is None:
        return None

    boundary_type, new_state = detected
    existing = _recent_duplicate(db, entry, boundary_type)
    if existing is not None:
        entry.restart_boundary_id = existing.id
        return existing

    previous = db.scalar(
        select(RestartBoundary)
        .where(RestartBoundary.printer_id == entry.printer_id)
        .order_by(desc(RestartBoundary.detected_at), desc(RestartBoundary.id))
        .limit(1)
    )
    boundary = RestartBoundary(
        printer_id=entry.printer_id,
        boundary_type=boundary_type,
        detected_at=entry.captured_at,
        message=entry.message,
        previous_state=previous.new_state if previous else None,
        new_state=new_state,
        raw_payload_json=entry.raw_payload_json,
    )
    db.add(boundary)
    db.flush()
    entry.restart_boundary_id = boundary.id
    return boundary


def _recent_duplicate(db: Session, entry: ConsoleEntry, boundary_type: str) -> RestartBoundary | None:
    earliest = entry.captured_at - SUPPRESSION_WINDOW
    latest = entry.captured_at + SUPPRESSION_WINDOW
    return db.scalar(
        select(RestartBoundary)
        .where(
            RestartBoundary.printer_id == entry.printer_id,
            RestartBoundary.boundary_type == boundary_type,
            RestartBoundary.detected_at >= earliest,
            RestartBoundary.detected_at <= latest,
        )
        .order_by(desc(RestartBoundary.detected_at), desc(RestartBoundary.id))
        .limit(1)
    )
