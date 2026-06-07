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
            "name": "Preserve Printer",
            "base_url": "http://moonraker.local",
            "is_enabled": True,
            "console_watch_enabled": True,
            "retention_hours": 4,
        },
    )
    assert response.status_code == 201
    return int(response.json()["id"])


def ingest_message(client: TestClient, printer_id: int, message: str):
    return client.post(
        f"/api/v1/console-entries/moonraker-notification?printer_id={printer_id}",
        json={"jsonrpc": "2.0", "method": "notify_gcode_response", "params": [message]},
    )


def test_trigger_creates_preserved_capture_with_trigger_marker_and_detected_event():
    client, _ = make_client()
    with client:
        printer_id = create_printer(client)

        assert ingest_message(client, printer_id, "Normal setup line").status_code == 201
        assert ingest_message(client, printer_id, "!! ADC out of range").status_code == 201

        captures = client.get("/api/v1/preserved-captures", params={"printer_id": printer_id})
        assert captures.status_code == 200
        assert len(captures.json()) == 1
        capture = captures.json()[0]
        assert capture["trigger_type"] == "adc"
        assert capture["entry_count"] == 2

        detail = client.get(f"/api/v1/preserved-captures/{capture['id']}")
        assert detail.status_code == 200
        body = detail.json()
        assert len(body["detected_events"]) == 1
        assert body["detected_events"][0]["event_type"] == "adc"
        assert [entry["message"] for entry in body["entries"]] == ["Normal setup line", "!! ADC out of range"]
        assert [entry["is_trigger_entry"] for entry in body["entries"]] == [False, True]

    app.dependency_overrides.clear()


def test_preserved_capture_extends_and_survives_rolling_prune():
    client, testing_session = make_client()
    with client:
        printer_id = create_printer(client)

        assert ingest_message(client, printer_id, "!! Heater error").status_code == 201
        first_capture = client.get("/api/v1/preserved-captures").json()[0]
        assert ingest_message(client, printer_id, "Timer too close").status_code == 201
        second_capture = client.get("/api/v1/preserved-captures").json()[0]
        assert first_capture["id"] == second_capture["id"]
        assert second_capture["entry_count"] == 2

        with testing_session() as db:
            for entry in db.query(ConsoleEntry).all():
                entry.captured_at = datetime.now(UTC) - timedelta(hours=5)
            db.commit()

        pruned = client.post("/api/v1/watch/prune")
        assert pruned.status_code == 200
        assert pruned.json()["deleted_total"] == 2

        detail = client.get(f"/api/v1/preserved-captures/{first_capture['id']}")
        assert detail.status_code == 200
        assert detail.json()["entry_count"] == 2
        assert [entry["message"] for entry in detail.json()["entries"]] == ["!! Heater error", "Timer too close"]

    app.dependency_overrides.clear()
