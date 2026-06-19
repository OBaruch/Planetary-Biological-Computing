from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.data_sources.credentials import CredentialStore
from app.services.data_sources.registry import SourceRegistry


@pytest.fixture
def client(tmp_path, monkeypatch):
    """TestClient with an isolated credential store and a no-op source rebuild.

    rebuild_sources normally force-refreshes connectors (network); we stub it so
    the API contract is tested hermetically.
    """
    runner = app.state.runner
    store = CredentialStore(tmp_path / "creds.json")
    monkeypatch.setattr(runner, "credentials", store)
    monkeypatch.setattr(runner, "registry", SourceRegistry(store))

    async def _noop() -> None:
        return None

    monkeypatch.setattr(runner, "rebuild_sources", _noop)
    return TestClient(app)


def test_list_sources(client) -> None:
    response = client.get("/api/sources")
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 10
    by_id = {s["descriptor"]["id"]: s for s in data["sources"]}
    assert {"usgs", "firms", "openweather", "gdelt"} <= set(by_id)
    assert by_id["usgs"]["active"] is True  # no key needed
    assert by_id["firms"]["active"] is False  # needs a key


def test_put_credentials_masks_secret(client) -> None:
    response = client.put(
        "/api/sources/firms/credentials",
        json={"secrets": {"map_key": "SECRET99"}, "enabled": True},
    )
    assert response.status_code == 200
    status = response.json()
    assert status["configured"] is True
    assert status["active"] is True
    assert "SECRET99" not in response.text
    assert status["masked_credentials"]["map_key"].endswith("T99")


def test_toggle_source(client) -> None:
    response = client.post("/api/sources/eonet/toggle", json={"enabled": False})
    assert response.status_code == 200
    assert response.json()["active"] is False


def test_test_endpoint_reports_missing_credentials(client) -> None:
    response = client.post("/api/sources/firms/test", json={"secrets": {}})
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["error"]


def test_unknown_source_404(client) -> None:
    assert client.post("/api/sources/nope/toggle", json={"enabled": True}).status_code == 404
    assert client.get("/api/sources").status_code == 200
