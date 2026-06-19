from __future__ import annotations

import logging

import httpx

from app.services.data_sources.signals.base import (
    WORLD_SAMPLE_POINTS,
    SignalConnector,
    SignalContribution,
)

logger = logging.getLogger(__name__)

AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _coords() -> tuple[str, str]:
    lats = ",".join(f"{p.lat:.4f}" for p in WORLD_SAMPLE_POINTS)
    lons = ",".join(f"{p.lon:.4f}" for p in WORLD_SAMPLE_POINTS)
    return lats, lons


def _as_list(payload: object) -> list[dict]:
    if isinstance(payload, list):
        return [p for p in payload if isinstance(p, dict)]
    if isinstance(payload, dict):
        return [payload]
    return []


class OpenMeteoConnector(SignalConnector):
    """Free (no-key) global weather + air-quality signals.

    Samples a fixed set of world cities in two batched requests and averages
    into ``air_quality_index`` and ``precipitation_index``.
    """

    source_id = "open_meteo"
    name = "Open-Meteo"

    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout

    async def fetch(self) -> SignalContribution | None:
        lats, lons = _coords()
        fields: dict[str, float] = {}
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                aq = await client.get(
                    AIR_QUALITY_URL,
                    params={"latitude": lats, "longitude": lons, "current": "us_aqi"},
                )
                aq.raise_for_status()
                aqi_values = [
                    float(item["current"]["us_aqi"])
                    for item in _as_list(aq.json())
                    if isinstance(item.get("current"), dict)
                    and item["current"].get("us_aqi") is not None
                ]
                if aqi_values:
                    fields["air_quality_index"] = _clamp01(
                        (sum(aqi_values) / len(aqi_values)) / 300.0
                    )

                fc = await client.get(
                    FORECAST_URL,
                    params={"latitude": lats, "longitude": lons, "current": "precipitation"},
                )
                fc.raise_for_status()
                precip = [
                    float(item["current"]["precipitation"])
                    for item in _as_list(fc.json())
                    if isinstance(item.get("current"), dict)
                    and item["current"].get("precipitation") is not None
                ]
                if precip:
                    fields["precipitation_index"] = _clamp01((sum(precip) / len(precip)) / 4.0)
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            logger.warning("[GAIA] Open-Meteo fetch failed: %s", exc)
            return None

        if not fields:
            return None
        return SignalContribution(
            source_id=self.source_id,
            fields=fields,
            detail=f"{len(WORLD_SAMPLE_POINTS)} cities sampled",
        )
