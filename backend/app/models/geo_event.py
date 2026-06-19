from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_validator


GeoEventType = Literal[
    "earthquake",
    "wildfire",
    "storm",
    "heatwave",
    "pollution",
    "conflict",
    "good_news",
    "renewable_boost",
    "ocean_recovery",
    "biodiversity_gain",
    "solar_storm",
    "neural_burst",
    "climate_alert",
    "volcanic_activity",
    "air_quality_alert",
    "flood",
    "drought",
]

GeoEventStatus = Literal["live", "recent", "simulated", "archived"]


class GeoPlanetEvent(BaseModel):
    """A geolocated planetary event ready to render on the 3D globe.

    The model is intentionally permissive about optional metadata so the
    frontend can render whatever it receives, but it strictly validates the
    coordinate / intensity bounds so a marker never lands off-sphere.
    """

    id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    type: GeoEventType
    label: str
    description: str | None = None

    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)

    intensity: float = Field(default=0.5, ge=0.0, le=1.0)
    magnitude: float | None = None
    source: str | None = None
    source_url: str | None = None

    country: str | None = None
    region: str | None = None
    city: str | None = None

    status: GeoEventStatus = "recent"

    @field_validator("latitude")
    @classmethod
    def _clamp_lat(cls, value: float) -> float:
        return max(-90.0, min(90.0, value))

    @field_validator("longitude")
    @classmethod
    def _wrap_lon(cls, value: float) -> float:
        # Normalize to [-180, 180] so connectors can pass raw 0..360 values.
        wrapped = (value + 180.0) % 360.0 - 180.0
        return wrapped

    @field_validator("intensity")
    @classmethod
    def _clamp_intensity(cls, value: float) -> float:
        return max(0.0, min(1.0, value))


class GeoEventsResponse(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    count: int
    mode: str
    sources: list[str] = Field(default_factory=list)
    events: list[GeoPlanetEvent] = Field(default_factory=list)
