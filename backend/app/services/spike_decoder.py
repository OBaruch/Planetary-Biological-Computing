from __future__ import annotations

import math
from collections import Counter

from app.models.neural import DecodedAction, NeuralMetrics, NeuralSpike
from app.models.planet import PlanetInputs
from app.services.math_utils import clamp


GROUPS = {
    "climate_regulation": range(0, 16),
    "biosphere_recovery": range(16, 32),
    "human_pressure": range(32, 48),
    "chaos_stress": range(48, 64),
}


class SpikeDecoder:
    def __init__(self, window_seconds: float = 1.0) -> None:
        self.window_seconds = window_seconds

    def decode(
        self,
        spikes: list[NeuralSpike],
        planet: PlanetInputs,
        adapter_latency_ms: float = 0.0,
        tick_rate: float = 0.0,
    ) -> tuple[NeuralMetrics, DecodedAction]:
        count = len(spikes)
        active_channels = {spike.channel for spike in spikes}
        channel_counts = Counter(spike.channel for spike in spikes)
        entropy = self._entropy(channel_counts, count)
        group_counts = {
            group: sum(1 for spike in spikes if spike.channel in channels)
            for group, channels in GROUPS.items()
        }
        dominant_group = max(group_counts, key=group_counts.get) if count else "none"
        activity = clamp(count / 18.0)
        synchrony = self._synchrony(spikes)
        burstiness = clamp((max(channel_counts.values()) / count) if count else 0.0)
        chaos_signal = clamp(group_counts["chaos_stress"] / max(count, 1) * 0.75 + planet.planetary_stress_score * 0.25)
        recovery_signal = clamp(group_counts["biosphere_recovery"] / max(count, 1) * 0.72 + planet.recovery_potential_score * 0.28)
        stability_signal = clamp((1.0 - chaos_signal) * 0.45 + recovery_signal * 0.35 + entropy * 0.2)
        metrics = NeuralMetrics(
            spikes_per_second=round(count / self.window_seconds, 3),
            active_channels_count=len(active_channels),
            channel_entropy=round(entropy, 4),
            dominant_channel_group=dominant_group,  # type: ignore[arg-type]
            neural_activity_level=round(activity, 4),
            synchrony_score=round(synchrony, 4),
            burstiness_score=round(burstiness, 4),
            stability_signal=round(stability_signal, 4),
            chaos_signal=round(chaos_signal, 4),
            recovery_signal=round(recovery_signal, 4),
            recent_spike_count=count,
            adapter_latency_ms=round(adapter_latency_ms, 3),
            tick_rate=round(tick_rate, 3),
        )
        action = self._action(metrics, planet)
        return metrics, action

    def _action(self, metrics: NeuralMetrics, planet: PlanetInputs) -> DecodedAction:
        climate = metrics.dominant_channel_group == "climate_regulation"
        recovery = metrics.dominant_channel_group == "biosphere_recovery"
        human = metrics.dominant_channel_group == "human_pressure"
        chaos = metrics.dominant_channel_group == "chaos_stress"
        actions = {
            "cool_planet": 0.0,
            "heat_planet": 0.0,
            "restore_biosphere": 0.0,
            "degrade_biosphere": 0.0,
            "calm_human_pressure": 0.0,
            "amplify_chaos": 0.0,
            "stabilize_oceans": 0.0,
            "clean_atmosphere": 0.0,
            "trigger_visual_pulse": metrics.neural_activity_level,
        }
        if climate:
            actions["cool_planet"] = clamp(planet.climate_pressure_score * 0.7 + metrics.stability_signal * 0.3)
            actions["stabilize_oceans"] = clamp(metrics.synchrony_score * 0.5 + planet.ocean_temperature_index * 0.4)
        elif recovery:
            actions["restore_biosphere"] = clamp(metrics.recovery_signal * 0.85 + planet.recovery_potential_score * 0.15)
            actions["stabilize_oceans"] = clamp(metrics.recovery_signal * 0.45)
            actions["clean_atmosphere"] = clamp((1.0 - planet.air_quality_index) * 0.28 + metrics.recovery_signal * 0.2)
        elif human:
            actions["calm_human_pressure"] = clamp((1.0 - metrics.chaos_signal) * 0.45 + planet.human_pressure_score * 0.35)
            actions["degrade_biosphere"] = clamp(planet.human_pressure_score * 0.18)
            actions["clean_atmosphere"] = clamp((1.0 - planet.air_quality_index) * 0.18)
        elif chaos:
            actions["amplify_chaos"] = clamp(metrics.chaos_signal * 0.92 + planet.conflict_index * 0.08)
            actions["heat_planet"] = clamp(planet.climate_pressure_score * 0.22 + metrics.burstiness_score * 0.25)
        else:
            actions["restore_biosphere"] = clamp(planet.recovery_potential_score * 0.15)

        primary = max(actions, key=actions.get)
        return DecodedAction(
            primary_action=primary,
            action_vector={key: round(value, 4) for key, value in actions.items()},
            confidence=round(clamp(actions[primary]), 4),
        )

    def _entropy(self, counts: Counter[int], total: int) -> float:
        if total <= 1:
            return 0.0
        entropy = 0.0
        for count in counts.values():
            p = count / total
            entropy -= p * math.log2(p)
        return clamp(entropy / math.log2(64))

    def _synchrony(self, spikes: list[NeuralSpike]) -> float:
        if len(spikes) < 2:
            return 0.0
        timestamps = [float(spike.timestamp) for spike in spikes]
        spread = max(timestamps) - min(timestamps)
        return clamp(1.0 - spread / 25_000.0)
