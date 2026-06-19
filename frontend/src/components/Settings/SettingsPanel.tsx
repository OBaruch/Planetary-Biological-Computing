import { useMemo } from "react";
import type { UseSourcesResult } from "../../hooks/useSources";
import { CATEGORY_LABELS, type SourceCategory } from "../../types/sources";
import { SourceCard } from "./SourceCard";

interface SettingsPanelProps {
  open: boolean;
  onClose: () => void;
  state: UseSourcesResult;
}

const CATEGORY_ORDER: SourceCategory[] = ["geophysics", "atmosphere", "space", "society", "movement"];

export function SettingsPanel({ open, onClose, state }: SettingsPanelProps) {
  const grouped = useMemo(() => {
    const map = new Map<SourceCategory, typeof state.sources>();
    for (const source of state.sources) {
      const category = source.descriptor.category;
      if (!map.has(category)) map.set(category, []);
      map.get(category)!.push(source);
    }
    return map;
  }, [state.sources]);

  if (!open) return null;

  return (
    <div className="settings-overlay" role="dialog" aria-modal="true" aria-label="Data source settings">
      <div className="settings-backdrop" onClick={onClose} />
      <aside className="settings-drawer">
        <header className="settings-header">
          <div>
            <p className="eyebrow">Real-data connections</p>
            <h2>Planet Sensors</h2>
            <p className="settings-sub">
              Paste your own API keys. The globe shows only the sources you have activated —
              everything else stays disabled. Your keys are stored locally and never leave your backend.
            </p>
          </div>
          <button className="settings-close" onClick={onClose} aria-label="Close settings">
            ✕
          </button>
        </header>

        <div className="settings-summary">
          <span className={`source-pill ${state.dataMode === "live" ? "online" : "muted"}`}>
            <span className="dot" />
            {state.dataMode === "live" ? "Live mode (strict)" : "Demo mode"}
          </span>
          <span className="settings-count">
            {state.activeCount} / {state.totalCount} sensors active
          </span>
        </div>

        {state.error ? <p className="settings-error">{state.error}</p> : null}
        {state.loading ? <p className="settings-loading">Loading sources…</p> : null}

        <div className="settings-body">
          {CATEGORY_ORDER.filter((category) => grouped.has(category)).map((category) => (
            <section key={category} className="settings-group">
              <h3>{CATEGORY_LABELS[category]}</h3>
              <div className="settings-cards">
                {grouped.get(category)!.map((source) => (
                  <SourceCard
                    key={source.descriptor.id}
                    status={source}
                    onSave={state.setCredentials}
                    onClear={state.clearCredentials}
                    onToggle={state.toggle}
                    onTest={state.test}
                  />
                ))}
              </div>
            </section>
          ))}
        </div>
      </aside>
    </div>
  );
}
