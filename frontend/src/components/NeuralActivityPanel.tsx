import type { SimulationFrame } from "../api/types";
import { MetricBar } from "./MetricBar";

function labelAction(action: string) {
  return action.replaceAll("_", " ");
}

export function NeuralActivityPanel({ frame }: { frame: SimulationFrame }) {
  const metrics = frame.neural_metrics;
  const signal = frame.encoded_signal;
  return (
    <section className="panel neural-panel" aria-label="Simulated neural activity">
      <div className="panel-heading">
        <span>Simulated Neural Activity</span>
        <strong>{metrics.dominant_channel_group.replaceAll("_", " ")}</strong>
      </div>
      <div className="neural-kpis">
        <div>
          <span>Spikes/sec</span>
          <strong>{metrics.spikes_per_second.toFixed(1)}</strong>
        </div>
        <div>
          <span>Active Channels</span>
          <strong>{metrics.active_channels_count}</strong>
        </div>
      </div>
      <MetricBar label="Neural Entropy" value={metrics.channel_entropy} tone="signal" />
      <MetricBar label="Synchrony" value={metrics.synchrony_score} tone="cool" />
      <MetricBar label="Burstiness" value={metrics.burstiness_score} tone="warm" />
      <MetricBar label="Chaos Signal" value={metrics.chaos_signal} tone="danger" />
      <MetricBar label="Recovery Signal" value={metrics.recovery_signal} tone="cool" />
      <div className="intent-box">
        <span>Current Decoded Action</span>
        <strong>{labelAction(frame.decoded_action.primary_action)}</strong>
        <small>
          Intent {signal.intensity.toFixed(2)} / {signal.burst_frequency.toFixed(1)} Hz / {signal.target_channels.length} channels
        </small>
      </div>
    </section>
  );
}
