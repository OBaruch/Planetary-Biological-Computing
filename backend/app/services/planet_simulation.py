from __future__ import annotations

import random

from app.models.neural import DecodedAction, NeuralMetrics
from app.models.planet import PlanetInputs, PlanetState
from app.services.math_utils import clamp, lerp, normalize


class PlanetSimulation:
    def __init__(self, seed: int = 42) -> None:
        self._rng = random.Random(seed)
        self.state = PlanetState(
            temperature=0.48,
            biosphere=0.68,
            ocean_health=0.64,
            atmosphere_quality=0.62,
            human_pressure=0.54,
            chaos=0.34,
            recovery=0.5,
            resilience=0.58,
            visual_intensity=0.35,
            planetary_mood_label="watchful equilibrium",
        )

    def reset(self) -> PlanetState:
        self.__init__()
        return self.state

    def step(self, inputs: PlanetInputs, metrics: NeuralMetrics, action: DecodedAction) -> PlanetState:
        noise = lambda scale: self._rng.uniform(-scale, scale)
        vector = action.action_vector
        heat = vector.get("heat_planet", 0.0)
        cool = vector.get("cool_planet", 0.0)
        restore = vector.get("restore_biosphere", 0.0)
        degrade = vector.get("degrade_biosphere", 0.0)
        calm = vector.get("calm_human_pressure", 0.0)
        chaos_amp = vector.get("amplify_chaos", 0.0)
        ocean_stability = vector.get("stabilize_oceans", 0.0)
        clean_atmosphere = vector.get("clean_atmosphere", 0.0)

        target_temperature = clamp(
            normalize(inputs.global_temperature_anomaly, -0.5, 2.5) * 0.58
            + inputs.climate_pressure_score * 0.32
            + heat * 0.18
            - cool * 0.24
            + noise(0.015)
        )
        target_biosphere = clamp(
            inputs.biosphere_stability_score * 0.62
            + self.state.resilience * 0.2
            + restore * 0.22
            - degrade * 0.18
            - inputs.wildfire_risk_index * 0.11
            + noise(0.012)
        )
        target_ocean = clamp(
            (1.0 - inputs.ocean_temperature_index) * 0.48
            + inputs.recovery_potential_score * 0.2
            + ocean_stability * 0.25
            - heat * 0.08
            + noise(0.01)
        )
        target_atmosphere = clamp(
            (1.0 - inputs.air_quality_index) * 0.48
            + inputs.renewable_energy_ratio * 0.26
            + calm * 0.14
            + clean_atmosphere * 0.22
            - inputs.wildfire_risk_index * 0.12
            + noise(0.012)
        )
        target_human_pressure = clamp(inputs.human_pressure_score * 0.72 - calm * 0.22 + chaos_amp * 0.08 + noise(0.01))
        target_chaos = clamp(
            inputs.chaos_score * 0.34
            + inputs.planetary_stress_score * 0.28
            + metrics.chaos_signal * 0.28
            + chaos_amp * 0.22
            - calm * 0.1
            + noise(0.012)
        )
        target_recovery = clamp(inputs.recovery_potential_score * 0.54 + metrics.recovery_signal * 0.28 + restore * 0.22)
        target_resilience = clamp(
            inputs.resilience_score * 0.18
            + target_biosphere * 0.26
            + target_ocean * 0.22
            + target_atmosphere * 0.18
            + target_recovery * 0.2
            - target_chaos * 0.12
        )
        visual_intensity = clamp(
            vector.get("trigger_visual_pulse", 0.0) * 0.42
            + metrics.neural_activity_level * 0.2
            + target_chaos * 0.18
            + target_recovery * 0.12
        )

        self.state = PlanetState(
            temperature=round(lerp(self.state.temperature, target_temperature, 0.18), 4),
            biosphere=round(lerp(self.state.biosphere, target_biosphere, 0.16), 4),
            ocean_health=round(lerp(self.state.ocean_health, target_ocean, 0.15), 4),
            atmosphere_quality=round(lerp(self.state.atmosphere_quality, target_atmosphere, 0.16), 4),
            human_pressure=round(lerp(self.state.human_pressure, target_human_pressure, 0.18), 4),
            chaos=round(lerp(self.state.chaos, target_chaos, 0.2), 4),
            recovery=round(lerp(self.state.recovery, target_recovery, 0.16), 4),
            resilience=round(lerp(self.state.resilience, target_resilience, 0.14), 4),
            visual_intensity=round(visual_intensity, 4),
            planetary_mood_label=self._mood(target_chaos, target_recovery, target_resilience),
        )
        return self.state

    def _mood(self, chaos: float, recovery: float, resilience: float) -> str:
        if chaos > 0.72:
            return "storm-charged instability"
        if recovery > 0.68 and resilience > 0.58:
            return "regenerative pulse"
        if resilience < 0.38:
            return "fragile biosphere"
        if chaos < 0.36 and recovery > 0.52:
            return "quiet recovery"
        return "watchful equilibrium"
