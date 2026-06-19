from __future__ import annotations

from typing import Protocol

from app.models.geo_event import GeoPlanetEvent


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def normalize_range(value: float, low: float, high: float) -> float:
    """Map ``value`` from [low, high] into [0, 1] with clamping."""
    if high <= low:
        return 0.0
    return clamp01((value - low) / (high - low))


def clamp_latitude(lat: float) -> float:
    return max(-90.0, min(90.0, lat))


def normalize_longitude(lon: float) -> float:
    return (lon + 180.0) % 360.0 - 180.0


class GeoEventConnector(Protocol):
    """Common shape for any live geolocated data source.

    Connectors must be resilient: a failure (no network, no API key,
    timeout, bad payload) should resolve to an empty list, never an
    exception, so the globe simply shows fewer markers.

    ``source_id`` matches the key in the source catalog; ``name`` is the
    human label stamped onto each event's ``source`` field.
    """

    source_id: str
    name: str

    async def fetch(self) -> list[GeoPlanetEvent]:
        ...
