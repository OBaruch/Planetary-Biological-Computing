import type { SimulationFrame } from "../api/types";
import { MetricBar } from "./MetricBar";

export function PlanetMetricsPanel({ frame }: { frame: SimulationFrame }) {
  const state = frame.planet_state;
  const inputs = frame.planet_inputs;
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
      <MetricBar label="Derived Chaos Score" value={inputs.chaos_score} tone="danger" />
      <MetricBar label="Derived Resilience Score" value={inputs.resilience_score} tone="cool" />
      <div className="compact-grid">
        <span>CO2</span>
        <strong>{Math.round(inputs.co2_ppm)} ppm</strong>
        <span>Quake</span>
        <strong>M {inputs.earthquake_magnitude.toFixed(1)}</strong>
      </div>
    </section>
  );
}
