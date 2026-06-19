from __future__ import annotations

from app.services.data_sources.credentials import CredentialStore


def test_set_get_mask_delete(tmp_path) -> None:
    store = CredentialStore(tmp_path / "creds.json")
    assert store.get_secrets("firms", ["map_key"]) == {}
    assert not store.is_configured("firms", ["map_key"])

    store.set("firms", {"map_key": "ABCD1234"}, enabled=True)
    assert store.is_configured("firms", ["map_key"])
    assert store.get_secrets("firms", ["map_key"])["map_key"] == "ABCD1234"
    assert store.enabled_flag("firms") is True

    masked = store.masked("firms", ["map_key"])
    assert masked["map_key"].endswith("1234")
    assert "ABCD" not in masked["map_key"]  # only the last 4 chars are revealed

    store.set_enabled("firms", False)
    assert store.enabled_flag("firms") is False

    store.delete("firms")
    assert store.get_secrets("firms", ["map_key"]) == {}


def test_persists_across_instances(tmp_path) -> None:
    path = tmp_path / "creds.json"
    CredentialStore(path).set("openweather", {"api_key": "key12345"})
    assert CredentialStore(path).get_secrets("openweather", ["api_key"])["api_key"] == "key12345"


def test_no_key_source_is_configured(tmp_path) -> None:
    store = CredentialStore(tmp_path / "creds.json")
    # A source with no required fields is always "configured".
    assert store.is_configured("usgs", [])


def test_env_fallback(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("GAIA_KEY_FIRMS_MAP_KEY", "envkey9999")
    store = CredentialStore(tmp_path / "creds.json")
    assert store.get_secrets("firms", ["map_key"])["map_key"] == "envkey9999"
    assert store.is_configured("firms", ["map_key"])
