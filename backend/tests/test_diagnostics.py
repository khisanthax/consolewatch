from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.deps import get_db
from app.main import app
from app.models import entities  # noqa: F401


def test_diagnostics_counts_storage_and_excludes_secrets():
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
                "name": "Diagnostics Printer",
                "base_url": "http://moonraker.local",
                "api_key": "secret",
                "is_enabled": True,
                "console_watch_enabled": False,
                "retention_hours": 8,
            },
        )
        assert created.status_code == 201

        response = client.get("/api/v1/diagnostics")
        assert response.status_code == 200
        body = response.json()
        assert body["counts"]["printers"] == 1
        assert "adc" in body["trigger_classifications"]
        assert body["runtime"]["app_name"] == "ConsoleWatch"
        assert "secret" not in response.text

    app.dependency_overrides.clear()
