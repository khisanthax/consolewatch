from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.entities import ConsoleEntry, Printer


def prune_rolling_entries(db: Session, *, now: datetime | None = None) -> dict[int, int]:
    now = now or datetime.now(UTC)
    deleted_by_printer: dict[int, int] = {}
    printers = db.scalars(select(Printer).where(Printer.console_watch_enabled.is_(True))).all()

    for printer in printers:
        cutoff = now - timedelta(hours=printer.retention_hours)
        result = db.execute(
            delete(ConsoleEntry).where(
                ConsoleEntry.printer_id == printer.id,
                ConsoleEntry.captured_at < cutoff,
            )
        )
        deleted_by_printer[printer.id] = int(result.rowcount or 0)

    db.commit()
    return deleted_by_printer


def count_watched_entries(db: Session) -> int:
    return int(db.query(ConsoleEntry).count())
