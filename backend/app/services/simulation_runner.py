from __future__ import annotations

import asyncio
import importlib.util
import logging
import time
from collections import deque
from datetime import datetime, timezone

from app.api.websocket import LiveBroadcaster
from app.config import Settings
from app.models.api import ConfigResponse, DemoEventRequest, SessionSummary, SimulationStatus
from app.models.neural import DecodedAction, NeuralMetrics, StimulationIntent
from app.models.planet import PlanetState, SimulationFrame
from app.services.cortical_simulator_adapter import CorticalSimulatorAdapter
from app.services.data_sources import CredentialStore, SignalService, SourceRegistry, derive_geo_signals
from app.services.encoder import PlanetEncoder
from app.services.fallback_synthetic_adapter import FallbackSyntheticAdapter
from app.services.geo_events import GeoEventService
from app.services.neural_adapter import NeuralAdapter
from app.services.planet_data import PlanetDataProvider
from app.services.planet_simulation import PlanetSimulation
from app.services.session_logger import SessionLogger
from app.services.spike_decoder import SpikeDecoder

logger = logging.getLogger(__name__)


ETHICS_TEXT = (
    "This MVP uses the Cortical Labs CL SDK Simulator. It is not connected to real neurons. "
    "It does not demonstrate biological learning, consciousness, or sentience."
)


class SimulationRunner:
    def __init__(self, settings: Settings, broadcaster: LiveBroadcaster) -> None:
        self.settings = settings
        self.broadcaster = broadcaster
        self.logger = SessionLogger(settings)
        self.session_id = self.logger.session_id
        self.credentials = CredentialStore(settings.credentials_path)
        self.registry = SourceRegistry(self.credentials)
        self.provider = PlanetDataProvider(data_mode=settings.data_mode)
        self.encoder = PlanetEncoder()
        self.decoder = SpikeDecoder(window_seconds=1 / settings.ticks_per_second)
        self.simulation = PlanetSimulation()
        self.geo_events = GeoEventService(self.registry, data_mode=settings.data_mode)
        self.signals = SignalService(self.registry)
        self.adapter: NeuralAdapter | None = None
        self.history: deque[SimulationFrame] = deque(maxlen=settings.history_limit)
        self.latest: SimulationFrame = self._idle_frame()
        self._task: asyncio.Task[None] | None = None
        self._lock = asyncio.Lock()
        self._tick = 0
        self._running = False
        self._created_at = datetime.now(timezone.utc)
        self._started_at: datetime | None = None
        self._last_error: str | None = None
        self._loop_started_monotonic: float | None = None

    @property
    def running(self) -> bool:
        return self._running

    @property
    def mode(self) -> str:
        if self.adapter is not None:
            return self.adapter.mode_label
        return "Simulator Mode (pending start)" if self.settings.gaia_mode == "simulator" else "Fallback Mode (pending start)"

    @property
    def adapter_status(self) -> str:
        return self.adapter.status if self.adapter else "not started"

    @property
    def cl_sdk_available(self) -> bool:
        return importlib.util.find_spec("cl") is not None

    async def start(self) -> str:
        async with self._lock:
            if self._running:
                return "Simulation already running"
            self.adapter = self._create_adapter()
            try:
                logger.info("[GAIA] Starting simulation session_id=%s", self.session_id)
                self.adapter.start()
                logger.info("[GAIA] Neural adapter mode=%s", self.adapter.mode_label)
            except Exception as exc:
                if not self.settings.allow_fallback:
                    self.adapter = None
                    raise
                logger.warning("[GAIA] Falling back to synthetic adapter because CL SDK failed: %s", exc)
                self.adapter = FallbackSyntheticAdapter()
                self.adapter.start()
            self._running = True
            self._started_at = datetime.now(timezone.utc)
            self._loop_started_monotonic = time.monotonic()
            self._last_error = None
            self._task = asyncio.create_task(self._loop(), name="gaia-simulation-loop")
            return f"Simulation started in {self.adapter.mode_label}"

    async def stop(self) -> str:
        task: asyncio.Task[None] | None = None
        async with self._lock:
            if not self._running:
                return "Simulation already stopped"
            self._running = False
            task = self._task
            self._task = None
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        if self.adapter:
            self.adapter.stop()
        logger.info("[GAIA] Simulation stopped cleanly session_id=%s", self.session_id)
        return "Simulation stopped"

    async def reset(self) -> str:
        was_running = self._running
        if was_running:
            await self.stop()
        async with self._lock:
            self.provider = PlanetDataProvider(data_mode=self.settings.data_mode)
            self.simulation = PlanetSimulation()
            self.geo_events = GeoEventService(self.registry, data_mode=self.settings.data_mode)
            self.signals = SignalService(self.registry)
            self.history.clear()
            self._tick = 0
            self._last_error = None
            self.latest = self._idle_frame()
        if was_running:
            await self.start()
        return "Planet state reset"

    async def inject_demo_event(self, event: DemoEventRequest) -> str:
        message = self.provider.inject_event(event)
        logger.info("[GAIA] Demo event injected type=%s intensity=%.2f", event.type, event.intensity)
        return message

    async def rebuild_sources(self) -> None:
        """Refresh connectors after a credential/toggle change.

        Active connectors are derived live from the registry, so we just force
        a refresh (in the background) so newly enabled sources appear promptly
        without blocking the settings request.
        """

        async def _refresh() -> None:
            try:
                await self.geo_events.refresh_live(force=True)
                await self.signals.refresh(force=True)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("[GAIA] Source rebuild refresh failed: %s", exc)

        asyncio.create_task(_refresh(), name="gaia-source-rebuild")

    async def get_state(self) -> SimulationFrame:
        async with self._lock:
            return self.latest

    async def get_history(self, limit: int | None = None) -> list[SimulationFrame]:
        async with self._lock:
            items = list(self.history)
        if limit is not None:
            return items[-limit:]
        return items

    async def shutdown(self) -> None:
        await self.stop()
        self.logger.close()

    async def get_status(self) -> SimulationStatus:
        async with self._lock:
            history_size = len(self.history)
            ticks = self._tick
            last_error = self._last_error
            started_at = self._started_at
        adapter_metrics = self.adapter.get_metrics() if self.adapter else {"mode": self.mode, "running": False}
        return SimulationStatus(
            running=self.running,
            mode=self.mode,
            session_id=self.session_id,
            started_at=started_at,
            ticks=ticks,
            last_error=last_error,
            adapter_status=self.adapter_status,
            adapter_metrics=adapter_metrics,
            history_size=history_size,
            history_limit=self.settings.history_limit,
            websocket_clients=self.broadcaster.client_count,
            uptime_seconds=round((datetime.now(timezone.utc) - self._created_at).total_seconds(), 3),
        )

    def get_config(self) -> ConfigResponse:
        return ConfigResponse(
            version=self.settings.app_version,
            gaia_mode=self.settings.gaia_mode,
            data_mode=self.settings.data_mode,
            ticks_per_second=self.settings.ticks_per_second,
            history_limit=self.settings.history_limit,
            use_live_data=self.settings.use_live_data,
            allow_fallback=self.settings.allow_fallback,
            log_to_file=self.settings.log_to_file,
            cors_origins=list(self.settings.cors_origins),
            cl_sdk_available=self.cl_sdk_available,
        )

    def list_sessions(self) -> list[SessionSummary]:
        sessions_dir = self.settings.data_dir / "sessions"
        items: list[SessionSummary] = []
        for path in sorted(sessions_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True):
            stat = path.stat()
            items.append(
                SessionSummary(
                    session_id=path.stem,
                    path=str(path),
                    size_bytes=stat.st_size,
                    modified_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
                )
            )
        return items[:100]

    def _create_adapter(self) -> NeuralAdapter:
        if self.settings.gaia_mode == "fallback":
            return FallbackSyntheticAdapter()
        return CorticalSimulatorAdapter(self.settings, self.session_id)

    async def _loop(self) -> None:
        assert self.adapter is not None
        interval = 1 / self.settings.ticks_per_second
        while self._running:
            started = asyncio.get_running_loop().time()
            try:
                await self.geo_events.maybe_refresh()
                await self.signals.maybe_refresh()
                frame = self._step_once()
                async with self._lock:
                    self.latest = frame
                    self.history.append(frame)
                self.logger.write(frame)
                await self.broadcaster.broadcast(frame.model_dump(mode="json"))
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self._last_error = str(exc)
                logger.exception("Simulation loop error: %s", exc)
            elapsed = asyncio.get_running_loop().time() - started
            await asyncio.sleep(max(0.0, interval - elapsed))

    def _planet_inputs_and_geo(self):
        """Resolve planet inputs + geolocated events for the current mode.

        Live mode overlays real signals (connectors + geo-derived) onto a
        neutral baseline and records provenance. Demo mode uses the synthetic
        provider and simulation-derived demo markers.
        """
        if self.settings.data_mode == "demo":
            planet_inputs = self.provider.next()
            events_geo = self.geo_events.current(planet_inputs)
            return planet_inputs, events_geo, {}

        events_geo = self.geo_events.current()
        overlay = self.signals.overlay
        provenance = self.signals.provenance
        geo_fields, geo_prov = derive_geo_signals(events_geo, self.registry.active_ids())
        overlay.update(geo_fields)
        provenance.update(geo_prov)
        planet_inputs = self.provider.next(overlay, provenance)
        return planet_inputs, events_geo, provenance

    def _step_once(self) -> SimulationFrame:
        assert self.adapter is not None
        self._tick += 1
        planet_inputs, events_geo, signal_provenance = self._planet_inputs_and_geo()
        intent = self.encoder.encode(planet_inputs)
        self.adapter.send_stimulation_intent(intent, planet_inputs)
        read_started = time.perf_counter()
        spikes = self.adapter.read_tick()
        latency_ms = (time.perf_counter() - read_started) * 1000
        actual_tick_rate = 0.0
        if self._loop_started_monotonic is not None:
            elapsed = max(time.monotonic() - self._loop_started_monotonic, 0.001)
            actual_tick_rate = self._tick / elapsed
        metrics, action = self.decoder.decode(
            spikes,
            planet_inputs,
            adapter_latency_ms=latency_ms,
            tick_rate=actual_tick_rate,
        )
        planet_state = self.simulation.step(planet_inputs, metrics, action)
        events = self._frame_events(planet_inputs.active_events, action, planet_state)
        return SimulationFrame(
            timestamp=datetime.now(timezone.utc),
            session_id=self.session_id,
            tick=self._tick,
            mode=self.adapter.mode_label,
            adapter_status=self.adapter.status,
            planet_inputs=planet_inputs,
            encoded_signal=intent,
            neural_metrics=metrics,
            decoded_action=action,
            planet_state=planet_state,
            events=events,
            events_geo=events_geo,
            signal_provenance=signal_provenance,
        )

    def _idle_frame(self) -> SimulationFrame:
        planet_inputs, events_geo, signal_provenance = self._planet_inputs_and_geo()
        intent = self.encoder.encode(planet_inputs)
        metrics = NeuralMetrics(
            spikes_per_second=0,
            active_channels_count=0,
            channel_entropy=0,
            dominant_channel_group="none",
            neural_activity_level=0,
            synchrony_score=0,
            burstiness_score=0,
            stability_signal=0.5,
            chaos_signal=planet_inputs.planetary_stress_score,
            recovery_signal=planet_inputs.recovery_potential_score,
            recent_spike_count=0,
        )
        action = DecodedAction(primary_action="standby", action_vector={"trigger_visual_pulse": 0.0}, confidence=0.0)
        return SimulationFrame(
            session_id=self.session_id,
            tick=0,
            mode=self.mode,
            adapter_status=self.adapter_status,
            planet_inputs=planet_inputs,
            encoded_signal=intent,
            neural_metrics=metrics,
            decoded_action=action,
            planet_state=self.simulation.state,
            events=[ETHICS_TEXT],
            events_geo=events_geo,
            signal_provenance=signal_provenance,
        )

    def _frame_events(self, active_events: list[str], action: DecodedAction, planet_state: PlanetState) -> list[str]:
        events = [f"Decoded action: {action.primary_action.replace('_', ' ')}"]
        for name in active_events[-4:]:
            events.append(f"Demo event active: {name.replace('_', ' ')}")
        if planet_state.chaos > 0.7:
            events.append("Planetary chaos threshold elevated")
        if planet_state.recovery > 0.65:
            events.append("Recovery potential rising")
        return events[-8:]
