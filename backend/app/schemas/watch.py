from pydantic import BaseModel


class WatchStatusRead(BaseModel):
    active_printer_ids: list[int]
    task_count: int
    background_watch_enabled: bool
    watched_printer_count: int


class RetentionPruneResult(BaseModel):
    deleted_by_printer: dict[int, int]
    deleted_total: int
