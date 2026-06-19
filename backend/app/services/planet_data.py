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


# Calm, defensible baseline used in live mode for any field that has no real
# source yet. These are not dramatic mock signals — they are neutral normals so
# the simulation can run while the UI marks unsourced fields as disabled.
_NEUTRAL_FIELDS: dict[str, float] = {
    "global_temperature_anomaly": 1.1,
    "co2_ppm": 424.0,
    "methane_index": 0.5,
    "ocean_temperature_index": 0.5,
    "sea_level_index": 0.5,
    "air_quality_index": 0.4,
    "wildfire_risk_index": 0.3,
    "drought_index": 0.4,
    "precipitation_index": 0.5,
    "storm_intensity_index": 0.3,
    "earthquake_magnitude": 0.0,
    "earthquake_frequency": 0.1,
    "volcanic_activity_index": 0.1,
    "energy_consumption_index": 0.6,
    "renewable_energy_ratio": 0.35,
    "air_traffic_index": 0.5,
    "urban_activity_index": 0.6,
    "internet_activity_index": 0.7,
    "global_news_tension_index": 0.5,
    "sentiment_index": 0.5,
    "conflict_index": 0.35,
    "cooperation_index": 0.5,
}


class PlanetDataProvider:
    """Produces planet signals.

    In ``live`` mode it starts from a neutral baseline and overlays real values
    from configured sources (tracking provenance). In ``demo`` mode it generates
    the legacy synthetic signals with injectable event biases.
    """

    def __init__(self, data_mode: str = "live", seed: int = 42) -> None:
        self.data_mode = data_mode
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

    def next(
        self,
        overlay: dict[str, float] | None = None,
        provenance: dict[str, str] | None = None,
    ) -> PlanetInputs:
        if self.data_mode == "demo":
            return self._mock_inputs(source_mode="demo")
        return self._live_inputs(overlay or {}, provenance or {})

    # -- live mode ---------------------------------------------------------
    def _live_inputs(self, overlay: dict[str, float], provenance: dict[str, str]) -> PlanetInputs:
        fields = dict(_NEUTRAL_FIELDS)
        for key, value in overlay.items():
            if key in fields:
                fields[key] = value
        mode = "live" if provenance else "live-pending"
        return self._compose(fields, source_mode=mode, provenance=dict(provenance), active_events=[])

    # -- demo / mock mode --------------------------------------------------
    def _mock_inputs(self, source_mode: str) -> PlanetInputs:
        elapsed = time.monotonic() - self._start
        self._tick += 1
        daily = math.sin(elapsed / 18.0)
        fast = math.sin(elapsed / 4.5)
        slow = math.sin(elapsed / 55.0)
        event = self._event_effects()

        fields = {
            "global_temperature_anomaly": 1.15 + 0.18 * slow + 0.08 * fast + event["heat"],
            "co2_ppm": 424.0 + 2.5 * slow + event["human"] * 4.0,
            "methane_index": clamp(0.58 + 0.08 * daily + event["human"] * 0.18),
            "ocean_temperature_index": clamp(0.52 + 0.12 * slow + event["heat"] * 0.25 - event["ocean"] * 0.22),
            "sea_level_index": clamp(0.46 + 0.06 * slow + normalize(424.0 + 2.5 * slow + event["human"] * 4.0, 380, 460) * 0.18),
            "air_quality_index": clamp(
                0.45 + 0.12 * fast + event["wildfire"] * 0.42 + event["human"] * 0.12
                + event["pollution"] * 0.42 - event["biodiversity"] * 0.12
            ),
            "wildfire_risk_index": clamp(0.34 + 0.18 * daily + event["wildfire"] + event["heat"] * 0.35),
            "drought_index": clamp(0.38 + 0.11 * slow + event["heat"] * 0.28),
            "precipitation_index": clamp(0.52 + 0.12 * math.cos(elapsed / 10.0) - event["heat"] * 0.15),
            "storm_intensity_index": clamp(0.33 + 0.2 * abs(fast) + event["chaos"] * 0.28 + event["solar"] * 0.32),
            "earthquake_frequency": clamp(0.18 + self._rng.random() * 0.07 + event["earthquake"] * 0.65),
            "earthquake_magnitude": clamp(0.12 + event["earthquake"] * 0.82 + self._rng.random() * 0.08) * 8.5,
            "volcanic_activity_index": clamp(0.14 + 0.05 * math.sin(elapsed / 21.0) + event["earthquake"] * 0.22),
            "energy_consumption_index": clamp(0.62 + 0.08 * daily + event["human"] * 0.18),
            "renewable_energy_ratio": clamp(0.33 + 0.06 * slow + event["renewable"] * 0.48),
            "air_traffic_index": clamp(0.55 + 0.1 * math.cos(elapsed / 9.0) + event["human"] * 0.1),
            "urban_activity_index": clamp(0.64 + 0.06 * fast + event["human"] * 0.18),
            "internet_activity_index": clamp(0.71 + 0.05 * abs(fast) + event["cooperation"] * 0.07 + event["solar"] * 0.08),
            "global_news_tension_index": clamp(0.4 + 0.12 * fast + event["conflict"] * 0.5 - event["cooperation"] * 0.16),
            "sentiment_index": clamp(0.5 + 0.12 * slow + event["cooperation"] * 0.28 - event["conflict"] * 0.25),
            "conflict_index": clamp(0.34 + 0.08 * daily + event["conflict"] * 0.55),
            "cooperation_index": clamp(
                0.45 + 0.08 * math.cos(elapsed / 14.0) + event["cooperation"] * 0.42 + event["biodiversity"] * 0.14
            ),
        }
        return self._compose(
            fields,
            source_mode=source_mode,
            provenance={},
            active_events=[bias.name for bias in self._biases],
        )

    # -- shared score composition -----------------------------------------
    def _compose(
        self,
        f: dict[str, float],
        *,
        source_mode: str,
        provenance: dict[str, str],
        active_events: list[str],
    ) -> PlanetInputs:
        climate_pressure_score = clamp(
            normalize(f["global_temperature_anomaly"], -0.5, 2.5) * 0.24
            + normalize(f["co2_ppm"], 380, 460) * 0.2
            + f["wildfire_risk_index"] * 0.18
            + f["drought_index"] * 0.14
            + f["storm_intensity_index"] * 0.14
            + f["air_quality_index"] * 0.1
        )
        human_pressure_score = clamp(
            f["energy_consumption_index"] * 0.22
            + f["air_traffic_index"] * 0.18
            + f["urban_activity_index"] * 0.18
            + f["global_news_tension_index"] * 0.17
            + f["conflict_index"] * 0.15
            + (1.0 - f["renewable_energy_ratio"]) * 0.1
        )
        recovery_potential_score = clamp(
            f["renewable_energy_ratio"] * 0.3
            + f["cooperation_index"] * 0.25
            + f["sentiment_index"] * 0.2
            + f["precipitation_index"] * 0.1
            + (1.0 - f["air_quality_index"]) * 0.15
        )
        planetary_stress_score = clamp(
            climate_pressure_score * 0.48
            + human_pressure_score * 0.32
            + f["earthquake_frequency"] * 0.08
            + f["volcanic_activity_index"] * 0.04
            + f["conflict_index"] * 0.08
        )
        biosphere_stability_score = clamp(1.0 - planetary_stress_score * 0.62 + recovery_potential_score * 0.28)
        chaos_score = clamp(
            f["storm_intensity_index"] * 0.2
            + f["earthquake_frequency"] * 0.14
            + f["global_news_tension_index"] * 0.2
            + f["conflict_index"] * 0.22
            + planetary_stress_score * 0.24
        )
        resilience_score = clamp(
            biosphere_stability_score * 0.34
            + recovery_potential_score * 0.3
            + f["cooperation_index"] * 0.18
            + f["renewable_energy_ratio"] * 0.18
            - chaos_score * 0.12
        )

        return PlanetInputs(
            source_mode=source_mode,
            global_temperature_anomaly=round(f["global_temperature_anomaly"], 4),
            co2_ppm=round(f["co2_ppm"], 3),
            methane_index=round(f["methane_index"], 4),
            ocean_temperature_index=round(f["ocean_temperature_index"], 4),
            sea_level_index=round(f["sea_level_index"], 4),
            air_quality_index=round(f["air_quality_index"], 4),
            wildfire_risk_index=round(f["wildfire_risk_index"], 4),
            drought_index=round(f["drought_index"], 4),
            precipitation_index=round(f["precipitation_index"], 4),
            storm_intensity_index=round(f["storm_intensity_index"], 4),
            earthquake_magnitude=round(f["earthquake_magnitude"], 4),
            earthquake_frequency=round(f["earthquake_frequency"], 4),
            volcanic_activity_index=round(f["volcanic_activity_index"], 4),
            energy_consumption_index=round(f["energy_consumption_index"], 4),
            renewable_energy_ratio=round(f["renewable_energy_ratio"], 4),
            air_traffic_index=round(f["air_traffic_index"], 4),
            urban_activity_index=round(f["urban_activity_index"], 4),
            internet_activity_index=round(f["internet_activity_index"], 4),
            global_news_tension_index=round(f["global_news_tension_index"], 4),
            sentiment_index=round(f["sentiment_index"], 4),
            conflict_index=round(f["conflict_index"], 4),
            cooperation_index=round(f["cooperation_index"], 4),
            planetary_stress_score=round(planetary_stress_score, 4),
            biosphere_stability_score=round(biosphere_stability_score, 4),
            climate_pressure_score=round(climate_pressure_score, 4),
            human_pressure_score=round(human_pressure_score, 4),
            recovery_potential_score=round(recovery_potential_score, 4),
            chaos_score=round(chaos_score, 4),
            resilience_score=round(resilience_score, 4),
            active_events=active_events,
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
