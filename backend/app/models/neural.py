from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


ChannelGroup = Literal[
    "climate_regulation",
    "biosphere_recovery",
    "human_pressure",
    "chaos_stress",
    "none",
]


class NeuralSpike(BaseModel):
    channel: int = Field(ge=0, le=63)
    timestamp: int | float
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StimulationIntent(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    target_channels: list[int]
    intensity: float = Field(ge=0.0, le=1.0)
    burst_frequency: float = Field(ge=0.0)
    encoded_planet_signature: list[float]
    stimulation_intent: str
    metadata: dict[str, float | str | int | bool]


class NeuralMetrics(BaseModel):
    spikes_per_second: float = Field(ge=0.0)
    active_channels_count: int = Field(ge=0)
    channel_entropy: float = Field(ge=0.0, le=1.0)
    dominant_channel_group: ChannelGroup
    neural_activity_level: float = Field(ge=0.0, le=1.0)
    synchrony_score: float = Field(ge=0.0, le=1.0)
    burstiness_score: float = Field(ge=0.0, le=1.0)
    stability_signal: float = Field(ge=0.0, le=1.0)
    chaos_signal: float = Field(ge=0.0, le=1.0)
    recovery_signal: float = Field(ge=0.0, le=1.0)
    recent_spike_count: int = Field(ge=0)


class DecodedAction(BaseModel):
    primary_action: str
    action_vector: dict[str, float]
    confidence: float = Field(ge=0.0, le=1.0)
    metaphor_notice: str = (
        "Decoded actions are visualization metaphors derived from simulated spikes, "
        "not claims about biological intent or cognition."
    )
