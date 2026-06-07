from datetime import datetime

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.search import SearchResultRead
from app.services import manual_sessions, preservation, search_export

router = APIRouter()


@router.get("/search", response_model=list[SearchResultRead])
def global_search(
    printer_id: int | None = None,
    search: str | None = None,
    classification: str | None = None,
    source: str | None = None,
    level: str | None = None,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return search_export.global_search(
        db,
        printer_id=printer_id,
        search=search,
        classification=classification,
        source=source,
        level=level,
        start_at=start_at,
        end_at=end_at,
        limit=limit,
    )


@router.get("/exports/search.txt")
def export_search(
    printer_id: int | None = None,
    search: str | None = None,
    classification: str | None = None,
    source: str | None = None,
    level: str | None = None,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    limit: int = Query(default=250, ge=1, le=500),
    db: Session = Depends(get_db),
):
    results = search_export.global_search(
        db,
        printer_id=printer_id,
        search=search,
        classification=classification,
        source=source,
        level=level,
        start_at=start_at,
        end_at=end_at,
        limit=limit,
    )
    return _text_response(search_export.render_search_export(results), "consolewatch-search.txt")


@router.get("/exports/manual-session/{session_id}.txt")
def export_manual_session(session_id: int, db: Session = Depends(get_db)):
    session = manual_sessions.get_session(db, session_id)
    if session is None:
        return Response(status_code=404)
    entries = manual_sessions.list_session_entries(db, session_id=session_id, limit=500)
    return _text_response(
        search_export.render_manual_session_export(db, session, entries),
        f"consolewatch-session-{session_id}.txt",
    )


@router.get("/exports/preserved-capture/{capture_id}.txt")
def export_preserved_capture(capture_id: int, db: Session = Depends(get_db)):
    capture = preservation.get_capture(db, capture_id)
    if capture is None:
        return Response(status_code=404)
    entries = preservation.list_capture_entries(db, capture_id=capture_id, limit=1000)
    return _text_response(
        search_export.render_preserved_capture_export(db, capture, entries),
        f"consolewatch-capture-{capture_id}.txt",
    )


def _text_response(body: str, filename: str) -> Response:
    return Response(
        content=body,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
