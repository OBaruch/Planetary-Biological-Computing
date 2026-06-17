interface Props {
  label: string;
  value: number;
  display?: string;
  tone?: "cool" | "warm" | "signal" | "danger";
}

export function MetricBar({ label, value, display, tone = "signal" }: Props) {
  const pct = Math.max(0, Math.min(100, value * 100));
  return (
    <div className="metric-row">
      <div className="metric-label">
        <span>{label}</span>
        <strong>{display ?? `${Math.round(pct)}%`}</strong>
      </div>
      <div className="meter" aria-hidden="true">
        <span className={`meter-fill ${tone}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
