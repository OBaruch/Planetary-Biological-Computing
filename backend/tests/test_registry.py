from __future__ import annotations

from app.services.data_sources.credentials import CredentialStore
from app.services.data_sources.registry import SourceRegistry


def _registry(tmp_path) -> SourceRegistry:
    return SourceRegistry(CredentialStore(tmp_path / "creds.json"))


def test_no_key_source_auto_active(tmp_path) -> None:
    reg = _registry(tmp_path)
    assert reg.is_configured("usgs")
    assert reg.is_enabled("usgs")
    assert reg.is_active("usgs")
    assert "usgs" in reg.active_ids()
    assert reg.build_geo_connector("usgs") is not None


def test_key_source_not_active_until_configured(tmp_path) -> None:
    store = CredentialStore(tmp_path / "creds.json")
    reg = SourceRegistry(store)
    assert not reg.is_configured("firms")
    assert not reg.is_active("firms")
    assert reg.build_geo_connector("firms") is None

    store.set("firms", {"map_key": "K123"})
    assert reg.is_configured("firms")
    assert reg.is_active("firms")
    assert reg.build_geo_connector("firms") is not None


def test_disable_no_key_source(tmp_path) -> None:
    store = CredentialStore(tmp_path / "creds.json")
    reg = SourceRegistry(store)
    store.set_enabled("eonet", False)
    assert not reg.is_active("eonet")
    assert "eonet" not in reg.active_ids()


def test_status_never_exposes_secret(tmp_path) -> None:
    store = CredentialStore(tmp_path / "creds.json")
    reg = SourceRegistry(store)
    store.set("openweather", {"api_key": "supersecret123"})
    status = reg.status("openweather")
    assert status is not None
    assert status.configured
    assert "supersecret123" not in str(status.model_dump())
    assert status.masked_credentials["api_key"].endswith("t123")


def test_active_signal_connectors_excludes_unconfigured_key_source(tmp_path) -> None:
    reg = _registry(tmp_path)
    active_ids = {c.source_id for c in reg.active_signal_connectors()}
    # No-key signal sources are active; key-based ones (openaq/openweather) are not.
    assert {"open_meteo", "gdelt", "noaa_swpc"} <= active_ids
    assert "openaq" not in active_ids
    assert "openweather" not in active_ids
