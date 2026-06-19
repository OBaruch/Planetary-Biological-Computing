from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from app.models.geo_event import GeoEventsResponse, GeoPlanetEvent
from app.models.planet import PlanetInputs
from app.services.geo_events.demo_events import build_demo_events, synthesize_from_simulation

if TYPE_CHECKING:
    from app.services.data_sources.registry import SourceRegistry

logger = logging.getLogger(__name__)


class GeoEventService:
    """Aggregates geolocated events from the user's active connectors.

    In ``live`` (strict) mode the globe shows ONLY events fetched from active,
    configured sources — no demo/simulated fallback. In ``demo`` mode it keeps
    the legacy behavior (curated demo events + simulation-derived markers).

    Live connectors are refreshed on a slow interval (never per simulation
    tick); :meth:`current` reads the cached events synchronously.
    """

    def __init__(
        self,
        registry: "SourceRegistry",
        *,
        data_mode: str = "live",
        refresh_interval_seconds: float = 60.0,
        max_events: int = 80,
    ) -> None:
        self.registry = registry
        self.data_mode = data_mode
        self.refresh_interval_seconds = refresh_interval_seconds
        self.max_events = max_events
        self._live_cache: list[GeoPlanetEvent] = []
        self._last_refresh: float | None = None
        self._refresh_lock = asyncio.Lock()

    @property
    def live_sources(self) -> list[str]:
        return sorted({c.name for c in self.registry.active_geo_connectors()})

    @property
    def mode(self) -> str:
        if self.data_mode == "demo":
            return "demo"
        if self._live_cache:
            return "live"
        return "live-pending"

    def _has_connectors(self) -> bool:
        return bool(self.registry.active_geo_connectors())

    def _needs_refresh(self) -> bool:
        if self.data_mode == "demo" or not self._has_connectors():
            return False
        if self._last_refresh is None:
            return True
        return (time.monotonic() - self._last_refresh) >= self.refresh_interval_seconds

    async def refresh_live(self, force: bool = False) -> None:
        """Pull active live connectors into the cache, respecting the interval."""
        if self.data_mode == "demo":
            return
        connectors = self.registry.active_geo_connectors()
        if not connectors:
            self._live_cache = []
            self._last_refresh = time.monotonic()
            return
        if not force and not self._needs_refresh():
            return
        async with self._refresh_lock:
            if not force and not self._needs_refresh():
                return
            collected: list[GeoPlanetEvent] = []
            for connector in connectors:
                try:
                    events = await connector.fetch()
                    collected.extend(events)
                    self.registry.record_health(connector.source_id, ok=True, count=len(events))
                except Exception as exc:  # connectors should already be safe
                    logger.warning("[GAIA] Geo connector %s failed: %s", connector.source_id, exc)
                    self.registry.record_health(connector.source_id, ok=False, error=str(exc))
            self._live_cache = collected
            self._last_refresh = time.monotonic()
            logger.info("[GAIA] Geo live refresh complete: %d events", len(collected))

    async def maybe_refresh(self) -> None:
        if self._needs_refresh():
            await self.refresh_live()

    def current(self, planet_inputs: PlanetInputs | None = None) -> list[GeoPlanetEvent]:
        """Return the events to render (synchronous, safe inside the loop)."""
        now = datetime.now(timezone.utc)
        merged: dict[str, GeoPlanetEvent] = {}

        if self.data_mode == "demo":
            if planet_inputs is not None:
                for event in synthesize_from_simulation(planet_inputs, now=now):
                    merged[event.id] = event
            for event in build_demo_events(now=now):
                merged.setdefault(event.id, event)
        else:
            # Strict live mode: only real events from active sources.
            for event in self._live_cache:
                merged.setdefault(event.id, event)

        events = list(merged.values())
        status_rank = {"live": 0, "recent": 1, "simulated": 2, "archived": 3}
        events.sort(key=lambda e: (status_rank.get(e.status, 9), -e.intensity))
        return events[: self.max_events]

    async def get_response(self, planet_inputs: PlanetInputs | None = None) -> GeoEventsResponse:
        await self.maybe_refresh()
        events = self.current(planet_inputs)
        sources = sorted({event.source for event in events if event.source})
        return GeoEventsResponse(
            timestamp=datetime.now(timezone.utc),
            count=len(events),
            mode=self.mode,
            sources=sources,
            events=events,
        )
