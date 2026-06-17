from __future__ import annotations

import hashlib

from app.models.neural import StimulationIntent
from app.models.planet import PlanetInputs
from app.services.math_utils import clamp, normalize


class PlanetEncoder:
    def encode(self, planet: PlanetInputs) -> StimulationIntent:
        vector = [
            normalize(planet.global_temperature_anomaly, -0.5, 2.5),
            normalize(planet.co2_ppm, 380, 460),
            planet.wildfire_risk_index,
            normalize(planet.earthquake_magnitude, 0, 8.5),
            planet.air_quality_index,
            planet.global_news_tension_index,
            planet.renewable_energy_ratio,
            planet.sentiment_index,
        ]
        vector = [round(clamp(v), 4) for v in vector]
        stress = planet.planetary_stress_score
        recovery = planet.recovery_potential_score
        intensity = clamp(stress * 0.72 + (1.0 - recovery) * 0.28)
        burst_frequency = 8.0 + intensity * 42.0
        target_channels = self._channels_for_signature(vector, intensity)
        signature = hashlib.sha1(",".join(f"{v:.4f}" for v in vector).encode("utf-8")).hexdigest()[:12]
        return StimulationIntent(
            target_channels=target_channels,
            intensity=round(intensity, 4),
            burst_frequency=round(burst_frequency, 3),
            encoded_planet_signature=vector,
            stimulation_intent=(
                "Record-only stimulation intent for simulator mode; designed to map to "
                "CL1/Cortical Cloud stimulation plans in a future biological deployment."
            ),
            metadata={
                "signature": signature,
                "planetary_stress_score": planet.planetary_stress_score,
                "climate_pressure_score": planet.climate_pressure_score,
                "human_pressure_score": planet.human_pressure_score,
                "recovery_potential_score": planet.recovery_potential_score,
                "simulator_non_causal": True,
            },
        )

    def _channels_for_signature(self, vector: list[float], intensity: float) -> list[int]:
        channels: set[int] = set()
        groups = [(0, 15), (16, 31), (32, 47), (48, 63)]
        for index, value in enumerate(vector):
            start, end = groups[index % len(groups)]
            width = end - start + 1
            channel = start + int(value * (width - 1))
            channels.add(channel)
            if value > 0.72 or intensity > 0.78:
                channels.add(min(end, channel + 1))
        return sorted(channels)
