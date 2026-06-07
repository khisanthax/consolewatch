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
            "name": "Search Printer",
            "base_url": "http://moonraker.local",
            "is_enabled": True,
            "console_watch_enabled": True,
            "retention_hours": 4,
        },
    )
    assert response.status_code == 201
    return int(response.json()["id"])


def ingest(client: TestClient, printer_id: int, message: str):
    response = client.post(
        f"/api/v1/console-entries/moonraker-notification?printer_id={printer_id}",
        json={"jsonrpc": "2.0", "method": "notify_gcode_response", "params": [message]},
    )
    assert response.status_code == 201
    return response


def test_global_search_finds_rolling_manual_and_preserved_entries_and_exports_text():
    client = make_client()
    with client:
        printer_id = create_printer(client)
        session = client.post("/api/v1/sessions", json={"printer_id": printer_id, "label": "Search session"}).json()
        ingest(client, printer_id, "!! Heater error")
        client.post(f"/api/v1/sessions/{session['id']}/save")

        results = client.get("/api/v1/search", params={"search": "Heater", "limit": 20})
        assert results.status_code == 200
        collections = {result["collection"] for result in results.json()}
        assert {"rolling", "manual_session", "preserved_capture"}.issubset(collections)

        search_export = client.get("/api/v1/exports/search.txt", params={"search": "Heater"})
        assert search_export.status_code == 200
        assert "ConsoleWatch Search Export" in search_export.text
        assert "!! Heater error" in search_export.text

        session_export = client.get(f"/api/v1/exports/manual-session/{session['id']}.txt")
        assert session_export.status_code == 200
        assert "ConsoleWatch Manual Session Export" in session_export.text
        assert "Search session" in session_export.text

        capture_id = client.get("/api/v1/preserved-captures").json()[0]["id"]
        capture_export = client.get(f"/api/v1/exports/preserved-capture/{capture_id}.txt")
        assert capture_export.status_code == 200
        assert "ConsoleWatch Preserved Capture Export" in capture_export.text
        assert "!! Heater error" in capture_export.text

    app.dependency_overrides.clear()
