from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


def test_dashboard_empty_state(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "empty.sqlite3"))
    get_settings.cache_clear()
    client = TestClient(app)
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    assert response.json()["repos"] == []
