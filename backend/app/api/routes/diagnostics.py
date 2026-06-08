from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.diagnostics import DiagnosticsRead
from app.services.diagnostics import get_diagnostics

router = APIRouter()


@router.get("", response_model=DiagnosticsRead)
def read_diagnostics(db: Session = Depends(get_db)):
    return get_diagnostics(db)
