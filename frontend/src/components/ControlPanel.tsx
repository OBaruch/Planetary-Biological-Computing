import { Flame, HeartPulse, Mountain, Play, RefreshCcw, Square, SunMedium, Wind, Zap } from "lucide-react";
import type { DemoEventType } from "../api/types";

interface Props {
  running: boolean;
  onStart: () => void;
  onStop: () => void;
  onReset: () => void;
  onEvent: (type: DemoEventType, intensity?: number) => void;
}

export function ControlPanel({ running, onStart, onStop, onReset, onEvent }: Props) {
  return (
    <section className="panel control-panel" aria-label="Simulation controls">
      <div className="panel-heading">
        <span>Demo Events</span>
        <strong>{running ? "running" : "standby"}</strong>
      </div>
      <div className="control-grid">
        <button type="button" onClick={running ? onStop : onStart} title={running ? "Stop simulation" : "Start simulation"}>
          {running ? <Square size={17} /> : <Play size={17} />}
          {running ? "Stop" : "Start"}
        </button>
        <button type="button" onClick={onReset} title="Reset planet">
          <RefreshCcw size={17} />
          Reset Planet
        </button>
        <button type="button" onClick={() => onEvent("heatwave", 0.85)} title="Inject heatwave">
          <SunMedium size={17} />
          Inject Heatwave
        </button>
        <button type="button" onClick={() => onEvent("wildfire", 0.82)} title="Inject wildfire">
          <Flame size={17} />
          Inject Wildfire
        </button>
        <button type="button" onClick={() => onEvent("earthquake", 0.75)} title="Inject earthquake">
          <Mountain size={17} />
          Inject Earthquake
        </button>
        <button type="button" onClick={() => onEvent("good_news", 0.78)} title="Inject global good news">
          <HeartPulse size={17} />
          Global Good News
        </button>
        <button type="button" onClick={() => onEvent("renewable_boost", 0.9)} title="Inject renewable boost">
          <Wind size={17} />
          Renewable Boost
        </button>
        <button type="button" onClick={() => onEvent("conflict", 0.8)} title="Inject conflict spike">
          <Zap size={17} />
          Conflict Spike
        </button>
      </div>
    </section>
  );
}
