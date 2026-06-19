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

AIR_POLLUTION_URL = "https://api.openweathermap.org/data/2.5/air_pollution"


class OpenWeatherConnector(SignalConnector):
    """Real-time air pollution sampled across world cities (requires API key).

    OpenWeather returns an AQI band of 1 (good) .. 5 (very poor) per location;
    averaged and normalized into ``air_quality_index``.
    """

    source_id = "openweather"
    name = "OpenWeatherMap"

    def __init__(self, api_key: str, timeout: float = 10.0) -> None:
        self.api_key = api_key
        self.timeout = timeout

    async def fetch(self) -> SignalContribution | None:
        if not self.api_key:
            return None
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                tasks = [
                    client.get(
                        AIR_POLLUTION_URL,
                        params={"lat": p.lat, "lon": p.lon, "appid": self.api_key},
                    )
                    for p in WORLD_SAMPLE_POINTS
                ]
                responses = await asyncio.gather(*tasks, return_exceptions=True)
        except httpx.HTTPError as exc:
            logger.warning("[GAIA] OpenWeather fetch failed: %s", exc)
            return None

        bands: list[int] = []
        for resp in responses:
            if isinstance(resp, Exception):
                continue
            try:
                resp.raise_for_status()
                aqi = resp.json()["list"][0]["main"]["aqi"]
                bands.append(int(aqi))
            except (httpx.HTTPError, KeyError, IndexError, ValueError, TypeError):
                continue

        if not bands:
            return None
        # AQI band 1..5 -> 0..1.
        normalized = (sum(bands) / len(bands) - 1.0) / 4.0
        return SignalContribution(
            source_id=self.source_id,
            fields={"air_quality_index": max(0.0, min(1.0, normalized))},
            detail=f"{len(bands)} cities sampled",
        )
