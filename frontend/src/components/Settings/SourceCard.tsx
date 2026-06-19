import { useState } from "react";
import type { SourceStatus, TestResult } from "../../types/sources";

interface SourceCardProps {
  status: SourceStatus;
  onSave: (id: string, secrets: Record<string, string>, enabled?: boolean) => Promise<void>;
  onClear: (id: string) => Promise<void>;
  onToggle: (id: string, enabled: boolean) => Promise<void>;
  onTest: (id: string, secrets?: Record<string, string>) => Promise<TestResult>;
}

function statusPill(status: SourceStatus): { label: string; cls: string } {
  const { descriptor, configured, enabled, active, health } = status;
  if (descriptor.requires_key && !configured) return { label: "Needs key", cls: "warn" };
  if (!enabled) return { label: "Disabled", cls: "muted" };
  if (active && health.ok === false) return { label: "Error", cls: "error" };
  if (active) return { label: "Active", cls: "online" };
  return { label: "Idle", cls: "muted" };
}

export function SourceCard({ status, onSave, onClear, onToggle, onTest }: SourceCardProps) {
  const { descriptor } = status;
  const [secrets, setSecrets] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [test, setTest] = useState<TestResult | null>(null);

  const pill = statusPill(status);
  const hasInput = Object.values(secrets).some((v) => v.trim().length > 0);

  async function run(action: () => Promise<void>) {
    setBusy(true);
    try {
      await action();
    } finally {
      setBusy(false);
    }
  }

  async function handleSave() {
    await run(() => onSave(descriptor.id, secrets, true));
    setSecrets({});
  }

  async function handleTest() {
    setBusy(true);
    try {
      setTest(await onTest(descriptor.id, hasInput ? secrets : {}));
    } catch (err) {
      setTest({ ok: false, count: 0, error: err instanceof Error ? err.message : "Test failed" });
    } finally {
      setBusy(false);
    }
  }

  return (
    <article className={`source-card ${status.active ? "is-active" : "is-inactive"}`}>
      <header className="source-card-head">
        <div className="source-card-title">
          <span className="source-name">{descriptor.name}</span>
          <span className={`key-badge ${descriptor.requires_key ? "needs-key" : "free"}`}>
            {descriptor.requires_key ? "API key" : "No key"}
          </span>
        </div>
        <span className={`source-pill ${pill.cls}`}>
          <span className="dot" />
          {pill.label}
        </span>
      </header>

      <p className="source-desc">{descriptor.description}</p>

      {descriptor.credential_fields.map((field) => (
        <label key={field.key} className="source-field">
          <span>
            {field.label}
            {status.masked_credentials[field.key] ? (
              <em className="masked"> · saved {status.masked_credentials[field.key]}</em>
            ) : null}
          </span>
          <input
            type={field.secret ? "password" : "text"}
            autoComplete="off"
            placeholder={field.placeholder ?? (status.configured ? "Replace saved key…" : field.help ?? "")}
            value={secrets[field.key] ?? ""}
            onChange={(e) => setSecrets((prev) => ({ ...prev, [field.key]: e.target.value }))}
            disabled={busy}
          />
          {field.help ? <small>{field.help}</small> : null}
        </label>
      ))}

      {test ? (
        <p className={`source-test ${test.ok ? "ok" : "fail"}`}>
          {test.ok
            ? `Connected · ${test.count} item(s)${test.sample ? ` · ${test.sample}` : ""}`
            : `Failed · ${test.error ?? "no data"}`}
        </p>
      ) : null}

      <footer className="source-card-actions">
        {descriptor.requires_key ? (
          <button className="ghost" onClick={handleSave} disabled={busy || !hasInput}>
            Save key
          </button>
        ) : null}
        <button className="ghost" onClick={handleTest} disabled={busy}>
          Test connection
        </button>
        <button
          className="ghost"
          onClick={() => run(() => onToggle(descriptor.id, !status.enabled))}
          disabled={busy || (descriptor.requires_key && !status.configured)}
        >
          {status.enabled ? "Disable" : "Enable"}
        </button>
        {descriptor.requires_key && status.configured ? (
          <button className="ghost danger" onClick={() => run(() => onClear(descriptor.id))} disabled={busy}>
            Remove key
          </button>
        ) : null}
        {descriptor.signup_url ? (
          <a className="source-link" href={descriptor.signup_url} target="_blank" rel="noreferrer">
            Get key ↗
          </a>
        ) : descriptor.doc_url ? (
          <a className="source-link" href={descriptor.doc_url} target="_blank" rel="noreferrer">
            Docs ↗
          </a>
        ) : null}
      </footer>
    </article>
  );
}
