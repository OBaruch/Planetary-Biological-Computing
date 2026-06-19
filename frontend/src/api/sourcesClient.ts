import type { SourceStatus, SourcesResponse, TestResult } from "../types/sources";

const apiBase = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBase}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init
  });
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

export const sourcesApi = {
  list: () => request<SourcesResponse>("/api/sources"),
  setCredentials: (id: string, secrets: Record<string, string>, enabled = true) =>
    request<SourceStatus>(`/api/sources/${id}/credentials`, {
      method: "PUT",
      body: JSON.stringify({ secrets, enabled })
    }),
  clearCredentials: (id: string) =>
    request<SourceStatus>(`/api/sources/${id}/credentials`, { method: "DELETE" }),
  toggle: (id: string, enabled: boolean) =>
    request<SourceStatus>(`/api/sources/${id}/toggle`, {
      method: "POST",
      body: JSON.stringify({ enabled })
    }),
  test: (id: string, secrets: Record<string, string> = {}) =>
    request<TestResult>(`/api/sources/${id}/test`, {
      method: "POST",
      body: JSON.stringify({ secrets })
    })
};
