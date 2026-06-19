from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT_DIR / "backend"
DATA_DIR = BACKEND_DIR / "data"
APP_VERSION = "0.2.0"


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    app_version: str = APP_VERSION
    gaia_mode: str = "simulator"
    ticks_per_second: int = 10
    history_limit: int = 1000
    log_to_file: bool = True
    session_name: str = "local_demo"
    use_live_data: bool = False
    # "live" = strict real-data mode (only configured sources are shown).
    # "demo" = legacy simulated planet + demo globe events.
    data_mode: str = "live"
    allow_fallback: bool = True
    autostart: bool = False
    enable_cl_recording: bool = False
    enable_cl_data_stream: bool = True
    enable_cl_stimulation: bool = False
    cl_recording_seconds: float = 0.0
    cors_origins: tuple[str, ...] = (
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    )
    data_dir: Path = DATA_DIR

    @property
    def credentials_path(self) -> Path:
        return self.data_dir / "credentials.json"


def load_settings() -> Settings:
    load_dotenv(ROOT_DIR / ".env")
    origins = tuple(
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174",
        ).split(",")
        if origin.strip()
    )
    settings = Settings(
        gaia_mode=os.getenv("GAIA_MODE", "simulator").strip().lower(),
        ticks_per_second=max(1, min(_int_env("GAIA_TICKS_PER_SECOND", 10), 30)),
        history_limit=max(10, _int_env("GAIA_HISTORY_LIMIT", 1000)),
        log_to_file=_bool_env("GAIA_LOG_TO_FILE", True),
        session_name=os.getenv("GAIA_SESSION_NAME", "local_demo").strip() or "local_demo",
        use_live_data=_bool_env("GAIA_USE_LIVE_DATA", False),
        data_mode=(os.getenv("GAIA_DATA_MODE", "live").strip().lower() or "live"),
        allow_fallback=_bool_env("GAIA_ALLOW_FALLBACK", True),
        autostart=_bool_env("GAIA_AUTOSTART", False),
        enable_cl_recording=_bool_env("GAIA_ENABLE_CL_RECORDING", False),
        enable_cl_data_stream=_bool_env("GAIA_ENABLE_CL_DATA_STREAM", True),
        enable_cl_stimulation=_bool_env("GAIA_ENABLE_CL_STIMULATION", False),
        cl_recording_seconds=max(0.0, _float_env("GAIA_CL_RECORDING_SECONDS", 0.0)),
        cors_origins=origins or ("http://localhost:5173", "http://127.0.0.1:5173"),
    )
    for folder in ("logs", "sessions", "recordings"):
        (settings.data_dir / folder).mkdir(parents=True, exist_ok=True)
    return settings
