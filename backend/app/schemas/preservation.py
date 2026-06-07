from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_serializer

from app.models.entities import ensure_utc


class PreservedCaptureRead(BaseModel):
    id: int
    printer_id: int
    printer_name: str | None = None
    trigger_type: str
    trigger_reason: str
    trigger_message: str
    triggered_at: datetime
    started_at: datetime
    ended_at: datetime
    status: str
    notes: str | None
    created_at: datetime
    updated_at: datetime
    entry_count: int = 0

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("triggered_at", "started_at", "ended_at", "created_at", "updated_at")
    def serialize_datetime(self, value: datetime) -> str:
        return ensure_utc(value).isoformat()


class PreservedEntryRead(BaseModel):
    id: int
    preserved_capture_id: int
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
    is_trigger_entry: bool
    boundary_type: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("captured_at", "created_at")
    def serialize_datetime(self, value: datetime) -> str:
        return ensure_utc(value).isoformat()


class DetectedEventRead(BaseModel):
    id: int
    printer_id: int
    captured_at: datetime
    event_type: str
    severity: str
    message: str
    related_capture_id: int | None
    related_session_id: int | None
    restart_boundary_id: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("captured_at", "created_at")
    def serialize_datetime(self, value: datetime) -> str:
        return ensure_utc(value).isoformat()


class PreservedCaptureDetail(PreservedCaptureRead):
    entries: list[PreservedEntryRead]
    detected_events: list[DetectedEventRead] = []
