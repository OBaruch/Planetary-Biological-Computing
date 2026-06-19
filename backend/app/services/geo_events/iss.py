from __future__ import annotations

import logging

import httpx

from app.models.geo_event import GeoPlanetEvent
from app.services.geo_events.normalizer import build_event

logger = logging.getLogger(__name__)

# Live ISS position. No API key required.
# Docs: https://wheretheiss.at/w/developer
ISS_URL = "https://api.wheretheiss.at/v1/satellites/25544"


class IssConnector:
    """Fetches the current International Space Station position as one marker."""

    source_id = "iss"
    name = "ISS"

    def __init__(self, url: str = ISS_URL, timeout: float = 10.0) -> None:
        self.url = url
        self.timeout = timeout

    async def fetch(self) -> list[GeoPlanetEvent]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.url, headers={"Accept": "application/json"})
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("[GAIA] ISS fetch failed: %s", exc)
            return []

        try:
            lat = float(payload["latitude"])
            lon = float(payload["longitude"])
        except (KeyError, TypeError, ValueError):
            return []

        event = build_event(
            id="iss-25544",
            type="neural_burst",  # rendered as a distinct, bright moving marker
            label="International Space Station",
            description="Live ISS ground position.",
            latitude=lat,
            longitude=lon,
            intensity=0.85,
            source="ISS",
            source_url="https://wheretheiss.at/",
            status="live",
        )
        return [event] if event is not None else []
