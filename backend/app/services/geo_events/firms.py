from __future__ import annotations

import csv
import io
import logging

import httpx

from app.models.geo_event import GeoPlanetEvent
from app.services.geo_events.normalizer import build_event

logger = logging.getLogger(__name__)

# NASA FIRMS area API (CSV). Requires a free MAP_KEY.
# Docs: https://firms.modaps.eosdis.nasa.gov/api/area/
FIRMS_BASE = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"


class FirmsConnector:
    """Fetches near-real-time active fire detections from NASA FIRMS.

    Requires a free ``map_key``. Returns an empty list on any failure (missing
    key, network, HTTP error, malformed CSV) so the globe simply shows no fires.
    """

    source_id = "firms"
    name = "NASA FIRMS"

    def __init__(
        self,
        map_key: str,
        *,
        sensor: str = "VIIRS_SNPP_NRT",
        day_range: int = 1,
        timeout: float = 12.0,
        limit: int = 120,
    ) -> None:
        self.map_key = map_key
        self.sensor = sensor
        self.day_range = day_range
        self.timeout = timeout
        self.limit = limit

    @property
    def url(self) -> str:
        return f"{FIRMS_BASE}/{self.map_key}/{self.sensor}/world/{self.day_range}"

    async def fetch(self) -> list[GeoPlanetEvent]:
        if not self.map_key:
            return []
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.url, headers={"Accept": "text/csv"})
                response.raise_for_status()
                text = response.text
        except httpx.HTTPError as exc:
            logger.warning("[GAIA] FIRMS fetch failed: %s", exc)
            return []

        # An invalid key returns an HTML/error body rather than CSV.
        if not text or "latitude" not in text.splitlines()[0].lower():
            logger.warning("[GAIA] FIRMS returned a non-CSV body (check MAP_KEY).")
            return []

        events: list[GeoPlanetEvent] = []
        for row in csv.DictReader(io.StringIO(text)):
            try:
                lat = float(row["latitude"])
                lon = float(row["longitude"])
            except (KeyError, TypeError, ValueError):
                continue
            frp = _safe_float(row.get("frp"))
            intensity = max(0.2, min(1.0, frp / 50.0)) if frp is not None else 0.4
            acq = f"{row.get('acq_date', '')} {row.get('acq_time', '')}".strip()
            event = build_event(
                id=f"firms-{row.get('latitude')}-{row.get('longitude')}-{acq}",
                type="wildfire",
                label="Active fire detection",
                description=f"FIRMS {self.sensor} · FRP {frp:.0f} MW" if frp is not None else "FIRMS detection",
                latitude=lat,
                longitude=lon,
                intensity=intensity,
                source="NASA FIRMS",
                source_url="https://firms.modaps.eosdis.nasa.gov/",
                status="live",
            )
            if event is not None:
                events.append(event)
        # Strongest fires first so the cap keeps the most significant.
        events.sort(key=lambda e: e.intensity, reverse=True)
        return events[: self.limit]


def _safe_float(value: object) -> float | None:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
