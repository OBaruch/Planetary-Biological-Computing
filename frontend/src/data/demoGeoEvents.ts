import type { GeoPlanetEvent } from "../types/geoEvents";

/**
 * Local, clearly-flagged demo events used when neither the WebSocket snapshot
 * nor the REST endpoint provide geolocated data. Coordinates are approximate
 * real-world city locations.
 */
export const DEMO_GEO_EVENTS: GeoPlanetEvent[] = [
  {
    id: "local-demo-mexico-eq",
    timestamp: new Date().toISOString(),
    type: "earthquake",
    label: "Simulated seismic activity",
    latitude: 19.4326,
    longitude: -99.1332,
    intensity: 0.7,
    magnitude: 5.1,
    city: "Mexico City",
    country: "Mexico",
    status: "simulated"
  },
  {
    id: "local-demo-la-fire",
    timestamp: new Date().toISOString(),
    type: "wildfire",
    label: "Simulated wildfire risk",
    latitude: 34.0522,
    longitude: -118.2437,
    intensity: 0.8,
    city: "Los Angeles",
    country: "United States",
    status: "simulated"
  },
  {
    id: "local-demo-miami-storm",
    timestamp: new Date().toISOString(),
    type: "storm",
    label: "Simulated storm system",
    latitude: 25.7617,
    longitude: -80.1918,
    intensity: 0.6,
    city: "Miami",
    country: "United States",
    status: "simulated"
  },
  {
    id: "local-demo-delhi-air",
    timestamp: new Date().toISOString(),
    type: "pollution",
    label: "Simulated air quality alert",
    latitude: 28.6139,
    longitude: 77.209,
    intensity: 0.75,
    city: "New Delhi",
    country: "India",
    status: "simulated"
  },
  {
    id: "local-demo-berlin-renewable",
    timestamp: new Date().toISOString(),
    type: "renewable_boost",
    label: "Simulated renewable energy surge",
    latitude: 52.52,
    longitude: 13.405,
    intensity: 0.55,
    city: "Berlin",
    country: "Germany",
    status: "simulated"
  },
  {
    id: "local-demo-sydney-ocean",
    timestamp: new Date().toISOString(),
    type: "ocean_recovery",
    label: "Simulated ocean recovery signal",
    latitude: -33.8688,
    longitude: 151.2093,
    intensity: 0.5,
    city: "Sydney",
    country: "Australia",
    status: "simulated"
  }
];
