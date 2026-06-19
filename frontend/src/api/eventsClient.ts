import type { GeoEventsResponse } from "../types/geoEvents";

const apiBase = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

/**
 * Fetch the current geolocated events from the backend. Resolves to ``null``
 * on any failure so callers can transparently fall back to WebSocket snapshot
 * events or local demo events without breaking the UI.
 */
export async function fetchLiveEvents(options?: { refresh?: boolean; signal?: AbortSignal }): Promise<GeoEventsResponse | null> {
  try {
    const query = options?.refresh ? "?refresh=true" : "";
    const response = await fetch(`${apiBase}/api/events/live${query}`, {
      headers: { Accept: "application/json" },
      signal: options?.signal
    });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as GeoEventsResponse;
  } catch {
    return null;
  }
}
