from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request

from app.models.api import ConfigResponse, ControlResponse, DemoEventRequest, HealthResponse, RootResponse, SessionSummary, SimulationStatus
from app.models.planet import SimulationFrame
from app.services.simulation_runner import ETHICS_TEXT, SimulationRunner


router = APIRouter()


def get_runner(request: Request) -> SimulationRunner:
    return request.app.state.runner


@router.get("/", response_model=RootResponse)
async def root(request: Request) -> RootResponse:
    runner = get_runner(request)
    return RootResponse(
        name="GAIA-1: Earth Dreams",
        tagline="The first neuron-ready planetary simulator.",
        mode=runner.mode,
        running=runner.running,
        session_id=runner.session_id,
        ethics=ETHICS_TEXT,
    )


@router.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    runner = get_runner(request)
    status = await runner.get_status()
    return HealthResponse(
        status="ok",
        version=runner.settings.app_version,
        mode=runner.mode,
        running=runner.running,
        session_id=runner.session_id,
        adapter_status=runner.adapter_status,
        cl_sdk_available=runner.cl_sdk_available,
        uptime_seconds=status.uptime_seconds,
    )


@router.get("/api/status", response_model=SimulationStatus)
async def status(request: Request) -> SimulationStatus:
    return await get_runner(request).get_status()


@router.get("/api/state", response_model=SimulationFrame)
async def state(request: Request) -> SimulationFrame:
    return await get_runner(request).get_state()


@router.get("/api/history", response_model=list[SimulationFrame])
async def history(request: Request, limit: int = Query(default=200, ge=1, le=5000)) -> list[SimulationFrame]:
    return await get_runner(request).get_history(limit=limit)


@router.get("/api/config", response_model=ConfigResponse)
async def config(request: Request) -> ConfigResponse:
    return get_runner(request).get_config()


@router.get("/api/sessions", response_model=list[SessionSummary])
async def sessions(request: Request) -> list[SessionSummary]:
    return get_runner(request).list_sessions()


@router.post("/api/control/start", response_model=ControlResponse)
async def start(request: Request) -> ControlResponse:
    runner = get_runner(request)
    try:
        message = await runner.start()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return ControlResponse(ok=True, message=message, running=runner.running, mode=runner.mode, session_id=runner.session_id)


@router.post("/api/control/stop", response_model=ControlResponse)
async def stop(request: Request) -> ControlResponse:
    runner = get_runner(request)
    message = await runner.stop()
    return ControlResponse(ok=True, message=message, running=runner.running, mode=runner.mode, session_id=runner.session_id)


@router.post("/api/control/reset", response_model=ControlResponse)
async def reset(request: Request) -> ControlResponse:
    runner = get_runner(request)
    message = await runner.reset()
    return ControlResponse(ok=True, message=message, running=runner.running, mode=runner.mode, session_id=runner.session_id)


@router.post("/api/control/demo-event", response_model=ControlResponse)
async def demo_event(request: Request, event: DemoEventRequest) -> ControlResponse:
    runner = get_runner(request)
    message = await runner.inject_demo_event(event)
    return ControlResponse(ok=True, message=message, running=runner.running, mode=runner.mode, session_id=runner.session_id)
