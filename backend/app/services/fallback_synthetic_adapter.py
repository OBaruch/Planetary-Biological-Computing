from __future__ import annotations

import random
import time
from collections import deque

from app.models.neural import NeuralSpike, StimulationIntent
from app.models.planet import PlanetInputs
from app.services.neural_adapter import NeuralAdapter
from app.services.math_utils import clamp


class FallbackSyntheticAdapter(NeuralAdapter):
    mode_label = "Fallback Synthetic Mode"

    def __init__(self, seed: int = 42, max_recent: int = 512) -> None:
        self._rng = random.Random(seed)
        self._recent: deque[NeuralSpike] = deque(maxlen=max_recent)
        self._running = False
        self._last_intent: StimulationIntent | None = None
        self._tick = 0
        self._status = "CL SDK not available. Running fallback synthetic mode, not Cortical Labs Simulator."

    def start(self) -> None:
        self._running = True

    def stop(self) -> None:
        self._running = False

    @property
    def status(self) -> str:
        return self._status

    def send_stimulation_intent(self, intent: StimulationIntent, planet_state: PlanetInputs | None = None) -> None:
        self._last_intent = intent

    def read_tick(self) -> list[NeuralSpike]:
        if not self._running:
            return []
        self._tick += 1
        intensity = self._last_intent.intensity if self._last_intent else 0.35
        base_count = 1 + int(intensity * 8)
        wobble = int(abs(self._rng.gauss(0, 1.2)))
        count = max(0, base_count + wobble - 1)
        target_channels = self._last_intent.target_channels if self._last_intent else [4, 18, 34, 52]
        now = time.time_ns() // 1000
        spikes: list[NeuralSpike] = []
        for idx in range(count):
            if self._rng.random() < clamp(0.68 + intensity * 0.24):
                channel = self._rng.choice(target_channels)
            else:
                channel = self._rng.randrange(0, 64)
            timestamp = now + idx * 40
            spikes.append(NeuralSpike(channel=channel, timestamp=timestamp))
        self._recent.extend(spikes)
        return spikes

    def get_recent_spikes(self) -> list[NeuralSpike]:
        return list(self._recent)

    def get_metrics(self) -> dict[str, str | int | float | bool]:
        return {
            "mode": self.mode_label,
            "running": self._running,
            "recent_spikes": len(self._recent),
            "warning": self._status,
        }
