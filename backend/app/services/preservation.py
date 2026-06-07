from datetime import timedelta

from sqlalchemy import Select, desc, func, select
from sqlalchemy.orm import Session

from app.models.entities import (
    ConsoleEntry,
    DetectedEvent,
    PreservedConsoleCapture,
    PreservedConsoleEntry,
    Printer,
    utc_now,
)

PRE_WINDOW = timedelta(minutes=30)
POST_WINDOW = timedelta(minutes=30)

TRIGGER_CLASSIFICATIONS = {
    "warning",
    "error",
    "shutdown",
    "disconnect",
    "firmware_restart",
    "heater",
    "thermal",
    "adc",
    "mcu",
    "canbus",
    "probe",
    "endstop",
    "serial",
    "timer",
    "print_failed",
    "print_cancelled",
}

TRIGGER_MESSAGE_MARKERS = (
    "shutdown",
    "adc out of range",
    "mcu",
    "lost communication",
    "timer too close",
    "heater",
    "thermal",
    "endstop",
    "probe",
    "canbus",
    "can ",
    "serial",
    "firmware_restart",
    "restart",
    "failed",
    "cancelled",
    "error",
)


def process_entry_for_preservation(db: Session, entry: ConsoleEntry) -> PreservedConsoleCapture | None:
    trigger_type = trigger_type_for_entry(entry)
    if trigger_type is None:
        _copy_entry_to_open_captures(db, entry)
        return None

    capture = _find_open_capture(db, entry)
    if capture is None:
        capture = PreservedConsoleCapture(
            printer_id=entry.printer_id,
            trigger_type=trigger_type,
            trigger_reason=f"Matched {trigger_type} preservation rule",
            trigger_message=entry.message,
            triggered_at=entry.captured_at,
            started_at=entry.captured_at - PRE_WINDOW,
            ended_at=entry.captured_at + POST_WINDOW,
            status="collecting",
        )
        db.add(capture)
        db.flush()
    else:
        capture.ended_at = max(capture.ended_at, entry.captured_at + POST_WINDOW)
        capture.updated_at = utc_now()

    detected = DetectedEvent(
        printer_id=entry.printer_id,
        captured_at=entry.captured_at,
        event_type=trigger_type,
        severity=entry.level,
        message=entry.message,
        raw_payload_json=entry.raw_payload_json,
        related_capture_id=capture.id,
    )
    db.add(detected)
    db.flush()

    _copy_window_entries(db, capture, trigger_entry_id=entry.id)
    db.commit()
    db.refresh(capture)
    return capture


def trigger_type_for_entry(entry: ConsoleEntry) -> str | None:
    if entry.classification in TRIGGER_CLASSIFICATIONS:
        return entry.classification
    if entry.level in {"error", "warning"}:
        return entry.level
    normalized = entry.message.lower()
    for marker in TRIGGER_MESSAGE_MARKERS:
        if marker in normalized:
            return marker.strip().replace(" ", "_")
    return None


def list_captures(db: Session, *, printer_id: int | None = None, limit: int = 100) -> list[PreservedConsoleCapture]:
    bounded_limit = max(1, min(limit, 500))
    statement = select(PreservedConsoleCapture)
    if printer_id is not None:
        statement = statement.where(PreservedConsoleCapture.printer_id == printer_id)
    statement = statement.order_by(desc(PreservedConsoleCapture.triggered_at), desc(PreservedConsoleCapture.id)).limit(
        bounded_limit
    )
    return list(db.scalars(statement).all())


def get_capture(db: Session, capture_id: int) -> PreservedConsoleCapture | None:
    return db.get(PreservedConsoleCapture, capture_id)


def list_capture_entries(
    db: Session,
    *,
    capture_id: int,
    search: str | None = None,
    classification: str | None = None,
    source: str | None = None,
    level: str | None = None,
    limit: int = 500,
) -> list[PreservedConsoleEntry]:
    bounded_limit = max(1, min(limit, 1000))
    statement: Select[tuple[PreservedConsoleEntry]] = select(PreservedConsoleEntry).where(
        PreservedConsoleEntry.preserved_capture_id == capture_id
    )
    if search:
        statement = statement.where(PreservedConsoleEntry.message.ilike(f"%{search}%"))
    if classification:
        statement = statement.where(PreservedConsoleEntry.classification == classification)
    if source:
        statement = statement.where(PreservedConsoleEntry.source == source)
    if level:
        statement = statement.where(PreservedConsoleEntry.level == level)
    statement = statement.order_by(PreservedConsoleEntry.captured_at.asc(), PreservedConsoleEntry.id.asc()).limit(
        bounded_limit
    )
    return list(db.scalars(statement).all())


def detected_events_for_capture(db: Session, capture_id: int) -> list[DetectedEvent]:
    return list(
        db.scalars(
            select(DetectedEvent)
            .where(DetectedEvent.related_capture_id == capture_id)
            .order_by(DetectedEvent.captured_at.asc(), DetectedEvent.id.asc())
        ).all()
    )


def attach_capture_metadata(db: Session, capture: PreservedConsoleCapture):
    setattr(capture, "entry_count", entry_count(db, capture.id))
    printer = db.get(Printer, capture.printer_id)
    setattr(capture, "printer_name", printer.name if printer else None)
    return capture


def entry_count(db: Session, capture_id: int) -> int:
    return int(
        db.scalar(
            select(func.count())
            .select_from(PreservedConsoleEntry)
            .where(PreservedConsoleEntry.preserved_capture_id == capture_id)
        )
        or 0
    )


def _find_open_capture(db: Session, entry: ConsoleEntry) -> PreservedConsoleCapture | None:
    return db.scalar(
        select(PreservedConsoleCapture)
        .where(
            PreservedConsoleCapture.printer_id == entry.printer_id,
            PreservedConsoleCapture.status == "collecting",
            PreservedConsoleCapture.started_at <= entry.captured_at,
            PreservedConsoleCapture.ended_at >= entry.captured_at,
        )
        .order_by(desc(PreservedConsoleCapture.triggered_at), desc(PreservedConsoleCapture.id))
        .limit(1)
    )


def _copy_entry_to_open_captures(db: Session, entry: ConsoleEntry) -> None:
    captures = db.scalars(
        select(PreservedConsoleCapture).where(
            PreservedConsoleCapture.printer_id == entry.printer_id,
            PreservedConsoleCapture.started_at <= entry.captured_at,
            PreservedConsoleCapture.ended_at >= entry.captured_at,
        )
    ).all()
    for capture in captures:
        _copy_entry(db, capture, entry, is_trigger_entry=False)


def _copy_window_entries(db: Session, capture: PreservedConsoleCapture, *, trigger_entry_id: int) -> None:
    entries = db.scalars(
        select(ConsoleEntry)
        .where(
            ConsoleEntry.printer_id == capture.printer_id,
            ConsoleEntry.captured_at >= capture.started_at,
            ConsoleEntry.captured_at <= capture.ended_at,
        )
        .order_by(ConsoleEntry.captured_at.asc(), ConsoleEntry.id.asc())
    ).all()
    for entry in entries:
        _copy_entry(db, capture, entry, is_trigger_entry=entry.id == trigger_entry_id)


def _copy_entry(
    db: Session,
    capture: PreservedConsoleCapture,
    entry: ConsoleEntry,
    *,
    is_trigger_entry: bool,
) -> PreservedConsoleEntry | None:
    existing = db.scalar(
        select(PreservedConsoleEntry).where(
            PreservedConsoleEntry.preserved_capture_id == capture.id,
            PreservedConsoleEntry.original_console_entry_id == entry.id,
        )
    )
    if existing is not None:
        if is_trigger_entry and not existing.is_trigger_entry:
            existing.is_trigger_entry = True
        return None

    copied = PreservedConsoleEntry(
        preserved_capture_id=capture.id,
        original_console_entry_id=entry.id,
        captured_at=entry.captured_at,
        source=entry.source,
        level=entry.level,
        message=entry.message,
        raw_payload_json=entry.raw_payload_json,
        classification=entry.classification,
        event_type=entry.event_type,
        print_state=entry.print_state,
        filename=entry.filename,
        is_trigger_entry=is_trigger_entry,
    )
    db.add(copied)
    return copied
