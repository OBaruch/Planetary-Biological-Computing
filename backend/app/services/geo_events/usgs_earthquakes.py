from __future__ import annotations

import logging

import httpx

from app.models.geo_event import GeoPlanetEvent
from app.services.geo_events.normalizer import normalize_usgs_feature

logger = logging.getLogger(__name__)

# Public USGS GeoJSON feed: significant + M2.5 events over the past day.
# Docs: https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php
USGS_FEED_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson"


class UsgsEarthquakeConnector:
    """Fetches recent earthquakes from the public USGS GeoJSON feed.

    No API key required. Always returns a list; on any failure it logs and
    returns an empty list.
    """

    source_id = "usgs"
    name = "USGS"

    def __init__(self, url: str = USGS_FEED_URL, timeout: float = 6.0, limit: int = 60) -> None:
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
            logger.warning("[GAIA] USGS earthquake fetch failed: %s", exc)
            return []

        features = payload.get("features") or []
        events: list[GeoPlanetEvent] = []
        for feature in features:
            event = normalize_usgs_feature(feature)
            if event is not None:
                events.append(event)
        # Strongest first so caps keep the most relevant quakes.
        events.sort(key=lambda e: e.intensity, reverse=True)
        return events[: self.limit]
