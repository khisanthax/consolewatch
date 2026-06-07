from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.models.entities import ensure_utc


class ConsoleEntryRead(BaseModel):
    id: int
    printer_id: int
    captured_at: datetime
    source: str
    level: str
    message: str
    raw_payload_json: str | None
    classification: str
    event_type: str | None
    print_state: str | None
    filename: str | None
    restart_boundary_id: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("captured_at", "created_at")
    def serialize_datetime(self, value: datetime) -> str:
        return ensure_utc(value).isoformat()


class MoonrakerNotificationIn(BaseModel):
    method: str = Field(min_length=1)
    params: list[Any] = Field(default_factory=list)
    jsonrpc: str | None = None


class ConsoleEntryIngestResult(BaseModel):
    entries_created: int
    entries: list[ConsoleEntryRead]
