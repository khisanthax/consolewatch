from datetime import UTC, datetime

from sqlalchemy import Select, desc, func, select
from sqlalchemy.orm import Session

from app.models.entities import ConsoleEntry, ManualLogSession, ManualSessionEntry, Printer, utc_now
from app.schemas.sessions import ManualSessionCreate, ManualSessionUpdate


def list_sessions(db: Session, *, printer_id: int | None = None, include_discarded: bool = False) -> list[ManualLogSession]:
    statement = select(ManualLogSession)
    if printer_id is not None:
        statement = statement.where(ManualLogSession.printer_id == printer_id)
    if not include_discarded:
        statement = statement.where(ManualLogSession.status != "discarded")
    statement = statement.order_by(desc(ManualLogSession.started_at), desc(ManualLogSession.id))
    return list(db.scalars(statement).all())


def get_session(db: Session, session_id: int) -> ManualLogSession | None:
    return db.get(ManualLogSession, session_id)


def start_session(db: Session, payload: ManualSessionCreate) -> ManualLogSession:
    printer = db.get(Printer, payload.printer_id)
    if printer is None:
        raise ValueError("Printer not found")

    session = ManualLogSession(
        printer_id=payload.printer_id,
        label=payload.label.strip(),
        notes=payload.notes,
        status="active",
        started_at=datetime.now(UTC),
        saved=False,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def update_session(db: Session, session: ManualLogSession, payload: ManualSessionUpdate) -> ManualLogSession:
    updates = payload.model_dump(exclude_unset=True)
    if "label" in updates and updates["label"] is not None:
        session.label = updates["label"].strip()
    if "notes" in updates:
        session.notes = updates["notes"]
    session.updated_at = utc_now()
    db.commit()
    db.refresh(session)
    return session


def stop_session(db: Session, session: ManualLogSession, *, stop_reason: str | None = "manual") -> ManualLogSession:
    if session.status != "active":
        return session
    session.status = "stopped"
    session.ended_at = datetime.now(UTC)
    session.stop_reason = stop_reason or "manual"
    session.updated_at = utc_now()
    db.commit()
    db.refresh(session)
    return session


def save_session(db: Session, session: ManualLogSession) -> ManualLogSession:
    if session.status == "active":
        stop_session(db, session, stop_reason="saved")
    session.status = "saved"
    session.saved = True
    session.updated_at = utc_now()
    db.commit()
    db.refresh(session)
    return session


def discard_session(db: Session, session: ManualLogSession) -> None:
    db.delete(session)
    db.commit()


def list_session_entries(
    db: Session,
    *,
    session_id: int,
    search: str | None = None,
    classification: str | None = None,
    source: str | None = None,
    level: str | None = None,
    limit: int = 250,
) -> list[ManualSessionEntry]:
    bounded_limit = max(1, min(limit, 500))
    statement: Select[tuple[ManualSessionEntry]] = select(ManualSessionEntry).where(
        ManualSessionEntry.session_id == session_id
    )
    if search:
        statement = statement.where(ManualSessionEntry.message.ilike(f"%{search}%"))
    if classification:
        statement = statement.where(ManualSessionEntry.classification == classification)
    if source:
        statement = statement.where(ManualSessionEntry.source == source)
    if level:
        statement = statement.where(ManualSessionEntry.level == level)
    statement = statement.order_by(ManualSessionEntry.captured_at.asc(), ManualSessionEntry.id.asc()).limit(bounded_limit)
    return list(db.scalars(statement).all())


def copy_entry_to_active_sessions(db: Session, entry: ConsoleEntry) -> list[ManualSessionEntry]:
    active_sessions = db.scalars(
        select(ManualLogSession).where(
            ManualLogSession.printer_id == entry.printer_id,
            ManualLogSession.status == "active",
        )
    ).all()
    copied: list[ManualSessionEntry] = []
    for session in active_sessions:
        session_entry = ManualSessionEntry(
            session_id=session.id,
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
        )
        db.add(session_entry)
        copied.append(session_entry)
    return copied


def entry_count(db: Session, session_id: int) -> int:
    return int(db.scalar(select(func.count()).select_from(ManualSessionEntry).where(ManualSessionEntry.session_id == session_id)) or 0)


def attach_session_metadata(db: Session, session: ManualLogSession):
    setattr(session, "entry_count", entry_count(db, session.id))
    printer = db.get(Printer, session.printer_id)
    setattr(session, "printer_name", printer.name if printer else None)
    return session
