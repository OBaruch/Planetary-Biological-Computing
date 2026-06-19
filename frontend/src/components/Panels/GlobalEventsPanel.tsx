import { useMemo, useState } from "react";
import type { EventFilter, GeoPlanetEvent } from "../../types/geoEvents";
import { eventTypeToVisualStyle } from "../../utils/geo";

type SortKey = "recent" | "intensity" | "type";

interface Props {
  events: GeoPlanetEvent[];
  selectedEventId?: string | null;
  onSelect: (event: GeoPlanetEvent) => void;
  mode: string;
  source: "websocket" | "rest" | "demo" | "none";
}

const FILTERS: { key: EventFilter; label: string }[] = [
  { key: "all", label: "All" },
  { key: "earthquakes", label: "Earthquakes" },
  { key: "wildfires", label: "Wildfires" },
  { key: "storms", label: "Storms" },
  { key: "climate", label: "Climate" },
  { key: "air_quality", label: "Air Quality" },
  { key: "human", label: "Human Activity" },
  { key: "positive", label: "Positive Recovery" },
  { key: "neural", label: "Neural" },
  { key: "simulated", label: "Simulated" }
];

const FILTER_GROUP: Record<Exclude<EventFilter, "all" | "simulated">, string> = {
  earthquakes: "seismic",
  wildfires: "fire",
  storms: "weather",
  climate: "climate",
  air_quality: "air",
  human: "human",
  positive: "positive",
  neural: "neural"
};

function matchesFilter(event: GeoPlanetEvent, filter: EventFilter): boolean {
  if (filter === "all") return true;
  if (filter === "simulated") return event.status === "simulated";
  return eventTypeToVisualStyle(event.type).group === FILTER_GROUP[filter];
}

function locationLine(event: GeoPlanetEvent): string {
  const parts = [event.city, event.country].filter(Boolean);
  if (parts.length) return parts.join(", ");
  return `${event.latitude.toFixed(1)}, ${event.longitude.toFixed(1)}`;
}

const SOURCE_LABEL: Record<Props["source"], string> = {
  websocket: "Live stream",
  rest: "REST feed",
  demo: "Local demo",
  none: "No data"
};

export function GlobalEventsPanel({ events, selectedEventId, onSelect, mode, source }: Props) {
  const [filter, setFilter] = useState<EventFilter>("all");
  const [sort, setSort] = useState<SortKey>("recent");

  const visible = useMemo(() => {
    const filtered = events.filter((event) => matchesFilter(event, filter));
    const sorted = [...filtered];
    if (sort === "intensity") {
      sorted.sort((a, b) => b.intensity - a.intensity);
    } else if (sort === "type") {
      sorted.sort((a, b) => a.type.localeCompare(b.type));
    } else {
      sorted.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
    }
    return sorted;
  }, [events, filter, sort]);

  const isSimulated = mode !== "live";

  return (
    <section className="panel events-panel" aria-label="Global events">
      <div className="panel-heading">
        <span>Global Events</span>
        <strong>{events.length} tracked</strong>
      </div>

      <div className={`events-source ${isSimulated ? "sim" : "live"}`}>
        <span className="events-source-dot" aria-hidden="true" />
        {SOURCE_LABEL[source]} · {isSimulated ? "Simulated geolocated events" : "Live geolocated events"}
      </div>

      <div className="events-toolbar">
        <div className="filter-chips" role="tablist" aria-label="Event filters">
          {FILTERS.map((item) => (
            <button
              key={item.key}
              type="button"
              className={`chip ${filter === item.key ? "active" : ""}`}
              onClick={() => setFilter(item.key)}
            >
              {item.label}
            </button>
          ))}
        </div>
        <label className="sort-select">
          <span className="sr-only">Sort events</span>
          <select value={sort} onChange={(e) => setSort(e.target.value as SortKey)}>
            <option value="recent">Most recent</option>
            <option value="intensity">Highest intensity</option>
            <option value="type">By type</option>
          </select>
        </label>
      </div>

      <ul className="events-list">
        {visible.length === 0 ? <li className="events-empty">No events match this filter.</li> : null}
        {visible.map((event) => {
          const style = eventTypeToVisualStyle(event.type);
          const status = event.status ?? "recent";
          return (
            <li key={event.id}>
              <button
                type="button"
                className={`event-row ${event.id === selectedEventId ? "selected" : ""}`}
                onClick={() => onSelect(event)}
              >
                <span className="event-dot" style={{ background: style.color }} aria-hidden="true" />
                <span className="event-row-main">
                  <span className="event-row-label">{event.label}</span>
                  <span className="event-row-meta">
                    {style.label} · {locationLine(event)}
                  </span>
                </span>
                <span className="event-row-side">
                  <span className={`status-tag status-${status}`}>{status}</span>
                  <span className="event-row-intensity">{Math.round(event.intensity * 100)}%</span>
                </span>
              </button>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
