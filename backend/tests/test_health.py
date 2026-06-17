from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "session_id" in payload
    assert "cl_sdk_available" in payload
    assert payload["version"]


def test_state_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/api/state")
    assert response.status_code == 200
    payload = response.json()
    assert payload["session_id"]
    assert "planet_state" in payload


def test_status_config_and_sessions_endpoints() -> None:
    client = TestClient(app)
    status = client.get("/api/status")
    config = client.get("/api/config")
    sessions = client.get("/api/sessions")
    assert status.status_code == 200
    assert config.status_code == 200
    assert sessions.status_code == 200
    assert "history_limit" in status.json()
    assert "cl_sdk_available" in config.json()
