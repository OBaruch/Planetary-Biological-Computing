from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.neural import NeuralSpike, StimulationIntent
from app.models.planet import PlanetInputs


class NeuralAdapter(ABC):
    mode_label: str = "Unknown"

    @abstractmethod
    def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def read_tick(self) -> list[NeuralSpike]:
        raise NotImplementedError

    @abstractmethod
    def get_recent_spikes(self) -> list[NeuralSpike]:
        raise NotImplementedError

    @abstractmethod
    def send_stimulation_intent(self, intent: StimulationIntent, planet_state: PlanetInputs | None = None) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_metrics(self) -> dict[str, str | int | float | bool]:
        raise NotImplementedError

    @property
    @abstractmethod
    def status(self) -> str:
        raise NotImplementedError
