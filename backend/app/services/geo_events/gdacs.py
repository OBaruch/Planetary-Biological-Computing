from __future__ import annotations

import logging

import httpx

from app.models.geo_event import GeoPlanetEvent
from app.services.geo_events.normalizer import normalize_gdacs_feature

logger = logging.getLogger(__name__)

# Global Disaster Alert and Coordination System. No API key required.
# Docs: https://www.gdacs.org/
GDACS_URL = "https://www.gdacs.org/gdacsapi/api/events/geteventlist/MAP"


class GdacsConnector:
    """Fetches current global disaster alerts from GDACS."""

    source_id = "gdacs"
    name = "GDACS"

    def __init__(self, url: str = GDACS_URL, timeout: float = 8.0, limit: int = 60) -> None:
        self.url = url
        self.timeout = timeout
        self.limit = limit

    async def fetch(self) -> list[GeoPlanetEvent]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.url, headers={"Accept": "application/json"})
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("[GAIA] GDACS fetch failed: %s", exc)
            return []

        events: list[GeoPlanetEvent] = []
        for feature in payload.get("features") or []:
            event = normalize_gdacs_feature(feature)
            if event is not None:
                events.append(event)
        events.sort(key=lambda e: e.intensity, reverse=True)
        return events[: self.limit]
