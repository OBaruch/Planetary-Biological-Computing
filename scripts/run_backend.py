from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    env = os.environ.copy()
    env.setdefault("GAIA_MODE", "simulator")
    env.setdefault("GAIA_ALLOW_FALLBACK", "true")
    env.setdefault("CL_SDK_VISUALISATION", "0")
    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--reload",
        "--port",
        "8000",
        "--app-dir",
        "backend",
    ]
    return subprocess.call(command, cwd=ROOT, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
