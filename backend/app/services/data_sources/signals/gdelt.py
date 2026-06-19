from __future__ import annotations

import logging

import httpx

from app.services.data_sources.signals.base import SignalConnector, SignalContribution

logger = logging.getLogger(__name__)

# GDELT DOC 2.0 timeline-tone. No API key required.
GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


class GdeltConnector(SignalConnector):
    """Global news tone (sentiment) from GDELT, mapped to society indices.

    GDELT "average tone" runs roughly -10 (very negative) .. +10 (very
    positive). We normalize it and derive tension / sentiment / conflict /
    cooperation indices from a single, no-key request.
    """

    source_id = "gdelt"
    name = "GDELT"

    def __init__(self, query: str = "climate OR conflict OR economy", timeout: float = 10.0) -> None:
        self.query = query
        self.timeout = timeout

    async def fetch(self) -> SignalContribution | None:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    GDELT_URL,
                    params={
                        "query": self.query,
                        "mode": "timelinetone",
                        "timespan": "1d",
                        "format": "json",
                    },
                    headers={"Accept": "application/json"},
                )
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("[GAIA] GDELT fetch failed: %s", exc)
            return None

        values: list[float] = []
        for series in payload.get("timeline") or []:
            for point in series.get("data") or []:
                value = point.get("value")
                if value is not None:
                    try:
                        values.append(float(value))
                    except (TypeError, ValueError):
                        continue
        if not values:
            return None

        # Use the most recent samples for a "current mood" reading.
        tone = sum(values[-8:]) / len(values[-8:])
        sentiment = _clamp01((tone + 10.0) / 20.0)
        return SignalContribution(
            source_id=self.source_id,
            fields={
                "sentiment_index": sentiment,
                "global_news_tension_index": _clamp01(1.0 - sentiment),
                "conflict_index": _clamp01(0.5 - tone * 0.05),
                "cooperation_index": _clamp01(0.5 + tone * 0.05),
            },
            detail=f"tone {tone:+.2f}",
        )
