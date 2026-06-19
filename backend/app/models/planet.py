from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from app.models.geo_event import GeoPlanetEvent
from app.models.neural import DecodedAction, NeuralMetrics, StimulationIntent


class PlanetInputs(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_mode: str = "mock"

    global_temperature_anomaly: float
    co2_ppm: float
    methane_index: float
    ocean_temperature_index: float
    sea_level_index: float
    air_quality_index: float
    wildfire_risk_index: float
    drought_index: float
    precipitation_index: float
    storm_intensity_index: float

    earthquake_magnitude: float
    earthquake_frequency: float
    volcanic_activity_index: float

    energy_consumption_index: float
    renewable_energy_ratio: float
    air_traffic_index: float
    urban_activity_index: float
    internet_activity_index: float

    global_news_tension_index: float
    sentiment_index: float
    conflict_index: float
    cooperation_index: float

    planetary_stress_score: float
    biosphere_stability_score: float
    climate_pressure_score: float
    human_pressure_score: float
    recovery_potential_score: float
    chaos_score: float
    resilience_score: float

    active_events: list[str] = Field(default_factory=list)


class PlanetState(BaseModel):
    temperature: float = Field(ge=0.0, le=1.0)
    biosphere: float = Field(ge=0.0, le=1.0)
    ocean_health: float = Field(ge=0.0, le=1.0)
    atmosphere_quality: float = Field(ge=0.0, le=1.0)
    human_pressure: float = Field(ge=0.0, le=1.0)
    chaos: float = Field(ge=0.0, le=1.0)
    recovery: float = Field(ge=0.0, le=1.0)
    resilience: float = Field(ge=0.0, le=1.0)
    visual_intensity: float = Field(ge=0.0, le=1.0)
    planetary_mood_label: str


class SimulationFrame(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    session_id: str
    tick: int
    mode: str
    adapter_status: str
    planet_inputs: PlanetInputs
    encoded_signal: StimulationIntent
    neural_metrics: NeuralMetrics
    decoded_action: DecodedAction
    planet_state: PlanetState
    events: list[str]
    events_geo: list[GeoPlanetEvent] = Field(default_factory=list)
    # Maps each real-data planet-input field to the source_id backing it.
    # Fields with no real source are absent (the UI renders them disabled).
    signal_provenance: dict[str, str] = Field(default_factory=dict)
