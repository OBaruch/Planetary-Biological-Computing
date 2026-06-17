import { useEffect, useMemo, useRef, useState } from "react";
import { api } from "./api/client";
import type { DemoEventType, SimulationFrame } from "./api/types";
import { ConnectionStatus } from "./components/ConnectionStatus";
import { ControlPanel } from "./components/ControlPanel";
import { EthicsBanner } from "./components/EthicsBanner";
import { EventTimeline } from "./components/EventTimeline";
import { NeuralActivityPanel } from "./components/NeuralActivityPanel";
import { PlanetMetricsPanel } from "./components/PlanetMetricsPanel";
import { PlanetView } from "./components/PlanetView";

type ConnectionState = "connecting" | "connected" | "reconnecting" | "disconnected" | "error";
type ControlResponse = { message?: string; running?: boolean };

function App() {
  const [frame, setFrame] = useState<SimulationFrame | null>(null);
  const [history, setHistory] = useState<SimulationFrame[]>([]);
  const [connectionState, setConnectionState] = useState<ConnectionState>("connecting");
  const [running, setRunning] = useState(false);
  const [lastCommand, setLastCommand] = useState<string | null>(null);
  const reconnectRef = useRef<number | null>(null);
  const pollingRef = useRef<number | null>(null);
  const reconnectAttemptRef = useRef(0);

  useEffect(() => {
    let socket: WebSocket | null = null;
    let cancelled = false;

    async function bootstrap() {
      try {
        const initial = await api.getState();
        setFrame(initial);
        setHistory(await api.getHistory());
        const started = (await api.start()) as ControlResponse;
        setLastCommand(started.message ?? "Simulation started");
        setRunning(true);
      } catch (error) {
        setConnectionState("error");
        console.error(error);
      }
      connect();
    }

    async function pollState() {
      try {
        const next = await api.getState();
        setFrame(next);
        setRunning(next.tick > 0);
        setHistory((items) => [...items.slice(-79), next]);
      } catch (error) {
        console.error(error);
      }
    }

    function startPollingFallback() {
      if (pollingRef.current) return;
      pollingRef.current = window.setInterval(pollState, 2500);
    }

    function stopPollingFallback() {
      if (pollingRef.current) {
        window.clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    }

    function connect() {
      if (cancelled) return;
      setConnectionState(reconnectAttemptRef.current > 0 ? "reconnecting" : "connecting");
      socket = new WebSocket(api.liveUrl);
      socket.onopen = () => {
        reconnectAttemptRef.current = 0;
        setConnectionState("connected");
        stopPollingFallback();
      };
      socket.onmessage = (event) => {
        const next = JSON.parse(event.data) as SimulationFrame;
        setFrame(next);
        setRunning(next.tick > 0 && !next.mode.includes("pending"));
        setHistory((items) => [...items.slice(-79), next]);
      };
      socket.onclose = () => {
        setConnectionState(cancelled ? "disconnected" : "reconnecting");
        startPollingFallback();
        if (!cancelled) {
          reconnectAttemptRef.current += 1;
          const delay = Math.min(8000, 800 * 2 ** Math.min(reconnectAttemptRef.current, 4));
          reconnectRef.current = window.setTimeout(connect, delay);
        }
      };
      socket.onerror = () => {
        setConnectionState("error");
        socket?.close();
      };
    }

    bootstrap();

    return () => {
      cancelled = true;
      socket?.close();
      if (reconnectRef.current) window.clearTimeout(reconnectRef.current);
      if (pollingRef.current) window.clearInterval(pollingRef.current);
    };
  }, []);

  const latest = useMemo(() => frame ?? history.at(-1) ?? null, [frame, history]);

  async function runCommand(command: "start" | "stop" | "reset") {
    try {
      if (command === "start") {
        const response = (await api.start()) as ControlResponse;
        setRunning(response.running ?? true);
        setLastCommand(response.message ?? "Simulation started");
      } else if (command === "stop") {
        const response = (await api.stop()) as ControlResponse;
        setRunning(response.running ?? false);
        setLastCommand(response.message ?? "Simulation stopped");
      } else {
        const response = (await api.reset()) as ControlResponse;
        const next = await api.getState();
        setFrame(next);
        setHistory([next]);
        setRunning(response.running ?? false);
        setLastCommand(response.message ?? "Planet reset");
      }
    } catch (error) {
      console.error(error);
    }
  }

  async function injectEvent(type: DemoEventType, intensity = 0.8, durationSeconds = 30) {
    try {
      const response = (await api.demoEvent(type, intensity, durationSeconds)) as ControlResponse;
      setLastCommand(response.message ?? `${type.replaceAll("_", " ")} injected`);
    } catch (error) {
      console.error(error);
    }
  }

  if (!latest) {
    return (
      <main className="app-shell loading">
        <p>GAIA-1 telemetry initializing</p>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">GAIA-1 / EARTH DREAMS</p>
          <h1>GAIA-1: Earth Dreams</h1>
          <p className="subtitle">
            A neuron-ready planetary simulator. Planetary signals are encoded into stimulation intents; simulated
            spikes are decoded into planetary actions. Designed for future CL1/Cortical Cloud deployment.
          </p>
        </div>
        <ConnectionStatus
          connectionState={connectionState}
          mode={latest.mode}
          status={latest.adapter_status}
          tick={latest.tick}
          running={running}
        />
      </header>

      <EthicsBanner />

      <section className="dashboard-grid">
        <div className="left-stack">
          <PlanetMetricsPanel frame={latest} />
          <ControlPanel
            running={running}
            onStart={() => runCommand("start")}
            onStop={() => runCommand("stop")}
            onReset={() => runCommand("reset")}
            onEvent={injectEvent}
            lastCommand={lastCommand}
          />
        </div>
        <PlanetView state={latest.planet_state} />
        <div className="right-stack">
          <NeuralActivityPanel frame={latest} />
          <EventTimeline frames={history.length ? history : [latest]} />
        </div>
      </section>
    </main>
  );
}

export default App;
