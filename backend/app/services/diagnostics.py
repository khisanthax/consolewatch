from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.entities import (
    ConsoleEntry,
    DetectedEvent,
    ManualLogSession,
    ManualSessionEntry,
    PreservedConsoleCapture,
    PreservedConsoleEntry,
    Printer,
    RestartBoundary,
)
from app.schemas.diagnostics import DiagnosticsRead, RuntimeInfo, StorageInfo
from app.services.preservation import TRIGGER_CLASSIFICATIONS, TRIGGER_MESSAGE_MARKERS
from app.services.restart_boundaries import SUPPRESSION_WINDOW


def get_diagnostics(db: Session) -> DiagnosticsRead:
    settings = get_settings()
    return DiagnosticsRead(
        counts={
            "printers": _count(db, Printer),
            "console_entries": _count(db, ConsoleEntry),
            "manual_log_sessions": _count(db, ManualLogSession),
            "manual_session_entries": _count(db, ManualSessionEntry),
            "preserved_console_captures": _count(db, PreservedConsoleCapture),
            "preserved_console_entries": _count(db, PreservedConsoleEntry),
            "detected_events": _count(db, DetectedEvent),
            "restart_boundaries": _count(db, RestartBoundary),
        },
        storage=_storage_info(settings.database_url),
        runtime=RuntimeInfo(
            app_name=settings.app_name,
            environment=settings.environment,
            background_watch_enabled=settings.background_watch_enabled,
            watch_manager_interval_seconds=settings.watch_manager_interval_seconds,
            retention_prune_interval_seconds=settings.retention_prune_interval_seconds,
            moonraker_reconnect_delay_seconds=settings.moonraker_reconnect_delay_seconds,
        ),
        trigger_classifications=sorted(TRIGGER_CLASSIFICATIONS),
        trigger_message_markers=list(TRIGGER_MESSAGE_MARKERS),
        boundary_suppression_seconds=SUPPRESSION_WINDOW.total_seconds(),
        notes=[
            "Moonraker API keys are intentionally excluded from diagnostics.",
            "SQLite file size is shown only when the configured SQLite path is visible to the backend process.",
            "Continuous watch pruning only deletes console_entries; copied manual sessions and preserved captures remain separate.",
        ],
    )


def _count(db: Session, model) -> int:
    return int(db.scalar(select(func.count()).select_from(model)) or 0)


def _storage_info(database_url: str) -> StorageInfo:
    sqlite_path = _sqlite_path(database_url)
    if sqlite_path is None:
        return StorageInfo(
            database_backend=_database_backend(database_url),
            sqlite_path=None,
            sqlite_exists=False,
            sqlite_size_bytes=None,
        )

    path = Path(sqlite_path)
    return StorageInfo(
        database_backend=_database_backend(database_url),
        sqlite_path=str(path),
        sqlite_exists=path.exists(),
        sqlite_size_bytes=path.stat().st_size if path.exists() else None,
    )


def _sqlite_path(database_url: str) -> str | None:
    if database_url == "sqlite://":
        return None
    if database_url.startswith("sqlite:////"):
        return "/" + database_url.removeprefix("sqlite:////")
    if database_url.startswith("sqlite:///"):
        return database_url.removeprefix("sqlite:///")
    return None


def _database_backend(database_url: str) -> str:
    if "://" in database_url:
        return database_url.split("://", 1)[0]
    return "unknown"
