import type { PlanetInputs, SimulationFrame } from "../api/types";
import { MetricBar } from "./MetricBar";

// Planet-input signals that real connectors can feed. Each row is dimmed and
// marked "no source" until a configured source backs it (signal_provenance).
const SENSOR_ROWS: { field: keyof PlanetInputs; label: string; tone: "cool" | "warm" | "signal" | "danger" }[] = [
  { field: "air_quality_index", label: "Air Quality", tone: "signal" },
  { field: "wildfire_risk_index", label: "Wildfire Risk", tone: "warm" },
  { field: "precipitation_index", label: "Precipitation", tone: "cool" },
  { field: "storm_intensity_index", label: "Storm / Geomagnetic", tone: "danger" },
  { field: "earthquake_frequency", label: "Seismic Activity", tone: "danger" },
  { field: "global_news_tension_index", label: "News Tension", tone: "warm" },
  { field: "sentiment_index", label: "Global Sentiment", tone: "cool" }
];

export function PlanetMetricsPanel({ frame }: { frame: SimulationFrame }) {
  const state = frame.planet_state;
  const inputs = frame.planet_inputs;
  const provenance = frame.signal_provenance ?? {};

  return (
    <section className="panel metrics-panel" aria-label="Planet metrics">
      <div className="panel-heading">
        <span>Planet State</span>
        <strong>{inputs.source_mode}</strong>
      </div>
      <MetricBar label="Temperature Index" value={state.temperature} tone="warm" />
      <MetricBar label="Biosphere Stability" value={state.biosphere} tone="cool" />
      <MetricBar label="Ocean Health" value={state.ocean_health} tone="cool" />
      <MetricBar label="Atmosphere Quality" value={state.atmosphere_quality} tone="signal" />
      <MetricBar label="Human Pressure" value={state.human_pressure} tone="danger" />
      <MetricBar label="Chaos Level" value={state.chaos} tone="danger" />
      <MetricBar label="Recovery Potential" value={state.recovery} tone="cool" />

      <div className="panel-heading" style={{ marginTop: 4 }}>
        <span>Live Sensors</span>
        <strong>real data</strong>
      </div>
      {SENSOR_ROWS.map((row) => {
        const sourceId = provenance[row.field as string] ?? null;
        return (
          <MetricBar
            key={row.field as string}
            label={row.label}
            value={Number(inputs[row.field] ?? 0)}
            tone={row.tone}
            sourceId={sourceId}
            disabled={!sourceId}
          />
        );
      })}

      <div className="compact-grid">
        <span>CO2</span>
        <strong>{Math.round(inputs.co2_ppm)} ppm</strong>
        <span>Quake</span>
        <strong>M {inputs.earthquake_magnitude.toFixed(1)}</strong>
      </div>
    </section>
  );
}
