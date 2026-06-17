import { Activity, CircleAlert, CircleCheck, RadioTower } from "lucide-react";

interface Props {
  connectionState: "connecting" | "connected" | "reconnecting" | "disconnected" | "error";
  mode: string;
  status: string;
  tick: number;
  running: boolean;
}

export function ConnectionStatus({ connectionState, mode, status, tick, running }: Props) {
  const connected = connectionState === "connected";
  return (
    <div className="status-strip" aria-label="Connection status">
      <span className={connected ? "status-pill online" : "status-pill offline"}>
        {connected ? <CircleCheck size={16} /> : <CircleAlert size={16} />}
        {connected ? "Live" : connectionState}
      </span>
      <span className={running ? "status-pill online" : "status-pill muted"}>{running ? "Running" : "Stopped"}</span>
      <span className="status-pill">
        <RadioTower size={16} />
        {mode}
      </span>
      <span className="status-pill muted">
        <Activity size={16} />
        Tick {tick}
      </span>
      <span className="adapter-status">{status}</span>
    </div>
  );
}
