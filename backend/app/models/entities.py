from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class Printer(Base):
    __tablename__ = "printers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    base_url: Mapped[str] = mapped_column(String(500), nullable=False)
    api_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    console_watch_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    retention_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=8)
    connection_status: Mapped[str] = mapped_column(String(40), nullable=False, default="unknown")
    last_connected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    console_entries: Mapped[list["ConsoleEntry"]] = relationship(back_populates="printer", cascade="all, delete-orphan")


class RestartBoundary(Base):
    __tablename__ = "restart_boundaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    printer_id: Mapped[int] = mapped_column(ForeignKey("printers.id", ondelete="CASCADE"), nullable=False, index=True)
    boundary_type: Mapped[str] = mapped_column(String(80), nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    previous_state: Mapped[str | None] = mapped_column(String(120), nullable=True)
    new_state: Mapped[str | None] = mapped_column(String(120), nullable=True)
    raw_payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class ConsoleEntry(Base):
    __tablename__ = "console_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    printer_id: Mapped[int] = mapped_column(ForeignKey("printers.id", ondelete="CASCADE"), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String(80), nullable=False, default="unknown")
    level: Mapped[str] = mapped_column(String(40), nullable=False, default="info")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    raw_payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    classification: Mapped[str] = mapped_column(String(80), nullable=False, default="unknown")
    event_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    print_state: Mapped[str | None] = mapped_column(String(80), nullable=True)
    filename: Mapped[str | None] = mapped_column(Text, nullable=True)
    restart_boundary_id: Mapped[int | None] = mapped_column(ForeignKey("restart_boundaries.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    printer: Mapped[Printer] = relationship(back_populates="console_entries")

    __table_args__ = (
        Index("ix_console_entries_printer_captured_at", "printer_id", "captured_at"),
        Index("ix_console_entries_classification", "classification"),
        Index("ix_console_entries_level", "level"),
        Index("ix_console_entries_event_type", "event_type"),
        Index("ix_console_entries_captured_at", "captured_at"),
    )


class ManualLogSession(Base):
    __tablename__ = "manual_log_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    printer_id: Mapped[int] = mapped_column(ForeignKey("printers.id", ondelete="CASCADE"), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="active")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    saved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    stop_reason: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    entries: Mapped[list["ManualSessionEntry"]] = relationship(cascade="all, delete-orphan")


class ManualSessionEntry(Base):
    __tablename__ = "manual_session_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("manual_log_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    original_console_entry_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String(80), nullable=False)
    level: Mapped[str] = mapped_column(String(40), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    raw_payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    classification: Mapped[str] = mapped_column(String(80), nullable=False)
    event_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    print_state: Mapped[str | None] = mapped_column(String(80), nullable=True)
    filename: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class PreservedConsoleCapture(Base):
    __tablename__ = "preserved_console_captures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    printer_id: Mapped[int] = mapped_column(ForeignKey("printers.id", ondelete="CASCADE"), nullable=False, index=True)
    trigger_type: Mapped[str] = mapped_column(String(80), nullable=False)
    trigger_reason: Mapped[str] = mapped_column(Text, nullable=False)
    trigger_message: Mapped[str] = mapped_column(Text, nullable=False)
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="collecting")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    entries: Mapped[list["PreservedConsoleEntry"]] = relationship(cascade="all, delete-orphan")


class PreservedConsoleEntry(Base):
    __tablename__ = "preserved_console_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    preserved_capture_id: Mapped[int] = mapped_column(ForeignKey("preserved_console_captures.id", ondelete="CASCADE"), nullable=False, index=True)
    original_console_entry_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String(80), nullable=False)
    level: Mapped[str] = mapped_column(String(40), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    raw_payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    classification: Mapped[str] = mapped_column(String(80), nullable=False)
    event_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    print_state: Mapped[str | None] = mapped_column(String(80), nullable=True)
    filename: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_trigger_entry: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class DetectedEvent(Base):
    __tablename__ = "detected_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    printer_id: Mapped[int] = mapped_column(ForeignKey("printers.id", ondelete="CASCADE"), nullable=False, index=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    severity: Mapped[str] = mapped_column(String(40), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    raw_payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    related_capture_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    related_session_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    restart_boundary_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
