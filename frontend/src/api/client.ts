import type { DemoEventType, SimulationFrame, SimulationStatus } from "./types";

const apiBase = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const wsBase = import.meta.env.VITE_WS_URL ?? "ws://localhost:8000/ws/live";

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

export const api = {
  getState: () => request<SimulationFrame>("/api/state"),
  getStatus: () => request<SimulationStatus>("/api/status"),
  getHistory: (limit = 80) => request<SimulationFrame[]>(`/api/history?limit=${limit}`),
  start: () => request("/api/control/start", { method: "POST" }),
  stop: () => request("/api/control/stop", { method: "POST" }),
  reset: () => request("/api/control/reset", { method: "POST" }),
  demoEvent: (type: DemoEventType, intensity = 0.8, duration_seconds = 30) =>
    request("/api/control/demo-event", {
      method: "POST",
      body: JSON.stringify({ type, intensity, duration_seconds })
    }),
  liveUrl: wsBase
};
