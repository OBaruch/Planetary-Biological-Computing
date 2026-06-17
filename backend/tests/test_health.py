from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "session_id" in payload


def test_state_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/api/state")
    assert response.status_code == 200
    payload = response.json()
    assert payload["session_id"]
    assert "planet_state" in payload
