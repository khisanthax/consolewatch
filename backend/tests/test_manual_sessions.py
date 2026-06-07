from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.deps import get_db
from app.main import app
from app.models import entities  # noqa: F401
from app.models.entities import ConsoleEntry


def make_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), testing_session


def create_printer(client: TestClient) -> int:
    response = client.post(
        "/api/v1/printers",
        json={
            "name": "Session Printer",
            "base_url": "http://moonraker.local",
            "is_enabled": True,
            "console_watch_enabled": True,
            "retention_hours": 4,
        },
    )
    assert response.status_code == 201
    return int(response.json()["id"])


def ingest_error(client: TestClient, printer_id: int):
    return client.post(
        f"/api/v1/console-entries/moonraker-notification?printer_id={printer_id}",
        json={
            "jsonrpc": "2.0",
            "method": "notify_gcode_response",
            "params": ["!! Heater error"],
        },
    )


def test_manual_session_save_survives_rolling_prune():
    client, testing_session = make_client()
    with client:
        printer_id = create_printer(client)

        started = client.post(
            "/api/v1/sessions",
            json={"printer_id": printer_id, "label": "Heater test", "notes": "Before wiring change"},
        )
        assert started.status_code == 201
        session_id = started.json()["id"]
        assert started.json()["status"] == "active"

        ingested = ingest_error(client, printer_id)
        assert ingested.status_code == 201

        detail = client.get(f"/api/v1/sessions/{session_id}")
        assert detail.status_code == 200
        assert detail.json()["entry_count"] == 1
        assert detail.json()["entries"][0]["message"] == "!! Heater error"

        stopped = client.post(f"/api/v1/sessions/{session_id}/stop", json={"stop_reason": "done"})
        assert stopped.status_code == 200
        assert stopped.json()["status"] == "stopped"

        saved = client.post(f"/api/v1/sessions/{session_id}/save")
        assert saved.status_code == 200
        assert saved.json()["status"] == "saved"
        assert saved.json()["saved"] is True

        with testing_session() as db:
            old_entry = db.query(ConsoleEntry).first()
            assert old_entry is not None
            old_entry.captured_at = datetime.now(UTC) - timedelta(hours=5)
            db.commit()

        pruned = client.post("/api/v1/watch/prune")
        assert pruned.status_code == 200
        assert pruned.json()["deleted_total"] == 1

        detail_after_prune = client.get(f"/api/v1/sessions/{session_id}")
        assert detail_after_prune.status_code == 200
        assert detail_after_prune.json()["entry_count"] == 1
        assert detail_after_prune.json()["entries"][0]["message"] == "!! Heater error"

    app.dependency_overrides.clear()


def test_manual_session_discard_removes_session_and_copied_entries():
    client, _ = make_client()
    with client:
        printer_id = create_printer(client)
        session = client.post("/api/v1/sessions", json={"printer_id": printer_id, "label": "Discard me"}).json()
        assert ingest_error(client, printer_id).status_code == 201

        discarded = client.delete(f"/api/v1/sessions/{session['id']}")
        assert discarded.status_code == 204
        assert client.get(f"/api/v1/sessions/{session['id']}").status_code == 404

    app.dependency_overrides.clear()
