from __future__ import annotations

import json
import sys
import time
from urllib import request


BASE_URL = "http://127.0.0.1:8000"


def call(path: str, method: str = "GET", body: dict | None = None) -> dict:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = request.Request(
        f"{BASE_URL}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    with request.urlopen(req, timeout=8) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    health = call("/health")
    started = call("/api/control/start", method="POST")
    time.sleep(0.8)
    state = call("/api/state")
    status = call("/api/status")
    event = call(
        "/api/control/demo-event",
        method="POST",
        body={"type": "ocean_recovery", "intensity": 0.7, "duration_seconds": 10},
    )
    history = call("/api/history?limit=5")
    result = {
        "health": health["status"],
        "start": started["message"],
        "mode": state["mode"],
        "tick": state["tick"],
        "status_ticks": status["ticks"],
        "event": event["message"],
        "history_items": len(history),
    }
    print(json.dumps(result, indent=2))
    if state["tick"] <= 0 or not history:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
