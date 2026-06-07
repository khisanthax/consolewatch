from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.console import ConsoleEntryIngestResult, ConsoleEntryRead, MoonrakerNotificationIn
from app.services import console_entries, printer_profiles

router = APIRouter()


@router.get("", response_model=list[ConsoleEntryRead])
def list_console_entries(
    printer_id: int | None = None,
    search: str | None = None,
    classification: str | None = None,
    source: str | None = None,
    level: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return console_entries.list_recent_entries(
        db,
        printer_id=printer_id,
        search=search,
        classification=classification,
        source=source,
        level=level,
        limit=limit,
    )


@router.post("/moonraker-notification", response_model=ConsoleEntryIngestResult, status_code=status.HTTP_201_CREATED)
def ingest_moonraker_notification(
    printer_id: int,
    payload: MoonrakerNotificationIn,
    db: Session = Depends(get_db),
):
    printer = printer_profiles.get_printer(db, printer_id)
    if printer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Printer not found")

    entries = console_entries.ingest_moonraker_notification(db, printer=printer, notification=payload)
    return ConsoleEntryIngestResult(entries_created=len(entries), entries=entries)
