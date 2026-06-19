from __future__ import annotations

import asyncio
import logging
import time

from app.models.geo_event import GeoPlanetEvent
from app.services.data_sources.registry import SourceRegistry
from app.services.data_sources.signals.base import SignalContribution

logger = logging.getLogger(__name__)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


# Lower number wins when several sources feed the same field (physical
# ground stations beat models).
_SIGNAL_PRIORITY: dict[str, int] = {"openaq": 1, "openweather": 2, "open_meteo": 3}


def _merge(contributions: list[SignalContribution]) -> tuple[dict[str, float], dict[str, str]]:
    overlay: dict[str, float] = {}
    provenance: dict[str, str] = {}
    # Process lowest priority first so the highest-priority source overwrites.
    ordered = sorted(
        contributions, key=lambda c: _SIGNAL_PRIORITY.get(c.source_id, 5), reverse=True
    )
    for contribution in ordered:
        for field, value in contribution.fields.items():
            overlay[field] = value
            provenance[field] = contribution.source_id
    return overlay, provenance


# Maps event ``source`` label -> the catalog source_id (for provenance).
_GEO_SOURCE_IDS: dict[str, str] = {
    "USGS": "usgs",
    "NASA FIRMS": "firms",
    "GDACS": "gdacs",
    "NASA EONET": "eonet",
}


def derive_geo_signals(
    events: list[GeoPlanetEvent], active_ids: set[str]
) -> tuple[dict[str, float], dict[str, str]]:
    """Derive scalar planet signals from geolocated events of active sources.

    e.g. recent earthquakes -> earthquake_frequency/magnitude (USGS),
    active fire detections -> wildfire_risk_index (FIRMS),
    volcanic events -> volcanic_activity_index (EONET/GDACS).
    """
    overlay: dict[str, float] = {}
    provenance: dict[str, str] = {}

    quakes = [e for e in events if e.type == "earthquake" and _GEO_SOURCE_IDS.get(e.source or "") == "usgs"]
    if "usgs" in active_ids and quakes:
        overlay["earthquake_frequency"] = _clamp01(len(quakes) / 25.0)
        mags = [e.magnitude for e in quakes if e.magnitude is not None]
        if mags:
            overlay["earthquake_magnitude"] = max(mags)
            provenance["earthquake_magnitude"] = "usgs"
        provenance["earthquake_frequency"] = "usgs"

    fires = [e for e in events if e.type == "wildfire" and e.source == "NASA FIRMS"]
    if "firms" in active_ids and fires:
        overlay["wildfire_risk_index"] = _clamp01(0.3 + len(fires) / 120.0)
        provenance["wildfire_risk_index"] = "firms"

    volcanoes = [e for e in events if e.type == "volcanic_activity"]
    volcano_ids = {_GEO_SOURCE_IDS.get(e.source or "") for e in volcanoes}
    active_volcano = next((sid for sid in ("eonet", "gdacs") if sid in volcano_ids and sid in active_ids), None)
    if active_volcano and volcanoes:
        overlay["volcanic_activity_index"] = _clamp01(0.2 + len(volcanoes) / 10.0)
        provenance["volcanic_activity_index"] = active_volcano

    return overlay, provenance


class SignalService:
    """Collects signal contributions from active connectors on a slow interval.

    Mirrors ``GeoEventService``: connectors are polled at most every
    ``refresh_interval_seconds`` (never per simulation tick); the merged overlay
    + provenance are cached and read synchronously inside the loop.
    """

    def __init__(self, registry: SourceRegistry, refresh_interval_seconds: float = 120.0) -> None:
        self.registry = registry
        self.refresh_interval_seconds = refresh_interval_seconds
        self._overlay: dict[str, float] = {}
        self._provenance: dict[str, str] = {}
        self._last_refresh: float | None = None
        self._lock = asyncio.Lock()

    @property
    def overlay(self) -> dict[str, float]:
        return dict(self._overlay)

    @property
    def provenance(self) -> dict[str, str]:
        return dict(self._provenance)

    def _needs_refresh(self) -> bool:
        if self._last_refresh is None:
            return True
        return (time.monotonic() - self._last_refresh) >= self.refresh_interval_seconds

    async def maybe_refresh(self) -> None:
        if self._needs_refresh():
            await self.refresh()

    async def refresh(self, force: bool = False) -> None:
        if not force and not self._needs_refresh():
            return
        async with self._lock:
            if not force and not self._needs_refresh():
                return
            connectors = self.registry.active_signal_connectors()
            contributions: list[SignalContribution] = []
            for connector in connectors:
                try:
                    contribution = await connector.fetch()
                except Exception as exc:  # connectors should already be safe
                    logger.warning("[GAIA] Signal connector %s failed: %s", connector.source_id, exc)
                    self.registry.record_health(connector.source_id, ok=False, error=str(exc))
                    continue
                if contribution is not None and contribution.fields:
                    contributions.append(contribution)
                    self.registry.record_health(
                        connector.source_id, ok=True, count=len(contribution.fields)
                    )
                else:
                    self.registry.record_health(
                        connector.source_id, ok=False, error="no data returned"
                    )
            self._overlay, self._provenance = _merge(contributions)
            self._last_refresh = time.monotonic()
            logger.info("[GAIA] Signal refresh complete: %d fields", len(self._overlay))
