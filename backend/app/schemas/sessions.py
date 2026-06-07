from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.models.entities import ensure_utc


class ManualSessionCreate(BaseModel):
    printer_id: int
    label: str = Field(min_length=1, max_length=200)
    notes: str | None = None


class ManualSessionUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=200)
    notes: str | None = None


class ManualSessionRead(BaseModel):
    id: int
    printer_id: int
    label: str
    notes: str | None
    status: str
    started_at: datetime
    ended_at: datetime | None
    saved: bool
    stop_reason: str | None
    created_at: datetime
    updated_at: datetime
    entry_count: int = 0
    printer_name: str | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("started_at", "ended_at", "created_at", "updated_at")
    def serialize_datetime(self, value: datetime | None) -> str | None:
        if value is None:
            return None
        return ensure_utc(value).isoformat()


class ManualSessionEntryRead(BaseModel):
    id: int
    session_id: int
    original_console_entry_id: int | None
    captured_at: datetime
    source: str
    level: str
    message: str
    raw_payload_json: str | None
    classification: str
    event_type: str | None
    print_state: str | None
    filename: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("captured_at", "created_at")
    def serialize_datetime(self, value: datetime) -> str:
        return ensure_utc(value).isoformat()


class ManualSessionDetail(ManualSessionRead):
    entries: list[ManualSessionEntryRead]


class ManualSessionStop(BaseModel):
    stop_reason: str | None = Field(default="manual", max_length=120)
