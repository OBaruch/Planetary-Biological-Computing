from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.api.websocket import LiveBroadcaster
from app.config import load_settings
from app.services.simulation_runner import SimulationRunner

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

settings = load_settings()
broadcaster = LiveBroadcaster()
runner = SimulationRunner(settings=settings, broadcaster=broadcaster)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    if settings.autostart:
        await runner.start()
    try:
        yield
    finally:
        await runner.shutdown()


app = FastAPI(
    title="GAIA-1: Earth Dreams API",
    description="Neuron-ready planetary simulator using the Cortical Labs CL SDK Simulator or fallback mode.",
    version="0.1.0",
    lifespan=lifespan,
)
app.state.runner = runner

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.websocket("/ws/live")
async def websocket_live(websocket: WebSocket) -> None:
    await broadcaster.connect(websocket)
    try:
        await websocket.send_json((await runner.get_state()).model_dump(mode="json"))
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await broadcaster.disconnect(websocket)
    except Exception:
        await broadcaster.disconnect(websocket)
