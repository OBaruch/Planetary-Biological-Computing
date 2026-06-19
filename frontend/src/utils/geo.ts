import * as THREE from "three";
import type { EventVisualStyle, GeoEventType } from "../types/geoEvents";

export function clampLatitude(lat: number): number {
  if (!Number.isFinite(lat)) return 0;
  return Math.max(-90, Math.min(90, lat));
}

export function normalizeLongitude(lon: number): number {
  if (!Number.isFinite(lon)) return 0;
  return ((lon + 180) % 360 + 360) % 360 - 180;
}

/**
 * Convert latitude/longitude (degrees) into a position on a sphere of the
 * given radius. Aligned so that a standard equirectangular Earth texture
 * (lon -180..180 left-to-right, lat 90..-90 top-to-bottom) lines up with the
 * marker positions on a default THREE.SphereGeometry.
 */
export function latLonToVector3(latitude: number, longitude: number, radius: number): THREE.Vector3 {
  const lat = clampLatitude(latitude);
  const lon = normalizeLongitude(longitude);
  const phi = (90 - lat) * (Math.PI / 180); // polar angle from +Y
  const theta = (lon + 180) * (Math.PI / 180); // azimuth
  const x = -(radius * Math.sin(phi) * Math.cos(theta));
  const z = radius * Math.sin(phi) * Math.sin(theta);
  const y = radius * Math.cos(phi);
  return new THREE.Vector3(x, y, z);
}

/** Map a 0..1 intensity onto a pleasant marker scale range. */
export function eventIntensityToScale(intensity: number): number {
  const clamped = Math.max(0, Math.min(1, intensity || 0));
  return 0.45 + clamped * 1.15;
}

/**
 * Build a lifted quadratic bezier curve between two surface points, used for
 * arcs connecting regions. ``lift`` controls how far the arc bows outward.
 */
export function buildArcCurve(
  start: THREE.Vector3,
  end: THREE.Vector3,
  lift = 0.6
): THREE.QuadraticBezierCurve3 {
  const mid = start.clone().add(end).multiplyScalar(0.5);
  const distance = start.distanceTo(end);
  mid.normalize().multiplyScalar(start.length() + lift * (0.4 + distance * 0.35));
  return new THREE.QuadraticBezierCurve3(start.clone(), mid, end.clone());
}

const STYLES: Record<GeoEventType, EventVisualStyle> = {
  earthquake: {
    color: "#ff7a3d",
    accent: "#ffd27a",
    pulseSpeed: 1.6,
    ring: "concentric",
    particles: false,
    group: "seismic",
    label: "Earthquake"
  },
  volcanic_activity: {
    color: "#ff5436",
    accent: "#ffb061",
    pulseSpeed: 1.9,
    ring: "concentric",
    particles: true,
    group: "seismic",
    label: "Volcanic Activity"
  },
  wildfire: {
    color: "#ff5a2c",
    accent: "#ffce4d",
    pulseSpeed: 1.1,
    ring: "single",
    particles: true,
    group: "fire",
    label: "Wildfire"
  },
  storm: {
    color: "#7fb6ff",
    accent: "#e8f4ff",
    pulseSpeed: 1.3,
    ring: "spiral",
    particles: false,
    group: "weather",
    label: "Storm"
  },
  flood: {
    color: "#4aa8ff",
    accent: "#bfe4ff",
    pulseSpeed: 1.7,
    ring: "single",
    particles: false,
    group: "weather",
    label: "Flood"
  },
  heatwave: {
    color: "#ff8a3d",
    accent: "#ffd98a",
    pulseSpeed: 2.2,
    ring: "single",
    particles: false,
    group: "climate",
    label: "Heatwave"
  },
  drought: {
    color: "#e0ab54",
    accent: "#f4d79a",
    pulseSpeed: 2.6,
    ring: "single",
    particles: false,
    group: "climate",
    label: "Drought"
  },
  climate_alert: {
    color: "#ffb24c",
    accent: "#ffe0a8",
    pulseSpeed: 2.0,
    ring: "single",
    particles: false,
    group: "climate",
    label: "Climate Alert"
  },
  pollution: {
    color: "#9a7bd0",
    accent: "#c9b6ec",
    pulseSpeed: 2.8,
    ring: "none",
    particles: false,
    group: "air",
    label: "Pollution"
  },
  air_quality_alert: {
    color: "#9b8bb0",
    accent: "#cabfdc",
    pulseSpeed: 2.8,
    ring: "none",
    particles: false,
    group: "air",
    label: "Air Quality Alert"
  },
  conflict: {
    color: "#ff6b6b",
    accent: "#ffc2c2",
    pulseSpeed: 1.4,
    ring: "single",
    particles: false,
    group: "human",
    label: "Conflict"
  },
  good_news: {
    color: "#52e6b0",
    accent: "#bdfce6",
    pulseSpeed: 2.4,
    ring: "single",
    particles: false,
    group: "positive",
    label: "Good News"
  },
  renewable_boost: {
    color: "#5fe084",
    accent: "#c8f7d4",
    pulseSpeed: 2.2,
    ring: "single",
    particles: true,
    group: "positive",
    label: "Renewable Boost"
  },
  ocean_recovery: {
    color: "#43c6e8",
    accent: "#bdeefb",
    pulseSpeed: 2.6,
    ring: "concentric",
    particles: false,
    group: "positive",
    label: "Ocean Recovery"
  },
  biodiversity_gain: {
    color: "#7ce05f",
    accent: "#d7f7c8",
    pulseSpeed: 2.5,
    ring: "single",
    particles: false,
    group: "positive",
    label: "Biodiversity Gain"
  },
  solar_storm: {
    color: "#a98bff",
    accent: "#8ef0ff",
    pulseSpeed: 1.5,
    ring: "none",
    particles: false,
    group: "cosmic",
    label: "Solar Storm"
  },
  neural_burst: {
    color: "#8ef0ff",
    accent: "#d7c9ff",
    pulseSpeed: 0.9,
    ring: "concentric",
    particles: false,
    group: "neural",
    label: "Neural Burst"
  }
};

const FALLBACK_STYLE: EventVisualStyle = {
  color: "#9be0cf",
  accent: "#e8f4ec",
  pulseSpeed: 2.0,
  ring: "single",
  particles: false,
  group: "climate",
  label: "Event"
};

export function eventTypeToVisualStyle(type: string): EventVisualStyle {
  return STYLES[type as GeoEventType] ?? FALLBACK_STYLE;
}
