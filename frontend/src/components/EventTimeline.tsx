import type { SimulationFrame } from "../api/types";

export function EventTimeline({ frames }: { frames: SimulationFrame[] }) {
  const items = frames
    .flatMap((frame) =>
      frame.events.map((event) => ({
        event,
        tick: frame.tick,
        timestamp: frame.timestamp
      }))
    )
    .slice(-12)
    .reverse();

  return (
    <section className="panel timeline-panel" aria-label="Event timeline">
      <div className="panel-heading">
        <span>Timeline</span>
        <strong>{items.length} events</strong>
      </div>
      <ol className="timeline-list">
        {items.map((item, index) => (
          <li key={`${item.tick}-${index}`}>
            <span>T{item.tick}</span>
            <p>{item.event}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}
