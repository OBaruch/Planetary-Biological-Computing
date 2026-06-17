from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def main() -> int:
    checks = {
        "python": sys.version.split()[0],
        "fastapi": has_module("fastapi"),
        "uvicorn": has_module("uvicorn"),
        "pydantic": has_module("pydantic"),
        "cl_sdk_import_cl": has_module("cl"),
        "frontend_package_json": (ROOT / "frontend" / "package.json").exists(),
        "backend_requirements": (ROOT / "backend" / "requirements.txt").exists(),
        "env_example": (ROOT / ".env.example").exists(),
    }
    print(json.dumps(checks, indent=2))
    required = ["fastapi", "uvicorn", "pydantic", "frontend_package_json", "backend_requirements", "env_example"]
    missing = [name for name in required if not checks[name]]
    if missing:
        print(f"Missing required environment pieces: {', '.join(missing)}", file=sys.stderr)
        return 1
    if not checks["cl_sdk_import_cl"]:
        print("CL SDK is not importable; GAIA-1 can still run with GAIA_ALLOW_FALLBACK=true.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
