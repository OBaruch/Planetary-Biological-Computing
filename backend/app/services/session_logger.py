from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.config import Settings
from app.models.planet import SimulationFrame


class SessionLogger:
    def __init__(self, settings: Settings) -> None:
        slug = settings.session_name.replace(" ", "_").lower()
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.session_id = f"{slug}_{stamp}_{uuid4().hex[:8]}"
        self.enabled = settings.log_to_file
        self._handle = None
        self._log_handle = None
        if self.enabled:
            path = settings.data_dir / "sessions" / f"{self.session_id}.jsonl"
            log_path = settings.data_dir / "logs" / f"{self.session_id}.jsonl"
            path.parent.mkdir(parents=True, exist_ok=True)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            self._handle = path.open("a", encoding="utf-8", buffering=1)
            self._log_handle = log_path.open("a", encoding="utf-8", buffering=1)

    def write(self, frame: SimulationFrame) -> None:
        if not self.enabled or self._handle is None:
            return
        payload = json.dumps(frame.model_dump(mode="json"), ensure_ascii=True)
        self._handle.write(payload + "\n")
        if self._log_handle is not None:
            self._log_handle.write(payload + "\n")

    def close(self) -> None:
        if self._handle is not None:
            self._handle.close()
            self._handle = None
        if self._log_handle is not None:
            self._log_handle.close()
            self._log_handle = None
