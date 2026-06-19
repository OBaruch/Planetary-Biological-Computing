from __future__ import annotations

from fastapi import APIRouter, Query, Request

from app.models.geo_event import GeoEventsResponse
from app.services.simulation_runner import SimulationRunner

router = APIRouter(prefix="/api/events", tags=["events"])


def get_runner(request: Request) -> SimulationRunner:
    return request.app.state.runner


@router.get("/live", response_model=GeoEventsResponse)
async def events_live(request: Request, refresh: bool = Query(default=False)) -> GeoEventsResponse:
    """Current geolocated events (live connectors + simulation-derived).

    Falls back to clearly-flagged ``simulated`` demo events when no live
    sources are configured or reachable.
    """
    runner = get_runner(request)
    if refresh:
        await runner.geo_events.refresh_live(force=True)
    planet_inputs = (await runner.get_state()).planet_inputs
    return await runner.geo_events.get_response(planet_inputs)
