from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.deps import get_db
from app.main import app
from app.models import entities  # noqa: F401


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
    return TestClient(app)


def create_printer(client: TestClient) -> int:
    response = client.post(
        "/api/v1/printers",
        json={
            "name": "Test Printer",
            "base_url": "http://moonraker.local",
            "is_enabled": True,
            "console_watch_enabled": False,
            "retention_hours": 8,
        },
    )
    assert response.status_code == 201
    return int(response.json()["id"])


def test_ingests_gcode_response_notification():
    with make_client() as client:
        printer_id = create_printer(client)

        response = client.post(
            f"/api/v1/console-entries/moonraker-notification?printer_id={printer_id}",
            json={
                "jsonrpc": "2.0",
                "method": "notify_gcode_response",
                "params": ["!! ADC out of range"],
            },
        )

        assert response.status_code == 201
        body = response.json()
        assert body["entries_created"] == 1
        entry = body["entries"][0]
        assert entry["source"] == "gcode_response"
        assert entry["classification"] == "adc"
        assert entry["level"] == "error"
        assert entry["captured_at"].endswith("+00:00")

        listed = client.get("/api/v1/console-entries", params={"printer_id": printer_id, "classification": "adc"})
        assert listed.status_code == 200
        assert listed.json()[0]["message"] == "!! ADC out of range"

    app.dependency_overrides.clear()


def test_ingests_klippy_state_and_status_update_notifications():
    with make_client() as client:
        printer_id = create_printer(client)

        shutdown = client.post(
            f"/api/v1/console-entries/moonraker-notification?printer_id={printer_id}",
            json={"jsonrpc": "2.0", "method": "notify_klippy_shutdown", "params": []},
        )
        assert shutdown.status_code == 201
        assert shutdown.json()["entries"][0]["event_type"] == "shutdown"

        status = client.post(
            f"/api/v1/console-entries/moonraker-notification?printer_id={printer_id}",
            json={
                "jsonrpc": "2.0",
                "method": "notify_status_update",
                "params": [
                    {
                        "webhooks": {"state": "ready"},
                        "print_stats": {"state": "printing", "filename": "cube.gcode"},
                    },
                    578243.57824499,
                ],
            },
        )
        assert status.status_code == 201
        assert status.json()["entries_created"] == 2

        listed = client.get("/api/v1/console-entries", params={"printer_id": printer_id, "source": "klippy_state"})
        messages = [entry["message"] for entry in listed.json()]
        assert "Klippy shutdown" in messages
        assert "Klippy webhooks state changed to ready" in messages
        assert "Print state changed to printing for cube.gcode" in messages

    app.dependency_overrides.clear()
