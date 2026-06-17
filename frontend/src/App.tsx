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

function App() {
  const [frame, setFrame] = useState<SimulationFrame | null>(null);
  const [history, setHistory] = useState<SimulationFrame[]>([]);
  const [connected, setConnected] = useState(false);
  const [running, setRunning] = useState(false);
  const reconnectRef = useRef<number | null>(null);

  useEffect(() => {
    let socket: WebSocket | null = null;
    let cancelled = false;

    async function bootstrap() {
      try {
        const initial = await api.getState();
        setFrame(initial);
        setHistory(await api.getHistory());
        await api.start();
        setRunning(true);
      } catch (error) {
        console.error(error);
      }
      connect();
    }

    function connect() {
      if (cancelled) return;
      socket = new WebSocket(api.liveUrl);
      socket.onopen = () => setConnected(true);
      socket.onmessage = (event) => {
        const next = JSON.parse(event.data) as SimulationFrame;
        setFrame(next);
        setRunning(next.tick > 0);
        setHistory((items) => [...items.slice(-79), next]);
      };
      socket.onclose = () => {
        setConnected(false);
        if (!cancelled) {
          reconnectRef.current = window.setTimeout(connect, 1200);
        }
      };
      socket.onerror = () => {
        socket?.close();
      };
    }

    bootstrap();

    return () => {
      cancelled = true;
      socket?.close();
      if (reconnectRef.current) window.clearTimeout(reconnectRef.current);
    };
  }, []);

  const latest = useMemo(() => frame ?? history.at(-1) ?? null, [frame, history]);

  async function runCommand(command: "start" | "stop" | "reset") {
    try {
      if (command === "start") {
        await api.start();
        setRunning(true);
      } else if (command === "stop") {
        await api.stop();
        setRunning(false);
      } else {
        await api.reset();
        const next = await api.getState();
        setFrame(next);
        setHistory([next]);
      }
    } catch (error) {
      console.error(error);
    }
  }

  async function injectEvent(type: DemoEventType, intensity = 0.8) {
    try {
      await api.demoEvent(type, intensity);
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
            Live planetary signals encoded into simulated neural activity, decoded back into a living digital Earth.
          </p>
        </div>
        <ConnectionStatus connected={connected} mode={latest.mode} status={latest.adapter_status} tick={latest.tick} />
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
