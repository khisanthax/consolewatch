from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.deps import get_db
from app.main import app
from app.models import entities  # noqa: F401
from app.models.entities import DetectedEvent, RestartBoundary


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
            "name": "Boundary Printer",
            "base_url": "http://moonraker.local",
            "is_enabled": True,
            "console_watch_enabled": True,
            "retention_hours": 4,
        },
    )
    assert response.status_code == 201
    return int(response.json()["id"])


def ingest(client: TestClient, printer_id: int, payload: dict):
    return client.post(f"/api/v1/console-entries/moonraker-notification?printer_id={printer_id}", json=payload)


def test_klippy_shutdown_creates_boundary_and_links_entry_and_event():
    client, testing_session = make_client()
    with client:
        printer_id = create_printer(client)
        response = ingest(client, printer_id, {"jsonrpc": "2.0", "method": "notify_klippy_shutdown", "params": []})

        assert response.status_code == 201
        entry = response.json()["entries"][0]
        assert entry["restart_boundary_id"] is not None
        assert entry["boundary_type"] == "klippy_shutdown"

        listed = client.get("/api/v1/console-entries", params={"printer_id": printer_id})
        assert listed.json()[0]["boundary_type"] == "klippy_shutdown"

        captures = client.get("/api/v1/preserved-captures").json()
        detail = client.get(f"/api/v1/preserved-captures/{captures[0]['id']}").json()
        assert detail["entries"][0]["boundary_type"] == "klippy_shutdown"
        assert detail["detected_events"][0]["restart_boundary_id"] is not None

        with testing_session() as db:
            assert db.query(RestartBoundary).count() == 1
            assert db.query(DetectedEvent).first().restart_boundary_id is not None

    app.dependency_overrides.clear()


def test_duplicate_restart_boundaries_are_suppressed():
    client, testing_session = make_client()
    with client:
        printer_id = create_printer(client)
        payload = {"jsonrpc": "2.0", "method": "notify_gcode_response", "params": ["FIRMWARE_RESTART"]}

        first = ingest(client, printer_id, payload).json()["entries"][0]
        second = ingest(client, printer_id, payload).json()["entries"][0]

        assert first["boundary_type"] == "firmware_restart"
        assert second["boundary_type"] == "firmware_restart"
        assert first["restart_boundary_id"] == second["restart_boundary_id"]

        with testing_session() as db:
            assert db.query(RestartBoundary).count() == 1

    app.dependency_overrides.clear()
