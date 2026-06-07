from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.preservation import PreservedCaptureDetail, PreservedCaptureRead
from app.services import preservation

router = APIRouter()


@router.get("", response_model=list[PreservedCaptureRead])
def list_preserved_captures(
    printer_id: int | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    captures = preservation.list_captures(db, printer_id=printer_id, limit=limit)
    return [preservation.attach_capture_metadata(db, capture) for capture in captures]


@router.get("/{capture_id}", response_model=PreservedCaptureDetail)
def get_preserved_capture(
    capture_id: int,
    search: str | None = None,
    classification: str | None = None,
    source: str | None = None,
    level: str | None = None,
    limit: int = Query(default=500, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    capture = preservation.get_capture(db, capture_id)
    if capture is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preserved capture not found")
    capture = preservation.attach_capture_metadata(db, capture)
    entries = preservation.list_capture_entries(
        db,
        capture_id=capture_id,
        search=search,
        classification=classification,
        source=source,
        level=level,
        limit=limit,
    )
    events = preservation.detected_events_for_capture(db, capture_id)
    return PreservedCaptureDetail.model_validate(capture).model_copy(
        update={"entries": entries, "detected_events": events}
    )
