from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.deps import get_db
from app.main import app
from app.models import entities  # noqa: F401


def test_printer_crud_round_trip():
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

    with TestClient(app) as client:
        created = client.post(
            "/api/v1/printers",
            json={
                "name": "Voron",
                "base_url": "http://moonraker.local",
                "api_key": "secret",
                "is_enabled": True,
                "console_watch_enabled": True,
                "retention_hours": 8,
            },
        )

        assert created.status_code == 201
        created_body = created.json()
        assert created_body["name"] == "Voron"
        assert "api_key" not in created_body
        assert created_body["created_at"].endswith("+00:00")

        printer_id = created_body["id"]

        listed = client.get("/api/v1/printers")
        assert listed.status_code == 200
        assert len(listed.json()) == 1

        updated = client.put(
            f"/api/v1/printers/{printer_id}",
            json={"name": "Voron Trident", "retention_hours": 12},
        )
        assert updated.status_code == 200
        assert updated.json()["name"] == "Voron Trident"
        assert updated.json()["retention_hours"] == 12

        deleted = client.delete(f"/api/v1/printers/{printer_id}")
        assert deleted.status_code == 204

        assert client.get("/api/v1/printers").json() == []

    app.dependency_overrides.clear()
