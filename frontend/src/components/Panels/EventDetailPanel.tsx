import { X } from "lucide-react";
import type { GeoPlanetEvent } from "../../types/geoEvents";
import { eventTypeToVisualStyle } from "../../utils/geo";

interface Props {
  event: GeoPlanetEvent | null;
  onClose: () => void;
}

function formatTimestamp(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

function locationLine(event: GeoPlanetEvent): string {
  const parts = [event.city, event.region, event.country].filter(Boolean);
  if (parts.length) return parts.join(", ");
  return `${event.latitude.toFixed(2)}, ${event.longitude.toFixed(2)}`;
}

export function EventDetailPanel({ event, onClose }: Props) {
  if (!event) return null;
  const style = eventTypeToVisualStyle(event.type);
  const status = event.status ?? "recent";

  return (
    <aside className="event-detail" aria-label="Event detail">
      <div className="event-detail-head">
        <span className="event-type-dot" style={{ background: style.color }} aria-hidden="true" />
        <div>
          <p className="event-detail-eyebrow">{style.label}</p>
          <h3>{event.label}</h3>
        </div>
        <button type="button" className="icon-button" onClick={onClose} aria-label="Close event detail">
          <X size={16} />
        </button>
      </div>

      <span className={`status-tag status-${status}`}>{status.toUpperCase()}</span>

      <dl className="event-detail-grid">
        <dt>Location</dt>
        <dd>{locationLine(event)}</dd>
        <dt>Coordinates</dt>
        <dd>
          {event.latitude.toFixed(3)}, {event.longitude.toFixed(3)}
        </dd>
        <dt>Intensity</dt>
        <dd>{Math.round(event.intensity * 100)}%</dd>
        {event.magnitude != null ? (
          <>
            <dt>Magnitude</dt>
            <dd>M {event.magnitude.toFixed(1)}</dd>
          </>
        ) : null}
        <dt>Source</dt>
        <dd>{event.source ?? "—"}</dd>
        <dt>Timestamp</dt>
        <dd>{formatTimestamp(event.timestamp)}</dd>
      </dl>

      {event.description ? <p className="event-detail-desc">{event.description}</p> : null}

      {event.source_url ? (
        <a className="event-source-link" href={event.source_url} target="_blank" rel="noreferrer noopener">
          View source
        </a>
      ) : null}
    </aside>
  );
}
