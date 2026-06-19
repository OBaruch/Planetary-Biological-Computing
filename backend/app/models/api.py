from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


DemoEventType = Literal[
    "wildfire",
    "earthquake",
    "heatwave",
    "good_news",
    "conflict",
    "renewable_boost",
    "ocean_recovery",
    "pollution_spike",
    "biodiversity_gain",
    "solar_storm",
]


class DemoEventRequest(BaseModel):
    type: DemoEventType
    intensity: float = Field(default=0.7, ge=0.0, le=1.0)
    duration_seconds: float = Field(default=30.0, ge=1.0, le=300.0)


class RootResponse(BaseModel):
    name: str
    tagline: str
    mode: str
    running: bool
    session_id: str
    ethics: str


class HealthResponse(BaseModel):
    status: Literal["ok"]
    version: str
    mode: str
    running: bool
    session_id: str
    adapter_status: str
    cl_sdk_available: bool
    uptime_seconds: float


class ControlResponse(BaseModel):
    ok: bool
    message: str
    running: bool
    mode: str
    session_id: str


class SimulationStatus(BaseModel):
    running: bool
    mode: str
    session_id: str
    started_at: datetime | None
    ticks: int
    last_error: str | None
    adapter_status: str
    adapter_metrics: dict[str, str | int | float | bool | None]
    history_size: int
    history_limit: int
    websocket_clients: int
    uptime_seconds: float


class ConfigResponse(BaseModel):
    version: str
    gaia_mode: str
    data_mode: str
    ticks_per_second: int
    history_limit: int
    use_live_data: bool
    allow_fallback: bool
    log_to_file: bool
    cors_origins: list[str]
    cl_sdk_available: bool


class SessionSummary(BaseModel):
    session_id: str
    path: str
    size_bytes: int
    modified_at: datetime
