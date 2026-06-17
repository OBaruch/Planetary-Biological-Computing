import { Activity, CircleAlert, CircleCheck, RadioTower } from "lucide-react";

interface Props {
  connected: boolean;
  mode: string;
  status: string;
  tick: number;
}

export function ConnectionStatus({ connected, mode, status, tick }: Props) {
  return (
    <div className="status-strip" aria-label="Connection status">
      <span className={connected ? "status-pill online" : "status-pill offline"}>
        {connected ? <CircleCheck size={16} /> : <CircleAlert size={16} />}
        {connected ? "Live" : "Reconnecting"}
      </span>
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
