from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.models.planet import PlanetInputs
from app.services.data_sources.credentials import CredentialStore
from app.services.data_sources.registry import SourceRegistry
from app.services.geo_events import GeoEventService
from app.services.geo_events.demo_events import synthesize_from_simulation
from app.services.geo_events.normalizer import (
    build_event,
    normalize_eonet_event,
    normalize_gdacs_feature,
    normalize_type,
)
from app.services.geo_events.usgs_earthquakes import UsgsEarthquakeConnector


def _planet_inputs(**overrides: float) -> PlanetInputs:
    base = dict(
        global_temperature_anomaly=1.2,
        co2_ppm=424.0,
        methane_index=0.5,
        ocean_temperature_index=0.5,
        sea_level_index=0.5,
        air_quality_index=0.5,
        wildfire_risk_index=0.5,
        drought_index=0.5,
        precipitation_index=0.5,
        storm_intensity_index=0.5,
        earthquake_magnitude=4.0,
        earthquake_frequency=0.2,
        volcanic_activity_index=0.1,
        energy_consumption_index=0.6,
        renewable_energy_ratio=0.4,
        air_traffic_index=0.5,
        urban_activity_index=0.6,
        internet_activity_index=0.7,
        global_news_tension_index=0.4,
        sentiment_index=0.5,
        conflict_index=0.3,
        cooperation_index=0.5,
        planetary_stress_score=0.4,
        biosphere_stability_score=0.6,
        climate_pressure_score=0.4,
        human_pressure_score=0.4,
        recovery_potential_score=0.5,
        chaos_score=0.4,
        resilience_score=0.6,
        active_events=[],
    )
    base.update(overrides)
    return PlanetInputs(**base)


def test_events_live_endpoint_returns_demo_events() -> None:
    # The test app runs in demo mode (see conftest), so the globe is populated
    # with clearly-flagged demo events rather than hitting live connectors.
    client = TestClient(app)
    response = client.get("/api/events/live")
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] >= 1
    assert payload["mode"] == "demo"
    first = payload["events"][0]
    assert -90.0 <= first["latitude"] <= 90.0
    assert -180.0 <= first["longitude"] <= 180.0
    assert 0.0 <= first["intensity"] <= 1.0


def test_state_frame_includes_events_geo() -> None:
    client = TestClient(app)
    payload = client.get("/api/state").json()
    assert "events_geo" in payload
    assert isinstance(payload["events_geo"], list)


def test_normalizer_coerces_and_clamps() -> None:
    assert normalize_type("FIRE") == "wildfire"
    assert normalize_type("unknown-thing") == "climate_alert"
    event = build_event(
        id="x",
        type="quake",
        label="t",
        latitude=200.0,  # out of range -> clamped to 90
        longitude=540.0,  # wraps to 180
        intensity=5.0,  # clamped to 1
    )
    assert event is not None
    assert event.type == "earthquake"
    assert event.latitude == 90.0
    assert event.intensity == 1.0
    assert -180.0 <= event.longitude <= 180.0


def test_build_event_rejects_nan() -> None:
    assert build_event(id="x", type="storm", label="t", latitude=float("nan"), longitude=0.0, intensity=0.5) is None


def test_synthesize_from_active_bias() -> None:
    inputs = _planet_inputs(active_events=["wildfire", "wildfire"], wildfire_risk_index=0.9)
    events = synthesize_from_simulation(inputs, now=datetime.now(timezone.utc))
    ids = {e.id for e in events}
    assert "sim-wildfire" in ids
    wildfire = next(e for e in events if e.id == "sim-wildfire")
    # Two injections strengthen the marker above the single-injection baseline.
    assert wildfire.intensity > 0.55
    assert "sim-climate-wildfire" in ids


def test_service_dedupes_and_caps(tmp_path) -> None:
    registry = SourceRegistry(CredentialStore(tmp_path / "creds.json"))
    service = GeoEventService(registry, data_mode="demo", max_events=5)
    inputs = _planet_inputs(active_events=["earthquake"])
    events = service.current(inputs)
    assert len(events) <= 5
    assert len({e.id for e in events}) == len(events)


def test_strict_live_mode_shows_only_real_events(tmp_path) -> None:
    # With no live cache populated, strict live mode renders an empty globe
    # (no demo fallback) so the user only ever sees real, configured data.
    registry = SourceRegistry(CredentialStore(tmp_path / "creds.json"))
    service = GeoEventService(registry, data_mode="live", max_events=5)
    inputs = _planet_inputs(active_events=["earthquake"])
    assert service.current(inputs) == []


def test_usgs_connector_has_no_key_requirement() -> None:
    connector = UsgsEarthquakeConnector()
    assert connector.source_id == "usgs"
    assert connector.name == "USGS"
    assert "geojson" in connector.url


def test_normalize_eonet_point_event() -> None:
    event = normalize_eonet_event(
        {
            "id": "EONET_1",
            "title": "Wildfire X",
            "categories": [{"id": "wildfires", "title": "Wildfires"}],
            "geometry": [{"date": "2024-01-01", "type": "Point", "coordinates": [-120.0, 38.0]}],
            "sources": [{"url": "http://example.com/fire"}],
        }
    )
    assert event is not None
    assert event.type == "wildfire"
    assert event.source == "NASA EONET"
    assert event.status == "live"
    assert -90.0 <= event.latitude <= 90.0


def test_normalize_eonet_polygon_and_missing_geometry() -> None:
    assert normalize_eonet_event({"id": "x", "geometry": []}) is None
    event = normalize_eonet_event(
        {
            "id": "p",
            "title": "Storm",
            "categories": [{"id": "severeStorms"}],
            "geometry": [{"type": "Polygon", "coordinates": [[[10.0, 20.0], [11.0, 21.0]]]}],
        }
    )
    assert event is not None
    assert event.type == "storm"


def test_normalize_gdacs_feature() -> None:
    event = normalize_gdacs_feature(
        {
            "geometry": {"coordinates": [100.0, -5.0]},
            "properties": {
                "eventtype": "TC",
                "alertlevel": "Red",
                "name": "Cyclone Y",
                "eventid": 123,
            },
        }
    )
    assert event is not None
    assert event.type == "storm"
    assert event.intensity == 0.9
    assert event.source == "GDACS"
