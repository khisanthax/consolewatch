from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.entities import Printer
from app.schemas.watch import RetentionPruneResult, WatchStatusRead
from app.services.retention import prune_rolling_entries
from app.services.runtime import rolling_watch_manager

router = APIRouter()


@router.get("/status", response_model=WatchStatusRead)
def get_watch_status(db: Session = Depends(get_db)):
    runtime_status = rolling_watch_manager.status()
    watched_printer_count = len(
        db.scalars(
            select(Printer.id).where(
                Printer.is_enabled.is_(True),
                Printer.console_watch_enabled.is_(True),
            )
        ).all()
    )
    return WatchStatusRead(
        active_printer_ids=runtime_status.active_printer_ids,
        task_count=runtime_status.task_count,
        background_watch_enabled=runtime_status.background_watch_enabled,
        watched_printer_count=watched_printer_count,
    )


@router.post("/prune", response_model=RetentionPruneResult)
def prune_watch_entries(db: Session = Depends(get_db)):
    deleted_by_printer = prune_rolling_entries(db)
    return RetentionPruneResult(
        deleted_by_printer=deleted_by_printer,
        deleted_total=sum(deleted_by_printer.values()),
    )
