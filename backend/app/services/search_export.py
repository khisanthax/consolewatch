from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Select, desc, select
from sqlalchemy.orm import Session

from app.models.entities import (
    ConsoleEntry,
    ManualLogSession,
    ManualSessionEntry,
    PreservedConsoleCapture,
    PreservedConsoleEntry,
    Printer,
)


@dataclass
class SearchResult:
    collection: str
    id: int
    parent_id: int | None
    printer_id: int
    printer_name: str | None
    captured_at: datetime
    source: str
    level: str
    classification: str
    message: str


def global_search(
    db: Session,
    *,
    printer_id: int | None = None,
    search: str | None = None,
    classification: str | None = None,
    source: str | None = None,
    level: str | None = None,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    limit: int = 100,
) -> list[SearchResult]:
    bounded_limit = max(1, min(limit, 500))
    results: list[SearchResult] = []
    results.extend(
        _rolling_results(
            db,
            printer_id=printer_id,
            search=search,
            classification=classification,
            source=source,
            level=level,
            start_at=start_at,
            end_at=end_at,
            limit=bounded_limit,
        )
    )
    results.extend(
        _manual_results(
            db,
            printer_id=printer_id,
            search=search,
            classification=classification,
            source=source,
            level=level,
            start_at=start_at,
            end_at=end_at,
            limit=bounded_limit,
        )
    )
    results.extend(
        _preserved_results(
            db,
            printer_id=printer_id,
            search=search,
            classification=classification,
            source=source,
            level=level,
            start_at=start_at,
            end_at=end_at,
            limit=bounded_limit,
        )
    )
    return sorted(results, key=lambda result: result.captured_at, reverse=True)[:bounded_limit]


def render_search_export(results: list[SearchResult]) -> str:
    lines = ["ConsoleWatch Search Export", f"Results: {len(results)}", ""]
    for result in results:
        lines.extend(
            [
                f"[{result.captured_at.isoformat()}] {result.collection} printer={result.printer_name or result.printer_id}",
                f"source={result.source} level={result.level} classification={result.classification}",
                result.message,
                "",
            ]
        )
    return "\n".join(lines)


def render_manual_session_export(db: Session, session: ManualLogSession, entries: list[ManualSessionEntry]) -> str:
    printer = db.get(Printer, session.printer_id)
    lines = [
        "ConsoleWatch Manual Session Export",
        f"Session: {session.label}",
        f"Printer: {printer.name if printer else session.printer_id}",
        f"Status: {session.status}",
        f"Started: {session.started_at.isoformat()}",
        f"Ended: {session.ended_at.isoformat() if session.ended_at else 'active'}",
        f"Entries: {len(entries)}",
        "",
    ]
    if session.notes:
        lines.extend(["Notes:", session.notes, ""])
    lines.extend(_entry_lines(entries))
    return "\n".join(lines)


def render_preserved_capture_export(
    db: Session,
    capture: PreservedConsoleCapture,
    entries: list[PreservedConsoleEntry],
) -> str:
    printer = db.get(Printer, capture.printer_id)
    lines = [
        "ConsoleWatch Preserved Capture Export",
        f"Capture: {capture.id}",
        f"Printer: {printer.name if printer else capture.printer_id}",
        f"Trigger type: {capture.trigger_type}",
        f"Trigger time: {capture.triggered_at.isoformat()}",
        f"Window: {capture.started_at.isoformat()} to {capture.ended_at.isoformat()}",
        f"Trigger message: {capture.trigger_message}",
        f"Entries: {len(entries)}",
        "",
    ]
    lines.extend(_entry_lines(entries))
    return "\n".join(lines)


def _entry_lines(entries) -> list[str]:
    lines: list[str] = []
    for entry in entries:
        marker = " TRIGGER" if getattr(entry, "is_trigger_entry", False) else ""
        lines.extend(
            [
                f"[{entry.captured_at.isoformat()}]{marker}",
                f"source={entry.source} level={entry.level} classification={entry.classification}",
                entry.message,
                "",
            ]
        )
    return lines


def _apply_entry_filters(statement, model, *, search, classification, source, level, start_at, end_at):
    if search:
        statement = statement.where(model.message.ilike(f"%{search}%"))
    if classification:
        statement = statement.where(model.classification == classification)
    if source:
        statement = statement.where(model.source == source)
    if level:
        statement = statement.where(model.level == level)
    if start_at:
        statement = statement.where(model.captured_at >= start_at)
    if end_at:
        statement = statement.where(model.captured_at <= end_at)
    return statement


def _rolling_results(db: Session, **filters) -> list[SearchResult]:
    limit = filters.pop("limit")
    printer_id = filters.pop("printer_id")
    statement: Select[tuple[ConsoleEntry]] = select(ConsoleEntry)
    if printer_id is not None:
        statement = statement.where(ConsoleEntry.printer_id == printer_id)
    statement = _apply_entry_filters(statement, ConsoleEntry, **filters)
    statement = statement.order_by(desc(ConsoleEntry.captured_at)).limit(limit)
    return [
        SearchResult(
            collection="rolling",
            id=entry.id,
            parent_id=None,
            printer_id=entry.printer_id,
            printer_name=_printer_name(db, entry.printer_id),
            captured_at=entry.captured_at,
            source=entry.source,
            level=entry.level,
            classification=entry.classification,
            message=entry.message,
        )
        for entry in db.scalars(statement).all()
    ]


def _manual_results(db: Session, **filters) -> list[SearchResult]:
    limit = filters.pop("limit")
    printer_id = filters.pop("printer_id")
    statement = select(ManualSessionEntry, ManualLogSession).join(
        ManualLogSession, ManualSessionEntry.session_id == ManualLogSession.id
    )
    if printer_id is not None:
        statement = statement.where(ManualLogSession.printer_id == printer_id)
    statement = _apply_entry_filters(statement, ManualSessionEntry, **filters)
    statement = statement.order_by(desc(ManualSessionEntry.captured_at)).limit(limit)
    return [
        SearchResult(
            collection="manual_session",
            id=entry.id,
            parent_id=session.id,
            printer_id=session.printer_id,
            printer_name=_printer_name(db, session.printer_id),
            captured_at=entry.captured_at,
            source=entry.source,
            level=entry.level,
            classification=entry.classification,
            message=entry.message,
        )
        for entry, session in db.execute(statement).all()
    ]


def _preserved_results(db: Session, **filters) -> list[SearchResult]:
    limit = filters.pop("limit")
    printer_id = filters.pop("printer_id")
    statement = select(PreservedConsoleEntry, PreservedConsoleCapture).join(
        PreservedConsoleCapture, PreservedConsoleEntry.preserved_capture_id == PreservedConsoleCapture.id
    )
    if printer_id is not None:
        statement = statement.where(PreservedConsoleCapture.printer_id == printer_id)
    statement = _apply_entry_filters(statement, PreservedConsoleEntry, **filters)
    statement = statement.order_by(desc(PreservedConsoleEntry.captured_at)).limit(limit)
    return [
        SearchResult(
            collection="preserved_capture",
            id=entry.id,
            parent_id=capture.id,
            printer_id=capture.printer_id,
            printer_name=_printer_name(db, capture.printer_id),
            captured_at=entry.captured_at,
            source=entry.source,
            level=entry.level,
            classification=entry.classification,
            message=entry.message,
        )
        for entry, capture in db.execute(statement).all()
    ]


def _printer_name(db: Session, printer_id: int) -> str | None:
    printer = db.get(Printer, printer_id)
    return printer.name if printer else None
