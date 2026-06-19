from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

from app.models.geo_event import GeoEventStatus, GeoEventType, GeoPlanetEvent
from app.services.geo_events.base import clamp01, clamp_latitude, normalize_longitude

# Maps loose / upstream type strings onto the canonical GeoEventType union.
_TYPE_ALIASES: dict[str, GeoEventType] = {
    "quake": "earthquake",
    "earthquakes": "earthquake",
    "fire": "wildfire",
    "wildfires": "wildfire",
    "fires": "wildfire",
    "storm_system": "storm",
    "cyclone": "storm",
    "hurricane": "storm",
    "tropical_storm": "storm",
    "heat": "heatwave",
    "heat_wave": "heatwave",
    "pollution_spike": "pollution",
    "air_quality": "air_quality_alert",
    "aqi": "air_quality_alert",
    "volcano": "volcanic_activity",
    "eruption": "volcanic_activity",
    "flooding": "flood",
    "good_news": "good_news",
    "cooperation": "good_news",
    "renewable": "renewable_boost",
    "ocean": "ocean_recovery",
    "biodiversity": "biodiversity_gain",
    "solar": "solar_storm",
    "neural": "neural_burst",
    "climate": "climate_alert",
}

_VALID_TYPES = set(GeoEventType.__args__)  # type: ignore[attr-defined]
_VALID_STATUS = set(GeoEventStatus.__args__)  # type: ignore[attr-defined]


def normalize_type(raw: str | None) -> GeoEventType:
    if not raw:
        return "climate_alert"
    key = raw.strip().lower().replace(" ", "_")
    if key in _VALID_TYPES:
        return key  # type: ignore[return-value]
    return _TYPE_ALIASES.get(key, "climate_alert")


def normalize_status(raw: str | None, default: GeoEventStatus = "recent") -> GeoEventStatus:
    if not raw:
        return default
    key = raw.strip().lower()
    if key in _VALID_STATUS:
        return key  # type: ignore[return-value]
    return default


def build_event(
    *,
    id: str,
    type: str,
    label: str,
    latitude: float,
    longitude: float,
    intensity: float,
    timestamp: datetime | None = None,
    status: str = "recent",
    description: str | None = None,
    magnitude: float | None = None,
    source: str | None = None,
    source_url: str | None = None,
    country: str | None = None,
    region: str | None = None,
    city: str | None = None,
) -> GeoPlanetEvent | None:
    """Validate + coerce raw fields into a GeoPlanetEvent, dropping junk rows.

    Returns ``None`` when coordinates are non-finite, so a single malformed
    upstream record can never break a whole batch.
    """
    try:
        raw_lat = float(latitude)
        raw_lon = float(longitude)
    except (TypeError, ValueError):
        return None
    if not (math.isfinite(raw_lat) and math.isfinite(raw_lon)):  # NaN / inf guard
        return None
    lat = clamp_latitude(raw_lat)
    lon = normalize_longitude(raw_lon)
    return GeoPlanetEvent(
        id=id,
        timestamp=timestamp or datetime.now(timezone.utc),
        type=normalize_type(type),
        label=label,
        description=description,
        latitude=lat,
        longitude=lon,
        intensity=clamp01(float(intensity)),
        magnitude=magnitude,
        source=source,
        source_url=source_url,
        country=country,
        region=region,
        city=city,
        status=normalize_status(status),
    )


# NASA EONET category id -> canonical GeoEventType.
_EONET_CATEGORY: dict[str, GeoEventType] = {
    "wildfires": "wildfire",
    "severeStorms": "storm",
    "volcanoes": "volcanic_activity",
    "floods": "flood",
    "drought": "drought",
    "dustHaze": "air_quality_alert",
    "earthquakes": "earthquake",
    "seaLakeIce": "climate_alert",
    "snow": "climate_alert",
    "temperatureExtremes": "heatwave",
    "manmade": "climate_alert",
    "waterColor": "climate_alert",
    "landslides": "climate_alert",
}


def _last_point(geometry: list[Any]) -> tuple[float, float] | None:
    """Extract a [lon, lat] pair from an EONET geometry array (latest entry)."""
    if not geometry:
        return None
    coords = (geometry[-1] or {}).get("coordinates")
    # Walk nested coordinate lists (Point / Polygon) down to the first pair.
    while isinstance(coords, list) and coords and isinstance(coords[0], list):
        coords = coords[0]
    if isinstance(coords, list) and len(coords) >= 2:
        try:
            return float(coords[0]), float(coords[1])
        except (TypeError, ValueError):
            return None
    return None


def normalize_eonet_event(event: dict[str, Any]) -> GeoPlanetEvent | None:
    """Normalize a single NASA EONET v3 event."""
    try:
        point = _last_point(event.get("geometry") or [])
        if point is None:
            return None
        lon, lat = point
        categories = event.get("categories") or []
        cat_id = categories[0].get("id") if categories else None
        etype = _EONET_CATEGORY.get(str(cat_id), "climate_alert")
        sources = event.get("sources") or []
        source_url = sources[0].get("url") if sources else event.get("link")
        return build_event(
            id=f"eonet-{event.get('id', lat)}",
            type=etype,
            label=event.get("title") or "Natural event",
            description=(categories[0].get("title") if categories else None),
            latitude=lat,
            longitude=lon,
            intensity=0.6,  # EONET carries no magnitude; use a moderate default
            source="NASA EONET",
            source_url=source_url,
            status="live",
        )
    except (TypeError, ValueError, KeyError, IndexError):
        return None


# GDACS event-type code -> canonical GeoEventType.
_GDACS_TYPE: dict[str, GeoEventType] = {
    "EQ": "earthquake",
    "TC": "storm",
    "FL": "flood",
    "VO": "volcanic_activity",
    "DR": "drought",
    "WF": "wildfire",
}

_GDACS_ALERT_INTENSITY: dict[str, float] = {"green": 0.35, "orange": 0.65, "red": 0.9}


def normalize_gdacs_feature(feature: dict[str, Any]) -> GeoPlanetEvent | None:
    """Normalize a single GDACS GeoJSON feature."""
    try:
        geometry = feature.get("geometry") or {}
        coords = geometry.get("coordinates") or []
        if len(coords) < 2:
            return None
        lon, lat = float(coords[0]), float(coords[1])
        props = feature.get("properties") or {}
        etype = _GDACS_TYPE.get(str(props.get("eventtype")).upper(), "climate_alert")
        alert = str(props.get("alertlevel", "")).lower()
        intensity = _GDACS_ALERT_INTENSITY.get(alert, 0.5)
        name = props.get("name") or props.get("eventname") or "Disaster alert"
        url = props.get("url")
        if isinstance(url, dict):
            url = url.get("report") or url.get("details")
        return build_event(
            id=f"gdacs-{props.get('eventid', name)}-{props.get('episodeid', '')}",
            type=etype,
            label=str(name),
            description=props.get("htmldescription") or props.get("description"),
            latitude=lat,
            longitude=lon,
            intensity=intensity,
            source="GDACS",
            source_url=url if isinstance(url, str) else None,
            country=props.get("country"),
            status="live",
        )
    except (TypeError, ValueError, KeyError):
        return None


def normalize_usgs_feature(feature: dict[str, Any]) -> GeoPlanetEvent | None:
    """Normalize a single USGS earthquake GeoJSON feature."""
    try:
        props = feature.get("properties") or {}
        geometry = feature.get("geometry") or {}
        coords = geometry.get("coordinates") or []
        if len(coords) < 2:
            return None
        lon, lat = float(coords[0]), float(coords[1])
        magnitude = props.get("mag")
        magnitude = float(magnitude) if magnitude is not None else None
        # Earthquake "intensity" mapped from magnitude (~M2.5 .. M8 -> 0..1).
        intensity = 0.0 if magnitude is None else max(0.0, min(1.0, (magnitude - 2.5) / 5.5))
        ms = props.get("time")
        timestamp = (
            datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)
            if isinstance(ms, (int, float))
            else datetime.now(timezone.utc)
        )
        place = props.get("place") or "Earthquake"
        return build_event(
            id=f"usgs-{feature.get('id', place)}",
            type="earthquake",
            label=props.get("title") or f"M{magnitude} earthquake" if magnitude else "Earthquake detected",
            description=place,
            latitude=lat,
            longitude=lon,
            intensity=intensity,
            magnitude=magnitude,
            timestamp=timestamp,
            source="USGS",
            source_url=props.get("url"),
            region=place,
            status="live",
        )
    except (TypeError, ValueError, KeyError):
        return None
