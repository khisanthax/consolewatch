from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_serializer

from app.models.entities import ensure_utc


class PrinterBase(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    base_url: HttpUrl
    is_enabled: bool = True
    console_watch_enabled: bool = False
    retention_hours: int = Field(default=8, ge=4, le=720)


class PrinterCreate(PrinterBase):
    api_key: str | None = Field(default=None, max_length=4096)


class PrinterUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    base_url: HttpUrl | None = None
    api_key: str | None = Field(default=None, max_length=4096)
    is_enabled: bool | None = None
    console_watch_enabled: bool | None = None
    retention_hours: int | None = Field(default=None, ge=4, le=720)


class PrinterRead(PrinterBase):
    id: int
    base_url: str
    connection_status: str
    last_connected_at: datetime | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("last_connected_at", "created_at", "updated_at")
    def serialize_datetime(self, value: datetime | None) -> str | None:
        if value is None:
            return None
        return ensure_utc(value).isoformat()
