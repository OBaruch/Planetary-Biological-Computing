export type ChannelGroup =
  | "climate_regulation"
  | "biosphere_recovery"
  | "human_pressure"
  | "chaos_stress"
  | "none";

export interface PlanetInputs {
  timestamp: string;
  source_mode: string;
  global_temperature_anomaly: number;
  co2_ppm: number;
  methane_index: number;
  ocean_temperature_index: number;
  sea_level_index: number;
  air_quality_index: number;
  wildfire_risk_index: number;
  drought_index: number;
  precipitation_index: number;
  storm_intensity_index: number;
  earthquake_magnitude: number;
  earthquake_frequency: number;
  volcanic_activity_index: number;
  energy_consumption_index: number;
  renewable_energy_ratio: number;
  air_traffic_index: number;
  urban_activity_index: number;
  internet_activity_index: number;
  global_news_tension_index: number;
  sentiment_index: number;
  conflict_index: number;
  cooperation_index: number;
  planetary_stress_score: number;
  biosphere_stability_score: number;
  climate_pressure_score: number;
  human_pressure_score: number;
  recovery_potential_score: number;
  active_events: string[];
}

export interface PlanetState {
  temperature: number;
  biosphere: number;
  ocean_health: number;
  atmosphere_quality: number;
  human_pressure: number;
  chaos: number;
  recovery: number;
  resilience: number;
  visual_intensity: number;
  planetary_mood_label: string;
}

export interface StimulationIntent {
  timestamp: string;
  target_channels: number[];
  intensity: number;
  burst_frequency: number;
  encoded_planet_signature: number[];
  stimulation_intent: string;
  metadata: Record<string, string | number | boolean>;
}

export interface NeuralMetrics {
  spikes_per_second: number;
  active_channels_count: number;
  channel_entropy: number;
  dominant_channel_group: ChannelGroup;
  neural_activity_level: number;
  synchrony_score: number;
  burstiness_score: number;
  stability_signal: number;
  chaos_signal: number;
  recovery_signal: number;
  recent_spike_count: number;
}

export interface DecodedAction {
  primary_action: string;
  action_vector: Record<string, number>;
  confidence: number;
  metaphor_notice: string;
}

export interface SimulationFrame {
  timestamp: string;
  session_id: string;
  tick: number;
  mode: string;
  adapter_status: string;
  planet_inputs: PlanetInputs;
  encoded_signal: StimulationIntent;
  neural_metrics: NeuralMetrics;
  decoded_action: DecodedAction;
  planet_state: PlanetState;
  events: string[];
}

export type DemoEventType =
  | "wildfire"
  | "earthquake"
  | "heatwave"
  | "good_news"
  | "conflict"
  | "renewable_boost";
