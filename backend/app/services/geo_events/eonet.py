from __future__ import annotations

import logging

import httpx

from app.models.geo_event import GeoPlanetEvent
from app.services.geo_events.normalizer import normalize_eonet_event

logger = logging.getLogger(__name__)

# Open natural events. No API key required.
# Docs: https://eonet.gsfc.nasa.gov/docs/v3
EONET_URL = "https://eonet.gsfc.nasa.gov/api/v3/events?status=open"


class EonetConnector:
    """Fetches open natural events (fires, storms, volcanoes...) from NASA EONET."""

    source_id = "eonet"
    name = "NASA EONET"

    def __init__(self, url: str = EONET_URL, timeout: float = 8.0, limit: int = 80) -> None:
        self.url = url
        self.timeout = timeout
        self.limit = limit

    async def fetch(self) -> list[GeoPlanetEvent]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.url}&limit={self.limit}", headers={"Accept": "application/json"}
                )
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("[GAIA] EONET fetch failed: %s", exc)
            return []

        events: list[GeoPlanetEvent] = []
        for raw in payload.get("events") or []:
            event = normalize_eonet_event(raw)
            if event is not None:
                events.append(event)
        return events[: self.limit]
