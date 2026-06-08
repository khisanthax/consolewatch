from pydantic import BaseModel


class StorageInfo(BaseModel):
    database_backend: str
    sqlite_path: str | None
    sqlite_exists: bool
    sqlite_size_bytes: int | None


class RuntimeInfo(BaseModel):
    app_name: str
    environment: str
    background_watch_enabled: bool
    watch_manager_interval_seconds: float
    retention_prune_interval_seconds: int
    moonraker_reconnect_delay_seconds: int


class DiagnosticsRead(BaseModel):
    counts: dict[str, int]
    storage: StorageInfo
    runtime: RuntimeInfo
    trigger_classifications: list[str]
    trigger_message_markers: list[str]
    boundary_suppression_seconds: float
    notes: list[str]
