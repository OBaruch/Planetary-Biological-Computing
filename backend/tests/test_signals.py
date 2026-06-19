from __future__ import annotations

from app.services.data_sources.signal_service import _merge, derive_geo_signals
from app.services.data_sources.signals.base import SignalContribution
from app.services.data_sources.signals.noaa_swpc import kp_from_rows
from app.services.geo_events.normalizer import build_event
from app.services.planet_data import PlanetDataProvider


def test_merge_priority_prefers_ground_stations() -> None:
    contributions = [
        SignalContribution("open_meteo", {"air_quality_index": 0.3}),
        SignalContribution("openaq", {"air_quality_index": 0.9}),
    ]
    overlay, provenance = _merge(contributions)
    assert overlay["air_quality_index"] == 0.9  # openaq outranks open_meteo
    assert provenance["air_quality_index"] == "openaq"


def test_derive_geo_signals_from_earthquakes() -> None:
    quake = build_event(
        id="usgs-1",
        type="earthquake",
        label="M5",
        latitude=10.0,
        longitude=20.0,
        intensity=0.5,
        magnitude=5.0,
        source="USGS",
        status="live",
    )
    fields, provenance = derive_geo_signals([quake], {"usgs"})
    assert "earthquake_frequency" in fields
    assert fields["earthquake_magnitude"] == 5.0
    assert provenance["earthquake_magnitude"] == "usgs"


def test_derive_geo_signals_ignores_inactive_source() -> None:
    quake = build_event(
        id="usgs-1",
        type="earthquake",
        label="M5",
        latitude=10.0,
        longitude=20.0,
        intensity=0.5,
        magnitude=5.0,
        source="USGS",
        status="live",
    )
    fields, provenance = derive_geo_signals([quake], set())  # usgs not active
    assert fields == {}
    assert provenance == {}


def test_live_overlay_applies_and_marks_pending() -> None:
    provider = PlanetDataProvider(data_mode="live")
    pending = provider.next({}, {})
    assert pending.source_mode == "live-pending"

    live = provider.next({"air_quality_index": 0.8}, {"air_quality_index": "openaq"})
    assert live.air_quality_index == 0.8
    assert live.source_mode == "live"


def test_demo_mode_ignores_overlay() -> None:
    provider = PlanetDataProvider(data_mode="demo")
    inputs = provider.next({"air_quality_index": 0.99})
    assert inputs.source_mode == "demo"


def test_kp_from_rows_handles_dict_and_array_forms() -> None:
    # SWPC's real payload is a list of dicts.
    dict_rows = [
        {"time_tag": "2026-06-10T00:00:00", "Kp": 2.0, "a_running": 7, "station_count": 8},
        {"time_tag": "2026-06-17T15:00:00", "Kp": 5.33, "a_running": 5, "station_count": 8},
    ]
    assert kp_from_rows(dict_rows) == 5.33
    # Legacy array form (header + rows) is handled too.
    array_rows = [["time_tag", "Kp", "a_running", "station_count"], ["2026-06-17", "4", "27", "8"]]
    assert kp_from_rows(array_rows) == 4.0
    # Malformed inputs degrade to None.
    assert kp_from_rows([]) is None
    assert kp_from_rows("nope") is None
