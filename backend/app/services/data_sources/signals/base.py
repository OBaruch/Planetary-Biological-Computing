from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class SamplePoint:
    city: str
    country: str
    lat: float
    lon: float


# Representative world cities used to turn point-based APIs (weather, air
# quality) into global indices by sampling + averaging. Broad geographic spread.
WORLD_SAMPLE_POINTS: tuple[SamplePoint, ...] = (
    SamplePoint("Mexico City", "Mexico", 19.4326, -99.1332),
    SamplePoint("New York", "United States", 40.7128, -74.0060),
    SamplePoint("Los Angeles", "United States", 34.0522, -118.2437),
    SamplePoint("Sao Paulo", "Brazil", -23.5505, -46.6333),
    SamplePoint("London", "United Kingdom", 51.5074, -0.1278),
    SamplePoint("Berlin", "Germany", 52.5200, 13.4050),
    SamplePoint("Lagos", "Nigeria", 6.5244, 3.3792),
    SamplePoint("Nairobi", "Kenya", -1.2921, 36.8219),
    SamplePoint("Cairo", "Egypt", 30.0444, 31.2357),
    SamplePoint("New Delhi", "India", 28.6139, 77.2090),
    SamplePoint("Beijing", "China", 39.9042, 116.4074),
    SamplePoint("Tokyo", "Japan", 35.6762, 139.6503),
    SamplePoint("Jakarta", "Indonesia", -6.2088, 106.8456),
    SamplePoint("Sydney", "Australia", -33.8688, 151.2093),
)


@dataclass
class SignalContribution:
    """A partial overlay onto ``PlanetInputs`` produced by one real source.

    ``fields`` maps a subset of ``PlanetInputs`` field names to normalized
    real values; ``SignalService`` merges contributions and records which
    source backed each field (provenance).
    """

    source_id: str
    fields: dict[str, float] = field(default_factory=dict)
    confidence: float = 1.0
    detail: str | None = None


class SignalConnector(Protocol):
    """Common shape for any scalar-signal source.

    Like geo connectors, signal connectors must be resilient: any failure
    (no network, bad key, timeout, malformed payload) resolves to ``None``,
    never an exception, so missing data degrades to an "unsourced" field.
    """

    source_id: str
    name: str

    async def fetch(self) -> SignalContribution | None:
        ...
