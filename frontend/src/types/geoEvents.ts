export type GeoEventType =
  | "earthquake"
  | "wildfire"
  | "storm"
  | "heatwave"
  | "pollution"
  | "conflict"
  | "good_news"
  | "renewable_boost"
  | "ocean_recovery"
  | "biodiversity_gain"
  | "solar_storm"
  | "neural_burst"
  | "climate_alert"
  | "volcanic_activity"
  | "air_quality_alert"
  | "flood"
  | "drought";

export type GeoEventStatus = "live" | "recent" | "simulated" | "archived";

export interface GeoPlanetEvent {
  id: string;
  timestamp: string;
  type: GeoEventType;

  label: string;
  description?: string;

  latitude: number;
  longitude: number;

  intensity: number; // 0.0 - 1.0
  magnitude?: number;
  source?: string;
  source_url?: string;

  country?: string;
  region?: string;
  city?: string;

  status?: GeoEventStatus;
}

export interface GeoEventsResponse {
  timestamp: string;
  count: number;
  mode: string;
  sources: string[];
  events: GeoPlanetEvent[];
}

/** Visual style descriptor returned by eventTypeToVisualStyle(). */
export interface EventVisualStyle {
  /** Primary marker / glow color. */
  color: string;
  /** Secondary color for rings, particles, arcs. */
  accent: string;
  /** Pulse cadence in seconds (lower = faster). */
  pulseSpeed: number;
  /** Ring style for the expanding ground wave. */
  ring: "concentric" | "single" | "spiral" | "none";
  /** Whether the marker emits ascending particles. */
  particles: boolean;
  /** Loose grouping used by the filter UI. */
  group: EventGroup;
  /** Short human label for the type. */
  label: string;
}

export type EventGroup =
  | "seismic"
  | "fire"
  | "weather"
  | "climate"
  | "air"
  | "human"
  | "positive"
  | "neural"
  | "cosmic";

/** Filter categories surfaced in the GlobalEventsPanel. */
export type EventFilter =
  | "all"
  | "earthquakes"
  | "wildfires"
  | "storms"
  | "climate"
  | "air_quality"
  | "human"
  | "positive"
  | "neural"
  | "simulated";
