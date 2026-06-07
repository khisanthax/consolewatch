from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models import entities  # noqa: F401
from app.models.entities import ConsoleEntry, ManualSessionEntry, PreservedConsoleEntry, Printer
from app.services.retention import prune_rolling_entries


def test_prune_rolling_entries_keeps_saved_copy_tables():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    now = datetime(2026, 6, 7, 12, 0, tzinfo=UTC)

    with testing_session() as db:
        printer = Printer(
            name="Prune Test",
            base_url="http://moonraker.local",
            console_watch_enabled=True,
            retention_hours=4,
        )
        db.add(printer)
        db.commit()
        db.refresh(printer)

        old_time = now - timedelta(hours=5)
        new_time = now - timedelta(hours=1)
        db.add_all(
            [
                ConsoleEntry(
                    printer_id=printer.id,
                    captured_at=old_time,
                    source="gcode_response",
                    level="info",
                    message="old rolling",
                    classification="normal",
                ),
                ConsoleEntry(
                    printer_id=printer.id,
                    captured_at=new_time,
                    source="gcode_response",
                    level="info",
                    message="new rolling",
                    classification="normal",
                ),
                ManualSessionEntry(
                    session_id=1,
                    captured_at=old_time,
                    source="gcode_response",
                    level="info",
                    message="saved manual copy",
                    classification="normal",
                ),
                PreservedConsoleEntry(
                    preserved_capture_id=1,
                    captured_at=old_time,
                    source="gcode_response",
                    level="info",
                    message="preserved copy",
                    classification="normal",
                ),
            ]
        )
        db.commit()

        deleted = prune_rolling_entries(db, now=now)

        remaining_messages = {entry.message for entry in db.query(ConsoleEntry).all()}
        assert deleted == {printer.id: 1}
        assert remaining_messages == {"new rolling"}
        assert db.query(ManualSessionEntry).count() == 1
        assert db.query(PreservedConsoleEntry).count() == 1
