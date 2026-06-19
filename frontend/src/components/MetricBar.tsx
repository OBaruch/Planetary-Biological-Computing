interface Props {
  label: string;
  value: number;
  display?: string;
  tone?: "cool" | "warm" | "signal" | "danger";
  /** Source id backing this metric (real data). Omit/undefined => unsourced. */
  sourceId?: string | null;
  /** When true the row is rendered dimmed (no real source configured). */
  disabled?: boolean;
}

export function MetricBar({ label, value, display, tone = "signal", sourceId, disabled }: Props) {
  const pct = Math.max(0, Math.min(100, value * 100));
  const showSource = sourceId !== undefined;
  return (
    <div className={`metric-row${disabled ? " unsourced" : ""}`}>
      <div className="metric-label">
        <span>{label}</span>
        {showSource ? (
          <span className={`metric-source-tag${sourceId ? " live" : ""}`}>
            {sourceId ? sourceId : "no source"}
          </span>
        ) : null}
        <strong>{disabled ? "—" : display ?? `${Math.round(pct)}%`}</strong>
      </div>
      <div className="meter" aria-hidden="true">
        <span className={`meter-fill ${tone}`} style={{ width: `${disabled ? 0 : pct}%` }} />
      </div>
    </div>
  );
}
