from __future__ import annotations

import logging

import httpx

from app.services.data_sources.signals.base import SignalConnector, SignalContribution

logger = logging.getLogger(__name__)

# NOAA SWPC planetary K-index (geomagnetic activity). No API key required.
KP_URL = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"


def kp_from_rows(rows: object) -> float | None:
    """Read the latest Kp value from the SWPC payload.

    SWPC serves this product as a list of dicts ({"time_tag", "Kp", ...}); the
    older array form ([["time_tag","Kp",...], [...]]) is handled defensively.
    """
    if not isinstance(rows, list) or not rows:
        return None
    last = rows[-1]
    try:
        if isinstance(last, dict):
            return float(last.get("Kp", last.get("kp_index")))
        return float(last[1])
    except (IndexError, KeyError, TypeError, ValueError):
        return None


class NoaaSwpcConnector(SignalConnector):
    """Geomagnetic storm activity from NOAA SWPC (planetary Kp index, no key).

    Kp runs 0..9; mapped to ``storm_intensity_index`` as a space-weather
    contribution (a geomagnetic storm reading).
    """

    source_id = "noaa_swpc"
    name = "NOAA SWPC"

    def __init__(self, url: str = KP_URL, timeout: float = 8.0) -> None:
        self.url = url
        self.timeout = timeout

    async def fetch(self) -> SignalContribution | None:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.url, headers={"Accept": "application/json"})
                response.raise_for_status()
                rows = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("[GAIA] NOAA SWPC fetch failed: %s", exc)
            return None

        kp = kp_from_rows(rows)
        if kp is None:
            return None

        return SignalContribution(
            source_id=self.source_id,
            fields={"storm_intensity_index": max(0.0, min(1.0, kp / 9.0))},
            detail=f"Kp {kp:.1f}",
        )
