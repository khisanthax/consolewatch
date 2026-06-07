from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.sessions import (
    ManualSessionCreate,
    ManualSessionDetail,
    ManualSessionRead,
    ManualSessionStop,
    ManualSessionUpdate,
)
from app.services import manual_sessions

router = APIRouter()


@router.get("", response_model=list[ManualSessionRead])
def list_sessions(printer_id: int | None = None, db: Session = Depends(get_db)):
    sessions = manual_sessions.list_sessions(db, printer_id=printer_id)
    return [manual_sessions.attach_session_metadata(db, session) for session in sessions]


@router.post("", response_model=ManualSessionRead, status_code=status.HTTP_201_CREATED)
def start_session(payload: ManualSessionCreate, db: Session = Depends(get_db)):
    try:
        session = manual_sessions.start_session(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return manual_sessions.attach_session_metadata(db, session)


@router.get("/{session_id}", response_model=ManualSessionDetail)
def get_session(
    session_id: int,
    search: str | None = None,
    classification: str | None = None,
    source: str | None = None,
    level: str | None = None,
    limit: int = Query(default=250, ge=1, le=500),
    db: Session = Depends(get_db),
):
    session = manual_sessions.get_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    session = manual_sessions.attach_session_metadata(db, session)
    entries = manual_sessions.list_session_entries(
        db,
        session_id=session_id,
        search=search,
        classification=classification,
        source=source,
        level=level,
        limit=limit,
    )
    return ManualSessionDetail.model_validate(session).model_copy(update={"entries": entries})


@router.put("/{session_id}", response_model=ManualSessionRead)
def update_session(session_id: int, payload: ManualSessionUpdate, db: Session = Depends(get_db)):
    session = manual_sessions.get_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return manual_sessions.attach_session_metadata(db, manual_sessions.update_session(db, session, payload))


@router.post("/{session_id}/stop", response_model=ManualSessionRead)
def stop_session(session_id: int, payload: ManualSessionStop | None = None, db: Session = Depends(get_db)):
    session = manual_sessions.get_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    stop_reason = payload.stop_reason if payload else "manual"
    return manual_sessions.attach_session_metadata(db, manual_sessions.stop_session(db, session, stop_reason=stop_reason))


@router.post("/{session_id}/save", response_model=ManualSessionRead)
def save_session(session_id: int, db: Session = Depends(get_db)):
    session = manual_sessions.get_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return manual_sessions.attach_session_metadata(db, manual_sessions.save_session(db, session))


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def discard_session(session_id: int, db: Session = Depends(get_db)):
    session = manual_sessions.get_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    manual_sessions.discard_session(db, session)
