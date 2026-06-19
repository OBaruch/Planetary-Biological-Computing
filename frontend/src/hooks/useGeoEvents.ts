import { useEffect, useMemo, useRef, useState } from "react";
import { fetchLiveEvents } from "../api/eventsClient";
import { DEMO_GEO_EVENTS } from "../data/demoGeoEvents";
import type { GeoPlanetEvent } from "../types/geoEvents";

export type GeoEventSource = "websocket" | "rest" | "demo" | "none";

export interface UseGeoEventsResult {
  events: GeoPlanetEvent[];
  source: GeoEventSource;
  mode: string;
  liveSources: string[];
  hasLive: boolean;
}

const MAX_EVENTS = 100;
const REST_POLL_MS = 30_000;

/** Drop malformed records, dedupe by id, and cap the list for performance. */
function sanitize(events: GeoPlanetEvent[] | undefined | null): GeoPlanetEvent[] {
  if (!events?.length) return [];
  const seen = new Map<string, GeoPlanetEvent>();
  for (const event of events) {
    if (!event || typeof event.id !== "string") continue;
    const lat = Number(event.latitude);
    const lon = Number(event.longitude);
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) continue;
    seen.set(event.id, {
      ...event,
      latitude: Math.max(-90, Math.min(90, lat)),
      longitude: ((lon + 180) % 360 + 360) % 360 - 180,
      intensity: Math.max(0, Math.min(1, Number(event.intensity) || 0))
    });
  }
  const list = Array.from(seen.values());
  const rank: Record<string, number> = { live: 0, recent: 1, simulated: 2, archived: 3 };
  list.sort((a, b) => {
    const ra = rank[a.status ?? "recent"] ?? 9;
    const rb = rank[b.status ?? "recent"] ?? 9;
    if (ra !== rb) return ra - rb;
    return b.intensity - a.intensity;
  });
  return list.slice(0, MAX_EVENTS);
}

function inferMode(events: GeoPlanetEvent[]): string {
  if (events.some((event) => event.status === "live")) return "live";
  if (events.length && events.every((event) => event.status === "simulated")) return "simulated";
  return "recent";
}

/**
 * Resolves the geolocated events to render, merging three sources by priority:
 *   1. events embedded in the latest WebSocket snapshot (``snapshotEvents``)
 *   2. the REST ``/api/events/live`` endpoint (polled while no snapshot data)
 *   3. local demo events (never empty)
 *
 * No duplicate events: each tier replaces the previous, and ids are deduped.
 */
export function useGeoEvents(
  snapshotEvents: GeoPlanetEvent[] | undefined,
  dataMode: string = "live"
): UseGeoEventsResult {
  const [restEvents, setRestEvents] = useState<GeoPlanetEvent[]>([]);
  const [restMode, setRestMode] = useState<string>("live-pending");
  const [restSources, setRestSources] = useState<string[]>([]);

  const snapshot = useMemo(() => sanitize(snapshotEvents), [snapshotEvents]);
  const hasSnapshot = snapshot.length > 0;
  const hasSnapshotRef = useRef(hasSnapshot);
  hasSnapshotRef.current = hasSnapshot;

  // Poll REST as a fallback only while the snapshot carries no geo events.
  useEffect(() => {
    if (hasSnapshot) return;
    let cancelled = false;
    const controller = new AbortController();

    async function load() {
      const response = await fetchLiveEvents({ signal: controller.signal });
      if (cancelled || !response) return;
      setRestEvents(sanitize(response.events));
      setRestMode(response.mode || "simulated");
      setRestSources(response.sources ?? []);
    }

    load();
    const timer = window.setInterval(() => {
      if (!hasSnapshotRef.current) load();
    }, REST_POLL_MS);

    return () => {
      cancelled = true;
      controller.abort();
      window.clearInterval(timer);
    };
  }, [hasSnapshot]);

  return useMemo<UseGeoEventsResult>(() => {
    if (hasSnapshot) {
      return {
        events: snapshot,
        source: "websocket",
        mode: inferMode(snapshot),
        liveSources: Array.from(new Set(snapshot.map((e) => e.source).filter(Boolean) as string[])),
        hasLive: snapshot.some((e) => e.status === "live")
      };
    }
    if (restEvents.length) {
      return {
        events: restEvents,
        source: "rest",
        mode: restMode,
        liveSources: restSources,
        hasLive: restEvents.some((e) => e.status === "live")
      };
    }
    // Strict live mode: never fall back to demo data — an empty globe means no
    // sources are configured/active. Demo fallback applies only in demo mode.
    if (dataMode === "demo") {
      const demo = sanitize(DEMO_GEO_EVENTS);
      return { events: demo, source: "demo", mode: "demo-local", liveSources: [], hasLive: false };
    }
    return { events: [], source: "none", mode: "live-pending", liveSources: [], hasLive: false };
  }, [hasSnapshot, snapshot, restEvents, restMode, restSources, dataMode]);
}
