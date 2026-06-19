from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.models.geo_event import GeoEventType, GeoPlanetEvent
from app.models.planet import PlanetInputs
from app.services.geo_events.base import clamp01
from app.services.geo_events.normalizer import build_event


@dataclass(frozen=True)
class _Place:
    city: str
    country: str
    lat: float
    lon: float


# Representative real-world coordinates used to anchor simulated events.
_PLACES: dict[str, _Place] = {
    "mexico_city": _Place("Mexico City", "Mexico", 19.4326, -99.1332),
    "los_angeles": _Place("Los Angeles", "United States", 34.0522, -118.2437),
    "miami": _Place("Miami", "United States", 25.7617, -80.1918),
    "new_delhi": _Place("New Delhi", "India", 28.6139, 77.2090),
    "berlin": _Place("Berlin", "Germany", 52.5200, 13.4050),
    "sydney": _Place("Sydney", "Australia", -33.8688, 151.2093),
    "tokyo": _Place("Tokyo", "Japan", 35.6762, 139.6503),
    "jakarta": _Place("Jakarta", "Indonesia", -6.2088, 106.8456),
    "reykjavik": _Place("Reykjavik", "Iceland", 64.1466, -21.9426),
    "nairobi": _Place("Nairobi", "Kenya", -1.2921, 36.8219),
    "sao_paulo": _Place("Sao Paulo", "Brazil", -23.5505, -46.6333),
    "tromso": _Place("Tromso", "Norway", 69.6492, 18.9553),
}


# Baseline simulated events keep the globe alive even with no biases injected.
_BASELINE: list[tuple[str, GeoEventType, str, float]] = [
    ("mexico_city", "earthquake", "Simulated seismic activity", 0.45),
    ("los_angeles", "wildfire", "Simulated wildfire risk", 0.5),
    ("miami", "storm", "Simulated storm system", 0.4),
    ("new_delhi", "air_quality_alert", "Simulated air quality alert", 0.55),
    ("berlin", "renewable_boost", "Simulated renewable energy surge", 0.42),
    ("sydney", "ocean_recovery", "Simulated ocean recovery signal", 0.4),
    ("nairobi", "biodiversity_gain", "Simulated biodiversity gain", 0.38),
    ("tromso", "solar_storm", "Simulated auroral activity", 0.35),
]


# Maps an injected demo bias name -> (place, event type, label, intensity gain).
_BIAS_MAP: dict[str, tuple[str, GeoEventType, str]] = {
    "heatwave": ("new_delhi", "heatwave", "Heatwave intensifying"),
    "wildfire": ("los_angeles", "wildfire", "Active wildfire front"),
    "earthquake": ("tokyo", "earthquake", "Seismic event detected"),
    "good_news": ("nairobi", "good_news", "Global cooperation signal"),
    "conflict": ("jakarta", "conflict", "Regional tension alert"),
    "renewable_boost": ("berlin", "renewable_boost", "Renewable energy surge"),
    "ocean_recovery": ("sydney", "ocean_recovery", "Ocean recovery signal"),
    "pollution_spike": ("sao_paulo", "pollution", "Air pollution spike"),
    "biodiversity_gain": ("nairobi", "biodiversity_gain", "Biodiversity recovery"),
    "solar_storm": ("reykjavik", "solar_storm", "Geomagnetic storm"),
}


def _place(key: str) -> _Place:
    return _PLACES[key]


def build_demo_events(now: datetime | None = None) -> list[GeoPlanetEvent]:
    """Curated, always-available simulated events with real coordinates."""
    timestamp = now or datetime.now(timezone.utc)
    events: list[GeoPlanetEvent] = []
    for place_key, etype, label, intensity in _BASELINE:
        place = _place(place_key)
        event = build_event(
            id=f"demo-{place_key}-{etype}",
            type=etype,
            label=label,
            description=f"Simulated geolocated demo event near {place.city}.",
            latitude=place.lat,
            longitude=place.lon,
            intensity=intensity,
            timestamp=timestamp,
            source="GAIA-1 demo",
            city=place.city,
            country=place.country,
            status="simulated",
        )
        if event is not None:
            events.append(event)
    return events


def synthesize_from_simulation(
    planet_inputs: PlanetInputs,
    *,
    now: datetime | None = None,
) -> list[GeoPlanetEvent]:
    """Derive geolocated events from active demo biases and planet indices.

    These are clearly flagged ``simulated``. Injected demo events produce
    prominent, higher-intensity markers anchored to representative cities.
    """
    timestamp = now or datetime.now(timezone.utc)
    events: list[GeoPlanetEvent] = []

    # Count duplicate biases so repeated injections strengthen the marker.
    bias_counts: dict[str, int] = {}
    for name in planet_inputs.active_events:
        bias_counts[name] = bias_counts.get(name, 0) + 1

    for name, count in bias_counts.items():
        mapping = _BIAS_MAP.get(name)
        if mapping is None:
            continue
        place_key, etype, label = mapping
        place = _place(place_key)
        intensity = clamp01(0.55 + 0.15 * (count - 1))
        magnitude = None
        if etype == "earthquake":
            magnitude = round(4.5 + intensity * 3.0, 1)
        event = build_event(
            id=f"sim-{name}",
            type=etype,
            label=label,
            description=f"Injected demo event amplifying {name.replace('_', ' ')}.",
            latitude=place.lat,
            longitude=place.lon,
            intensity=intensity,
            magnitude=magnitude,
            timestamp=timestamp,
            source="GAIA-1 demo",
            city=place.city,
            country=place.country,
            status="simulated",
        )
        if event is not None:
            events.append(event)

    # Derive ambient climate alerts from elevated planet indices.
    if planet_inputs.wildfire_risk_index > 0.7:
        place = _place("sao_paulo")
        ev = build_event(
            id="sim-climate-wildfire",
            type="wildfire",
            label="Elevated wildfire risk",
            description="Derived from elevated wildfire risk index.",
            latitude=place.lat,
            longitude=place.lon,
            intensity=clamp01(planet_inputs.wildfire_risk_index),
            timestamp=timestamp,
            source="GAIA-1 derived",
            city=place.city,
            country=place.country,
            status="simulated",
        )
        if ev is not None:
            events.append(ev)

    if planet_inputs.drought_index > 0.7:
        place = _place("nairobi")
        ev = build_event(
            id="sim-climate-drought",
            type="drought",
            label="Drought conditions",
            description="Derived from elevated drought index.",
            latitude=place.lat,
            longitude=place.lon,
            intensity=clamp01(planet_inputs.drought_index),
            timestamp=timestamp,
            source="GAIA-1 derived",
            city=place.city,
            country=place.country,
            status="simulated",
        )
        if ev is not None:
            events.append(ev)

    if planet_inputs.storm_intensity_index > 0.7:
        place = _place("miami")
        ev = build_event(
            id="sim-climate-storm",
            type="storm",
            label="Severe storm activity",
            description="Derived from elevated storm intensity index.",
            latitude=place.lat,
            longitude=place.lon,
            intensity=clamp01(planet_inputs.storm_intensity_index),
            timestamp=timestamp,
            source="GAIA-1 derived",
            city=place.city,
            country=place.country,
            status="simulated",
        )
        if ev is not None:
            events.append(ev)

    return events
