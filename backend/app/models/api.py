from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


DemoEventType = Literal[
    "wildfire",
    "earthquake",
    "heatwave",
    "good_news",
    "conflict",
    "renewable_boost",
]


class DemoEventRequest(BaseModel):
    type: DemoEventType
    intensity: float = Field(default=0.7, ge=0.0, le=1.0)


class RootResponse(BaseModel):
    name: str
    tagline: str
    mode: str
    running: bool
    session_id: str
    ethics: str


class HealthResponse(BaseModel):
    status: Literal["ok"]
    mode: str
    running: bool
    session_id: str
    adapter_status: str


class ControlResponse(BaseModel):
    ok: bool
    message: str
    running: bool
    mode: str
    session_id: str
