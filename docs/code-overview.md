# Code Overview

> This document was added during a later documentation pass. It explains the original code, which was **not modified**.

## 1. Big picture

```text
backend/app/main.py ── creates ── SimulationRunner (singleton) + LiveBroadcaster
        │                               │
   routers (api/*)                      ├── PlanetDataProvider   (planet inputs)
        │                               ├── SignalService        (scalar real-data overlay)
        └── request.app.state.runner ──►├── GeoEventService      (globe markers)
                                        ├── PlanetEncoder        (inputs → StimulationIntent)
                                        ├── NeuralAdapter        (CL SDK Simulator | Fallback)
                                        ├── SpikeDecoder         (spikes → metrics + action)
                                        ├── PlanetSimulation     (evolving PlanetState)
                                        └── SessionLogger        (JSONL)
```

All routers reach the shared `SimulationRunner` through `request.app.state.runner`. The runner owns one asyncio task (`gaia-simulation-loop`) that executes the tick pipeline.

## 2. Tick pipeline (`SimulationRunner._step_once`)

1. `_planet_inputs_and_geo()`
   - **demo**: `PlanetDataProvider.next()` returns synthetic sine-wave signals with event biases. `GeoEventService.current(inputs)` returns curated demo markers plus markers derived from the simulation.
   - **live**: cached geo events, plus `SignalService.overlay`, plus `derive_geo_signals()` (USGS quakes → earthquake fields, FIRMS fires → wildfire risk, EONET/GDACS volcanoes → volcanic index). `PlanetDataProvider.next(overlay, provenance)` fills every other field with a neutral baseline.
2. `PlanetEncoder.encode()` produces a `StimulationIntent`.
3. `adapter.send_stimulation_intent()`, then `adapter.read_tick()` returns the spikes (latency is measured).
4. `SpikeDecoder.decode()` produces `NeuralMetrics` + `DecodedAction`.
5. `PlanetSimulation.step()` produces a `PlanetState`.
6. The result is assembled into a `SimulationFrame`, stored as `latest`, appended to the history deque, written to JSONL, and broadcast over `/ws/live`.

Connectors are refreshed **inside the loop but on slow intervals**: geo events every 60 s, signals every 120 s. A settings change triggers a background refresh.

## 3. Backend modules

### Entry point and configuration

| File | Responsibility |
| --- | --- |
| `app/main.py` | Logging, settings, broadcaster, and runner singletons. Lifespan (optional autostart, shutdown). CORS. Includes routers. Defines `WS /ws/live` (sends the current frame on connect, then keeps the socket open). |
| `app/config.py` | Frozen `Settings` dataclass built from env vars (`_bool_env`, `_int_env`, `_float_env`). Loads `.env` from the repository root and creates `backend/data/{logs,sessions,recordings}`. `APP_VERSION = "0.2.0"`. |

### API (`app/api/`)

| File | Endpoints / role |
| --- | --- |
| `routes.py` | `/`, `/health`, `/api/status`, `/api/state`, `/api/history`, `/api/config`, `/api/sessions`, `/api/control/{start,stop,reset,demo-event}` |
| `events.py` | `GET /api/events/live` (optional forced refresh) |
| `sources.py` | `GET /api/sources`, `PUT/DELETE /api/sources/{id}/credentials`, `POST /api/sources/{id}/toggle`, `POST /api/sources/{id}/test` |
| `websocket.py` | `LiveBroadcaster`: a set of sockets guarded by an asyncio lock. Stale sockets are dropped when broadcasting. |

### Models (`app/models/`, Pydantic v2)

| File | Key types |
| --- | --- |
| `planet.py` | `PlanetInputs` (22 raw indices + 7 derived scores + active events), `PlanetState` (8 bounded variables + `visual_intensity` + mood label), `SimulationFrame` (the streamed unit, including `events_geo` and `signal_provenance`) |
| `neural.py` | `NeuralSpike` (channel 0–63), `StimulationIntent`, `NeuralMetrics`, `DecodedAction` (with `metaphor_notice`) |
| `geo_event.py` | `GeoPlanetEvent`: latitude is clamped, longitude wrapped to [-180, 180], intensity clamped. Includes `GeoEventsResponse`. |
| `data_source.py` | `SourceDescriptor`, `CredentialField`, `SourceStatus`, `SourceHealth`, request/response bodies for the sources API |
| `api.py` | `DemoEventRequest` (10 event types), `HealthResponse`, `SimulationStatus`, `ConfigResponse`, `SessionSummary`, … |

### Core services (`app/services/`)

| File | What it does |
| --- | --- |
| `simulation_runner.py` | Lifecycle (`start` / `stop` / `reset` / `shutdown`), the async loop with fixed-interval sleep, status/config/sessions, `ETHICS_TEXT`, idle frame. If the CL adapter fails to start and fallback is allowed, it switches to `FallbackSyntheticAdapter`. |
| `planet_data.py` | `PlanetDataProvider`. In **live** mode: `_NEUTRAL_FIELDS` baseline plus overlay. In **demo** mode: sinusoids at three time scales plus decaying `_EventBias`es. `_compose()` derives climate pressure, human pressure, recovery potential, planetary stress, biosphere stability, chaos, and resilience through fixed weighted sums. |
| `encoder.py` | `PlanetEncoder`. Builds an 8-value signature (temperature anomaly, CO₂, wildfire, quake magnitude, air quality, news tension, renewables, sentiment). Intensity = `0.72·stress + 0.28·(1−recovery)`. Burst frequency = 8–50 Hz. Each signature value picks a channel in one of four 16-channel groups (a neighbour channel is added when the value or intensity is high). The signature hash is the first 12 hex digits of its SHA-1. |
| `neural_adapter.py` | Abstract `NeuralAdapter` (`start`, `stop`, `read_tick`, `get_recent_spikes`, `send_stimulation_intent`, `get_metrics`, `status`). |
| `cortical_simulator_adapter.py` | Calls `import cl` → `cl.open()` → `neurons.loop(ticks_per_second, ignore_jitter=True)` and reads `tick.analysis.spikes`. Optional `neurons.record(...)` and `neurons.create_data_stream("gaia_earth_dreams_state")`, which receives the intent and planet inputs on every tick. Physical stimulation (`ChannelSet`, `StimDesign`, `neurons.stim`) runs only if `GAIA_ENABLE_CL_STIMULATION=true`. SDK calls have `TypeError` fallbacks for signature differences. |
| `fallback_synthetic_adapter.py` | Seeded RNG (42). Spike count grows with intent intensity. About 68–92 % of spikes land on the intent's target channels. Reports "Fallback Synthetic Mode". |
| `spike_decoder.py` | Groups: 0–15 `climate_regulation`, 16–31 `biosphere_recovery`, 32–47 `human_pressure`, 48–63 `chaos_stress`. Computes normalized Shannon entropy over 64 channels, synchrony (timestamp spread), burstiness, chaos/recovery/stability signals. The dominant group selects which action weights are filled. `primary_action` is the arg-max. |
| `planet_simulation.py` | `PlanetSimulation`. Computes a target value for each state variable from inputs, metrics, and the action vector, plus seeded noise. Each variable moves toward its target with `lerp` (α = 0.14–0.2). `_mood()` maps chaos/recovery/resilience to five labels. |
| `session_logger.py` | Session ID `<name>_<UTC stamp>_<8 hex>`. Writes each frame as one JSON line to both `data/sessions/` and `data/logs/`. |
| `math_utils.py` | `clamp`, `normalize`, `lerp` |

### Real-data layer (`app/services/data_sources/`)

| File | What it does |
| --- | --- |
| `catalog.py` | `SOURCE_CATALOG`: 10 declarative `SourceDescriptor`s. This is the single source of truth for the UI and the connector factory. |
| `credentials.py` | `CredentialStore`. JSON file `backend/data/credentials.json` with atomic writes (temp file + `os.replace`) and a thread lock. Falls back to `GAIA_KEY_<SOURCE>_<FIELD>` env vars. `_mask` keeps only the last 4 characters visible. |
| `registry.py` | `SourceRegistry`. A source is *active* when it is enabled (default true) and configured. Builds connectors (`build_geo_connector`, `build_signal_connector`, `build_one` for testing a key before saving it). Keeps an in-memory health record per source. |
| `signal_service.py` | `SignalService` polls the active signal connectors and merges them by priority (OpenAQ > OpenWeather > Open-Meteo) into overlay + provenance. `derive_geo_signals()` turns events into scalar fields. |
| `signals/base.py` | `SignalConnector` protocol, `SignalContribution`, 14 `WORLD_SAMPLE_POINTS` cities used to approximate global indices from point APIs. |
| `signals/open_meteo.py`, `openweather.py`, `openaq.py`, `gdelt.py`, `noaa_swpc.py` | One async `httpx` connector per API. Each one swallows its own errors and returns `None`. |

### Geolocated events (`app/services/geo_events/`)

| File | What it does |
| --- | --- |
| `__init__.py` | `GeoEventService`. In **live** mode it caches events from active connectors only (strict). In **demo** mode it returns curated demo events plus events synthesized from the simulation. Events are sorted by status, then intensity, and capped at 80. |
| `base.py` | `GeoEventConnector` protocol and coordinate helpers |
| `normalizer.py` | `build_event` plus per-API normalizers (USGS, EONET, GDACS) and type/status mapping |
| `usgs_earthquakes.py`, `eonet.py`, `gdacs.py`, `iss.py`, `firms.py` | One async connector per API (FIRMS parses CSV and needs a `MAP_KEY`) |
| `demo_events.py` | Fixed demo places/events and `synthesize_from_simulation()` (demo mode only) |

## 4. Frontend (`frontend/src/`)

| Path | Responsibility |
| --- | --- |
| `main.tsx`, `App.tsx` | Bootstrap. On load it fetches state and history, **calls `start`**, then opens the WebSocket. Reconnects with exponential backoff (up to 8 s) and polls REST every 2.5 s while disconnected. Keeps the last 80 frames. Lays out the dashboard. |
| `api/client.ts`, `api/types.ts` | REST/WS client (`VITE_API_BASE_URL`, `VITE_WS_URL`) and TypeScript mirrors of the backend models |
| `api/eventsClient.ts`, `api/sourcesClient.ts` | Clients for `/api/events/live` and `/api/sources/*` |
| `hooks/useGeoEvents.ts` | Picks globe events by priority: WebSocket snapshot → REST polling → local demo events (**demo mode only**) |
| `hooks/useSources.ts` | Loads the source catalog and exposes save, clear, toggle, and test actions |
| `hooks/useEarthTextures.ts` | Loads optional textures from `public/textures/earth/`. Falls back to procedural textures. |
| `components/Visuals/*` | `RealTimeEarthGlobe` (R3F canvas) composed of `EarthSphere`, `EarthAtmosphere`, `EarthClouds`, `SpaceBackground`, `GeoEventMarker`, `GeoEventPulse`, `GeoEventArc` |
| `components/Panels/*` | `GlobalEventsPanel` (event list), `EventDetailPanel` (selected event) |
| `components/Settings/*` | `SettingsButton`, `SettingsPanel`, `SourceCard` (key entry, test, toggle) |
| `components/*.tsx` | `PlanetMetricsPanel`, `NeuralActivityPanel`, `MetricBar` (shows disabled state for unsourced fields), `ControlPanel` (start/stop/reset + 10 demo-event buttons), `ConnectionStatus`, `EventTimeline`, `EthicsBanner` |
| `components/PlanetView.tsx` | Earlier planet visual. Nothing imports it any more; it appears to have been superseded by `RealTimeEarthGlobe` (inferred). |
| `utils/geo.ts`, `utils/proceduralEarth.ts` | Lat/lon → `Vector3`, arc curves, event visual styles; canvas-generated Earth and cloud textures |
| `data/demoGeoEvents.ts` | Static demo events for the globe |
| `styles/*.css` | Global, globe, and settings styles |

## 5. Scripts and tooling

| File | Role |
| --- | --- |
| `scripts/check_env.py` | Prints which modules and files are present. Fails if FastAPI, Uvicorn, Pydantic, or project files are missing. Only warns if `cl` is missing. |
| `scripts/run_backend.py` | Runs uvicorn from the repository root with `GAIA_MODE=simulator`, `GAIA_ALLOW_FALLBACK=true`, `CL_SDK_VISUALISATION=0` as defaults |
| `scripts/smoke_test.py` | Calls health → start → state → status → demo-event → history against `127.0.0.1:8000` |
| `scripts/run_backend.ps1`, `run_frontend.ps1` | Windows equivalents (creates `.venv` with `py -3.12`; runs `npm install` if needed) |
| `Makefile` | `backend`, `frontend`, `dev` (hint only), `test` |

## 6. Tests (`backend/tests/`)

`conftest.py` forces `GAIA_MODE=fallback`, `GAIA_DATA_MODE=demo`, and `GAIA_LOG_TO_FILE=false`, and adds `backend/` to `sys.path`. As a result, the suite needs neither `cl-sdk` nor network access.

| File | Tests | Focus |
| --- | --- | --- |
| `test_health.py` | 3 | `/health`, `/api/state`, status/config/sessions endpoints |
| `test_controls.py` | 4 | Idempotent start/stop, reset, demo-event validation, history limit |
| `test_encoder.py` | 1 | Intent ranges |
| `test_decoder.py` | 1 | Metrics/action from fake spikes |
| `test_simulation.py` | 2 | Planet simulation step, demo-event injection |
| `test_fallback_adapter.py` | 1 | Synthetic spikes |
| `test_planet_data.py` | 1 | Mock inputs |
| `test_geo_events.py` | 11 | Normalizers, model bounds, service modes |
| `test_registry.py` | 5 | Active/configured logic, connector factory |
| `test_credentials.py` | 4 | Persistence, masking, env fallback |
| `test_signals.py` | 6 | Signal parsing/merging, geo-derived signals |
| `test_sources_api.py` | 5 | Listing, masked credentials, toggle, missing-key test, unknown source 404 |

Result observed during the documentation pass: **44 passed** (Python 3.11, without `cl-sdk`).
