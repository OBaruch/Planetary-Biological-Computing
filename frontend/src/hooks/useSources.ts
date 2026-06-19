import { useCallback, useEffect, useMemo, useState } from "react";
import { sourcesApi } from "../api/sourcesClient";
import type { SourceStatus, TestResult } from "../types/sources";

export interface UseSourcesResult {
  sources: SourceStatus[];
  dataMode: string;
  activeCount: number;
  totalCount: number;
  loading: boolean;
  error: string | null;
  /** Planet-input field names a currently-active source is able to feed. */
  activeFields: Set<string>;
  refresh: () => Promise<void>;
  setCredentials: (id: string, secrets: Record<string, string>, enabled?: boolean) => Promise<void>;
  clearCredentials: (id: string) => Promise<void>;
  toggle: (id: string, enabled: boolean) => Promise<void>;
  test: (id: string, secrets?: Record<string, string>) => Promise<TestResult>;
}

export function useSources(): UseSourcesResult {
  const [sources, setSources] = useState<SourceStatus[]>([]);
  const [dataMode, setDataMode] = useState<string>("live");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const data = await sourcesApi.list();
      setSources(data.sources);
      setDataMode(data.data_mode);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load sources");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const replace = useCallback((next: SourceStatus) => {
    setSources((prev) => prev.map((s) => (s.descriptor.id === next.descriptor.id ? next : s)));
  }, []);

  const setCredentials = useCallback(
    async (id: string, secrets: Record<string, string>, enabled = true) => {
      replace(await sourcesApi.setCredentials(id, secrets, enabled));
    },
    [replace]
  );

  const clearCredentials = useCallback(
    async (id: string) => {
      replace(await sourcesApi.clearCredentials(id));
    },
    [replace]
  );

  const toggle = useCallback(
    async (id: string, enabled: boolean) => {
      replace(await sourcesApi.toggle(id, enabled));
    },
    [replace]
  );

  const test = useCallback(
    (id: string, secrets: Record<string, string> = {}) => sourcesApi.test(id, secrets),
    []
  );

  const activeFields = useMemo(() => {
    const fields = new Set<string>();
    for (const source of sources) {
      if (source.active) {
        for (const feed of source.descriptor.feeds) fields.add(feed);
      }
    }
    return fields;
  }, [sources]);

  const activeCount = useMemo(() => sources.filter((s) => s.active).length, [sources]);

  return {
    sources,
    dataMode,
    activeCount,
    totalCount: sources.length,
    loading,
    error,
    activeFields,
    refresh,
    setCredentials,
    clearCredentials,
    toggle,
    test
  };
}
