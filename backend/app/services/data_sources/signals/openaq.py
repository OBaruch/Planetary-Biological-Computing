from __future__ import annotations

import asyncio
import logging

import httpx

from app.services.data_sources.signals.base import (
    WORLD_SAMPLE_POINTS,
    SignalConnector,
    SignalContribution,
)

logger = logging.getLogger(__name__)

LOCATIONS_URL = "https://api.openaq.org/v3/locations"
# PM2.5 is parameter id 2 in OpenAQ v3.
PM25_PARAMETER_ID = 2
# Use a curated subset to stay within free-tier rate limits (2 calls/point).
_SAMPLE = WORLD_SAMPLE_POINTS[:8]


class OpenAqConnector(SignalConnector):
    """Air quality from physical OpenAQ monitoring stations (requires API key).

    For each sample city it finds the nearest PM2.5 station and reads its latest
    value, averaging into ``air_quality_index``. Highest provenance priority
    because these are real ground stations.
    """

    source_id = "openaq"
    name = "OpenAQ"

    def __init__(self, api_key: str, timeout: float = 10.0) -> None:
        self.api_key = api_key
        self.timeout = timeout

    @property
    def _headers(self) -> dict[str, str]:
        return {"X-API-Key": self.api_key, "Accept": "application/json"}

    async def _pm25_near(self, client: httpx.AsyncClient, lat: float, lon: float) -> float | None:
        loc = await client.get(
            LOCATIONS_URL,
            params={
                "coordinates": f"{lat},{lon}",
                "radius": 25000,
                "parameters_id": PM25_PARAMETER_ID,
                "limit": 1,
            },
            headers=self._headers,
        )
        loc.raise_for_status()
        results = loc.json().get("results") or []
        if not results:
            return None
        location_id = results[0].get("id")
        if location_id is None:
            return None
        latest = await client.get(
            f"{LOCATIONS_URL}/{location_id}/latest", headers=self._headers
        )
        latest.raise_for_status()
        for row in latest.json().get("results") or []:
            value = row.get("value")
            if value is not None and float(value) >= 0:
                return float(value)
        return None

    async def fetch(self) -> SignalContribution | None:
        if not self.api_key:
            return None
        values: list[float] = []
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                results = await asyncio.gather(
                    *(self._pm25_near(client, p.lat, p.lon) for p in _SAMPLE),
                    return_exceptions=True,
                )
        except httpx.HTTPError as exc:
            logger.warning("[GAIA] OpenAQ fetch failed: %s", exc)
            return None

        for result in results:
            if isinstance(result, (int, float)):
                values.append(float(result))

        if not values:
            return None
        # Mean PM2.5 (µg/m³) normalized: ~150 µg/m³ is hazardous -> ~1.0.
        normalized = (sum(values) / len(values)) / 150.0
        return SignalContribution(
            source_id=self.source_id,
            fields={"air_quality_index": max(0.0, min(1.0, normalized))},
            detail=f"{len(values)} stations",
        )
