from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass

from app.models.api import DemoEventRequest
from app.models.planet import PlanetInputs
from app.services.math_utils import clamp, normalize


@dataclass
class _EventBias:
    name: str
    intensity: float
    ttl_ticks: int
    original_ttl_ticks: int


class PlanetDataProvider:
    """Generates realistic synthetic planet signals and leaves hooks for live APIs."""

    def __init__(self, use_live_data: bool = False, seed: int = 42) -> None:
        self.use_live_data = use_live_data
        self._rng = random.Random(seed)
        self._start = time.monotonic()
        self._tick = 0
        self._biases: list[_EventBias] = []

    def inject_event(self, event: DemoEventRequest) -> str:
        ttl = max(1, int(event.duration_seconds * 10))
        self._biases.append(_EventBias(event.type, event.intensity, ttl, ttl))
        return (
            f"{event.type.replace('_', ' ').title()} injected at {event.intensity:.2f} "
            f"intensity for {event.duration_seconds:.0f}s"
        )

    def next(self) -> PlanetInputs:
        if self.use_live_data:
            # Live connectors should return this same model. The MVP stays reliable offline.
            return self._mock_inputs(source_mode="mock-live-fallback")
        return self._mock_inputs(source_mode="mock")

    def _mock_inputs(self, source_mode: str) -> PlanetInputs:
        elapsed = time.monotonic() - self._start
        self._tick += 1
        daily = math.sin(elapsed / 18.0)
        fast = math.sin(elapsed / 4.5)
        slow = math.sin(elapsed / 55.0)
        event = self._event_effects()

        global_temperature_anomaly = 1.15 + 0.18 * slow + 0.08 * fast + event["heat"]
        co2_ppm = 424.0 + 2.5 * slow + event["human"] * 4.0
        methane_index = clamp(0.58 + 0.08 * daily + event["human"] * 0.18)
        ocean_temperature_index = clamp(0.52 + 0.12 * slow + event["heat"] * 0.25 - event["ocean"] * 0.22)
        sea_level_index = clamp(0.46 + 0.06 * slow + normalize(co2_ppm, 380, 460) * 0.18)
        air_quality_index = clamp(
            0.45
            + 0.12 * fast
            + event["wildfire"] * 0.42
            + event["human"] * 0.12
            + event["pollution"] * 0.42
            - event["biodiversity"] * 0.12
        )
        wildfire_risk_index = clamp(0.34 + 0.18 * daily + event["wildfire"] + event["heat"] * 0.35)
        drought_index = clamp(0.38 + 0.11 * slow + event["heat"] * 0.28)
        precipitation_index = clamp(0.52 + 0.12 * math.cos(elapsed / 10.0) - event["heat"] * 0.15)
        storm_intensity_index = clamp(0.33 + 0.2 * abs(fast) + event["chaos"] * 0.28 + event["solar"] * 0.32)

        earthquake_frequency = clamp(0.18 + self._rng.random() * 0.07 + event["earthquake"] * 0.65)
        earthquake_magnitude = clamp(0.12 + event["earthquake"] * 0.82 + self._rng.random() * 0.08) * 8.5
        volcanic_activity_index = clamp(0.14 + 0.05 * math.sin(elapsed / 21.0) + event["earthquake"] * 0.22)

        energy_consumption_index = clamp(0.62 + 0.08 * daily + event["human"] * 0.18)
        renewable_energy_ratio = clamp(0.33 + 0.06 * slow + event["renewable"] * 0.48)
        air_traffic_index = clamp(0.55 + 0.1 * math.cos(elapsed / 9.0) + event["human"] * 0.1)
        urban_activity_index = clamp(0.64 + 0.06 * fast + event["human"] * 0.18)
        internet_activity_index = clamp(0.71 + 0.05 * abs(fast) + event["cooperation"] * 0.07 + event["solar"] * 0.08)

        global_news_tension_index = clamp(0.4 + 0.12 * fast + event["conflict"] * 0.5 - event["cooperation"] * 0.16)
        sentiment_index = clamp(0.5 + 0.12 * slow + event["cooperation"] * 0.28 - event["conflict"] * 0.25)
        conflict_index = clamp(0.34 + 0.08 * daily + event["conflict"] * 0.55)
        cooperation_index = clamp(
            0.45
            + 0.08 * math.cos(elapsed / 14.0)
            + event["cooperation"] * 0.42
            + event["biodiversity"] * 0.14
        )

        climate_pressure_score = clamp(
            normalize(global_temperature_anomaly, -0.5, 2.5) * 0.24
            + normalize(co2_ppm, 380, 460) * 0.2
            + wildfire_risk_index * 0.18
            + drought_index * 0.14
            + storm_intensity_index * 0.14
            + air_quality_index * 0.1
        )
        human_pressure_score = clamp(
            energy_consumption_index * 0.22
            + air_traffic_index * 0.18
            + urban_activity_index * 0.18
            + global_news_tension_index * 0.17
            + conflict_index * 0.15
            + (1.0 - renewable_energy_ratio) * 0.1
        )
        recovery_potential_score = clamp(
            renewable_energy_ratio * 0.3
            + cooperation_index * 0.25
            + sentiment_index * 0.2
            + precipitation_index * 0.1
            + (1.0 - air_quality_index) * 0.15
        )
        planetary_stress_score = clamp(
            climate_pressure_score * 0.48
            + human_pressure_score * 0.32
            + earthquake_frequency * 0.08
            + volcanic_activity_index * 0.04
            + conflict_index * 0.08
        )
        biosphere_stability_score = clamp(1.0 - planetary_stress_score * 0.62 + recovery_potential_score * 0.28)
        chaos_score = clamp(
            storm_intensity_index * 0.2
            + earthquake_frequency * 0.14
            + global_news_tension_index * 0.2
            + conflict_index * 0.22
            + planetary_stress_score * 0.24
        )
        resilience_score = clamp(
            biosphere_stability_score * 0.34
            + recovery_potential_score * 0.3
            + cooperation_index * 0.18
            + renewable_energy_ratio * 0.18
            - chaos_score * 0.12
        )

        return PlanetInputs(
            source_mode=source_mode,
            global_temperature_anomaly=round(global_temperature_anomaly, 4),
            co2_ppm=round(co2_ppm, 3),
            methane_index=round(methane_index, 4),
            ocean_temperature_index=round(ocean_temperature_index, 4),
            sea_level_index=round(sea_level_index, 4),
            air_quality_index=round(air_quality_index, 4),
            wildfire_risk_index=round(wildfire_risk_index, 4),
            drought_index=round(drought_index, 4),
            precipitation_index=round(precipitation_index, 4),
            storm_intensity_index=round(storm_intensity_index, 4),
            earthquake_magnitude=round(earthquake_magnitude, 4),
            earthquake_frequency=round(earthquake_frequency, 4),
            volcanic_activity_index=round(volcanic_activity_index, 4),
            energy_consumption_index=round(energy_consumption_index, 4),
            renewable_energy_ratio=round(renewable_energy_ratio, 4),
            air_traffic_index=round(air_traffic_index, 4),
            urban_activity_index=round(urban_activity_index, 4),
            internet_activity_index=round(internet_activity_index, 4),
            global_news_tension_index=round(global_news_tension_index, 4),
            sentiment_index=round(sentiment_index, 4),
            conflict_index=round(conflict_index, 4),
            cooperation_index=round(cooperation_index, 4),
            planetary_stress_score=round(planetary_stress_score, 4),
            biosphere_stability_score=round(biosphere_stability_score, 4),
            climate_pressure_score=round(climate_pressure_score, 4),
            human_pressure_score=round(human_pressure_score, 4),
            recovery_potential_score=round(recovery_potential_score, 4),
            chaos_score=round(chaos_score, 4),
            resilience_score=round(resilience_score, 4),
            active_events=[bias.name for bias in self._biases],
        )

    def _event_effects(self) -> dict[str, float]:
        effects = {
            "heat": 0.0,
            "wildfire": 0.0,
            "earthquake": 0.0,
            "human": 0.0,
            "conflict": 0.0,
            "cooperation": 0.0,
            "renewable": 0.0,
            "chaos": 0.0,
            "ocean": 0.0,
            "pollution": 0.0,
            "biodiversity": 0.0,
            "solar": 0.0,
        }
        remaining: list[_EventBias] = []
        for bias in self._biases:
            decay = bias.ttl_ticks / max(1, bias.original_ttl_ticks)
            amount = clamp(bias.intensity * decay)
            if bias.name == "heatwave":
                effects["heat"] += amount * 0.45
                effects["chaos"] += amount * 0.2
            elif bias.name == "wildfire":
                effects["wildfire"] += amount * 0.72
                effects["human"] += amount * 0.08
            elif bias.name == "earthquake":
                effects["earthquake"] += amount
                effects["chaos"] += amount * 0.35
            elif bias.name == "good_news":
                effects["cooperation"] += amount
                effects["conflict"] -= amount * 0.28
            elif bias.name == "conflict":
                effects["conflict"] += amount
                effects["human"] += amount * 0.22
                effects["chaos"] += amount * 0.22
            elif bias.name == "renewable_boost":
                effects["renewable"] += amount
                effects["cooperation"] += amount * 0.18
            elif bias.name == "ocean_recovery":
                effects["ocean"] += amount
                effects["cooperation"] += amount * 0.12
            elif bias.name == "pollution_spike":
                effects["pollution"] += amount
                effects["human"] += amount * 0.18
                effects["chaos"] += amount * 0.16
            elif bias.name == "biodiversity_gain":
                effects["biodiversity"] += amount
                effects["cooperation"] += amount * 0.18
            elif bias.name == "solar_storm":
                effects["solar"] += amount
                effects["chaos"] += amount * 0.4
            bias.ttl_ticks -= 1
            if bias.ttl_ticks > 0:
                remaining.append(bias)
        self._biases = remaining
        return {key: clamp(value, -1.0, 1.0) for key, value in effects.items()}
