from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.models.data_source import (
    CredentialUpdate,
    SourcesResponse,
    SourceStatus,
    TestRequest,
    TestResult,
    ToggleRequest,
)
from app.services.data_sources.catalog import get_descriptor
from app.services.simulation_runner import SimulationRunner

router = APIRouter(prefix="/api/sources", tags=["sources"])


def get_runner(request: Request) -> SimulationRunner:
    return request.app.state.runner


def _status_or_404(runner: SimulationRunner, source_id: str) -> SourceStatus:
    status = runner.registry.status(source_id)
    if status is None:
        raise HTTPException(status_code=404, detail=f"Unknown source '{source_id}'")
    return status


@router.get("", response_model=SourcesResponse)
async def list_sources(request: Request) -> SourcesResponse:
    """Catalog of every data source with per-user state (never exposes secrets)."""
    runner = get_runner(request)
    statuses = runner.registry.statuses()
    return SourcesResponse(
        data_mode=runner.settings.data_mode,
        active_count=sum(1 for s in statuses if s.active),
        total_count=len(statuses),
        sources=statuses,
    )


@router.put("/{source_id}/credentials", response_model=SourceStatus)
async def set_credentials(request: Request, source_id: str, body: CredentialUpdate) -> SourceStatus:
    runner = get_runner(request)
    if get_descriptor(source_id) is None:
        raise HTTPException(status_code=404, detail=f"Unknown source '{source_id}'")
    runner.credentials.set(source_id, body.secrets, enabled=body.enabled)
    await runner.rebuild_sources()
    return _status_or_404(runner, source_id)


@router.delete("/{source_id}/credentials", response_model=SourceStatus)
async def clear_credentials(request: Request, source_id: str) -> SourceStatus:
    runner = get_runner(request)
    if get_descriptor(source_id) is None:
        raise HTTPException(status_code=404, detail=f"Unknown source '{source_id}'")
    runner.credentials.delete(source_id)
    await runner.rebuild_sources()
    return _status_or_404(runner, source_id)


@router.post("/{source_id}/toggle", response_model=SourceStatus)
async def toggle_source(request: Request, source_id: str, body: ToggleRequest) -> SourceStatus:
    runner = get_runner(request)
    if get_descriptor(source_id) is None:
        raise HTTPException(status_code=404, detail=f"Unknown source '{source_id}'")
    runner.credentials.set_enabled(source_id, body.enabled)
    await runner.rebuild_sources()
    return _status_or_404(runner, source_id)


@router.post("/{source_id}/test", response_model=TestResult)
async def test_source(request: Request, source_id: str, body: TestRequest | None = None) -> TestResult:
    """Run one live fetch to confirm what real data the credentials reach."""
    runner = get_runner(request)
    descriptor = get_descriptor(source_id)
    if descriptor is None:
        raise HTTPException(status_code=404, detail=f"Unknown source '{source_id}'")

    secrets = body.secrets if body else {}
    connector = runner.registry.build_one(source_id, secrets)
    if connector is None:
        return TestResult(ok=False, error="Missing required credentials for this source.")

    try:
        result = await connector.fetch()
    except Exception as exc:  # connectors are defensive, but never leak a 500
        runner.registry.record_health(source_id, ok=False, error=str(exc))
        return TestResult(ok=False, error=str(exc))

    if descriptor.kind == "geo_event":
        events = result or []
        count = len(events)
        sample = events[0].label if events else None
    else:
        count = len(result.fields) if result and result.fields else 0
        sample = result.detail if result else None

    ok = count > 0
    error = None if ok else "Connected but no data returned (check the key, or try again later)."
    runner.registry.record_health(source_id, ok=ok, count=count, error=error)
    return TestResult(ok=ok, count=count, error=error, sample=sample)
