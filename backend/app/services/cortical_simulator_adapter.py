from __future__ import annotations

import json
import logging
import time
from collections import deque
from typing import Any

from app.config import Settings
from app.models.neural import NeuralSpike, StimulationIntent
from app.models.planet import PlanetInputs
from app.services.neural_adapter import NeuralAdapter

logger = logging.getLogger(__name__)


class CorticalSimulatorAdapter(NeuralAdapter):
    mode_label = "CL SDK Simulator Mode"

    def __init__(self, settings: Settings, session_id: str, max_recent: int = 1024) -> None:
        self.settings = settings
        self.session_id = session_id
        self._recent: deque[NeuralSpike] = deque(maxlen=max_recent)
        self._cl: Any | None = None
        self._context: Any | None = None
        self._neurons: Any | None = None
        self._loop: Any | None = None
        self._recording: Any | None = None
        self._data_stream: Any | None = None
        self._running = False
        self._last_stream_timestamp = 0
        self._status = "not started"

    @property
    def status(self) -> str:
        return self._status

    def start(self) -> None:
        try:
            import cl  # type: ignore[import-not-found]
        except Exception as exc:  # pragma: no cover - depends on optional local SDK
            raise RuntimeError("cl-sdk is not installed or could not be imported") from exc

        self._cl = cl
        self._context = cl.open()
        self._neurons = self._context.__enter__()
        self._running = True
        self._status = "connected to Cortical Labs CL SDK Simulator"
        self._start_optional_recording()
        self._start_optional_data_stream()
        self._loop = self._create_loop()

    def stop(self) -> None:
        self._running = False
        if self._recording is not None:
            try:
                self._recording.stop()
            except Exception as exc:  # pragma: no cover - SDK dependent
                logger.warning("Unable to stop CL recording cleanly: %s", exc)
        if self._context is not None:
            try:
                self._context.__exit__(None, None, None)
            except TypeError:
                self._context.__exit__(None, None, None)  # type: ignore[misc]
            except Exception as exc:  # pragma: no cover - SDK dependent
                logger.warning("Unable to close CL context cleanly: %s", exc)
        self._context = None
        self._neurons = None
        self._loop = None
        self._recording = None
        self._data_stream = None
        self._status = "stopped"

    def read_tick(self) -> list[NeuralSpike]:
        if not self._running or self._loop is None:
            return []
        try:
            tick = next(self._loop)
        except StopIteration:
            self._loop = self._create_loop()
            tick = next(self._loop)
        except Exception as exc:  # pragma: no cover - SDK dependent
            logger.warning("CL SDK loop recovered after timing error: %s", exc)
            self._status = "CL SDK loop timing recovered"
            self._loop = self._create_loop()
            return []

        raw_spikes = getattr(getattr(tick, "analysis", None), "spikes", []) or []
        spikes = [
            NeuralSpike(
                channel=int(getattr(spike, "channel")),
                timestamp=getattr(spike, "timestamp", time.time_ns() // 1000),
            )
            for spike in raw_spikes
            if hasattr(spike, "channel")
        ]
        self._recent.extend(spikes)
        self._status = "connected to Cortical Labs CL SDK Simulator"
        return spikes

    def get_recent_spikes(self) -> list[NeuralSpike]:
        return list(self._recent)

    def send_stimulation_intent(self, intent: StimulationIntent, planet_state: PlanetInputs | None = None) -> None:
        self._append_data_stream(intent, planet_state)
        if self.settings.enable_cl_stimulation:
            self._try_physical_stim(intent)

    def get_metrics(self) -> dict[str, str | int | float | bool]:
        return {
            "mode": self.mode_label,
            "running": self._running,
            "recent_spikes": len(self._recent),
            "recording": self._recording is not None,
            "data_stream": self._data_stream is not None,
            "stimulation_enabled": self.settings.enable_cl_stimulation,
        }

    def _create_loop(self) -> Any:
        assert self._neurons is not None
        try:
            loop = self._neurons.loop(ticks_per_second=self.settings.ticks_per_second, ignore_jitter=True)
        except TypeError:
            loop = self._neurons.loop(ticks_per_second=self.settings.ticks_per_second)
        return iter(loop)

    def _start_optional_recording(self) -> None:
        if not self.settings.enable_cl_recording or self._neurons is None:
            return
        recording_dir = self.settings.data_dir / "recordings"
        recording_dir.mkdir(parents=True, exist_ok=True)
        kwargs: dict[str, Any] = {"file_location": str(recording_dir)}
        if self.settings.cl_recording_seconds > 0:
            kwargs["stop_after_seconds"] = self.settings.cl_recording_seconds
        try:
            self._recording = self._neurons.record(**kwargs)
        except TypeError:
            self._recording = self._neurons.record()
        except Exception as exc:  # pragma: no cover - SDK dependent
            logger.warning("CL SDK recording unavailable: %s", exc)

    def _start_optional_data_stream(self) -> None:
        if not self.settings.enable_cl_data_stream or self._neurons is None:
            return
        try:
            self._data_stream = self._neurons.create_data_stream(
                name="gaia_earth_dreams_state",
                attributes={
                    "session_id": self.session_id,
                    "purpose": "planetary stimulation intents and simulator state snapshots",
                    "not_real_neurons": True,
                },
            )
        except Exception as exc:  # pragma: no cover - SDK dependent
            logger.warning("CL SDK data stream unavailable: %s", exc)
            self._data_stream = None

    def _append_data_stream(self, intent: StimulationIntent, planet_state: PlanetInputs | None) -> None:
        if self._data_stream is None or self._neurons is None:
            return
        try:
            timestamp = int(self._neurons.timestamp())
        except Exception:
            timestamp = time.time_ns() // 1000
        timestamp = max(timestamp, self._last_stream_timestamp + 1)
        self._last_stream_timestamp = timestamp
        payload = {
            "intent": intent.model_dump(mode="json"),
            "planet_state": planet_state.model_dump(mode="json") if planet_state else None,
        }
        try:
            self._data_stream.append(timestamp, json.loads(json.dumps(payload)))
        except Exception as exc:  # pragma: no cover - SDK dependent
            logger.debug("Unable to append GAIA data stream entry: %s", exc)

    def _try_physical_stim(self, intent: StimulationIntent) -> None:
        """Optional future-facing path; disabled by default for simulator honesty."""
        if self._cl is None or self._neurons is None:
            return
        try:
            channel_set = self._cl.ChannelSet(intent.target_channels[:8])
            current = max(0.1, min(2.0, intent.intensity * 2.0))
            stim_design = self._cl.StimDesign(160, -current, 160, current)
            self._neurons.stim(channel_set, stim_design)
        except Exception as exc:  # pragma: no cover - SDK dependent
            logger.debug("CL stimulation call skipped/failed: %s", exc)
