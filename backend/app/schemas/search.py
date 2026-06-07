from datetime import datetime

from pydantic import BaseModel, field_serializer

from app.models.entities import ensure_utc


class SearchResultRead(BaseModel):
    collection: str
    id: int
    parent_id: int | None = None
    printer_id: int
    printer_name: str | None = None
    captured_at: datetime
    source: str
    level: str
    classification: str
    message: str

    @field_serializer("captured_at")
    def serialize_datetime(self, value: datetime) -> str:
        return ensure_utc(value).isoformat()
