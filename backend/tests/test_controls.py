from fastapi.testclient import TestClient

from app.main import app


def test_start_stop_are_idempotent() -> None:
    client = TestClient(app)
    first = client.post("/api/control/start")
    second = client.post("/api/control/start")
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["message"] == "Simulation already running"

    first_stop = client.post("/api/control/stop")
    second_stop = client.post("/api/control/stop")
    assert first_stop.status_code == 200
    assert second_stop.status_code == 200
    assert second_stop.json()["message"] == "Simulation already stopped"


def test_reset_endpoint() -> None:
    client = TestClient(app)
    response = client.post("/api/control/reset")
    assert response.status_code == 200
    assert response.json()["ok"] is True
    state = client.get("/api/state").json()
    assert state["tick"] == 0


def test_demo_event_payload_valid_and_invalid() -> None:
    client = TestClient(app)
    valid = client.post(
        "/api/control/demo-event",
        json={"type": "ocean_recovery", "intensity": 0.8, "duration_seconds": 10},
    )
    invalid_type = client.post(
        "/api/control/demo-event",
        json={"type": "fake_event", "intensity": 0.8, "duration_seconds": 10},
    )
    invalid_range = client.post(
        "/api/control/demo-event",
        json={"type": "heatwave", "intensity": 1.4, "duration_seconds": 10},
    )
    assert valid.status_code == 200
    assert invalid_type.status_code == 422
    assert invalid_range.status_code == 422


def test_history_limit() -> None:
    client = TestClient(app)
    response = client.get("/api/history?limit=2")
    assert response.status_code == 200
    assert len(response.json()) <= 2
