# Specification: GAIA-1: Earth Dreams

> **Document type:** Specification (the *what*). Derived from [intent.md](intent.md); executed by [plan.md](plan.md).
> **Status:** *As-built, reconstructed.* Each requirement describes behavior that already exists and points to its evidence in code and tests. Nothing here is a change request. Gaps are marked **Partial** and cross-referenced to [possible-improvements.md](../possible-improvements.md).

Status legend: **Implemented** · **Partial** · **Not implemented** (planned in the roadmap).

## 1. Context and constraints

| ID | Constraint |
| --- | --- |
| K1 | Runs locally: Python backend (FastAPI) on `:8000`, Vite dev server on `:5173` (or `:5174`). |
| K2 | `cl-sdk` is optional at runtime. Its absence must not prevent operation when fallback is allowed. |
| K3 | Configuration comes only from environment variables / `.env`. |
| K4 | **Repository rule (documentation pass):** the original source code is frozen. Documentation may change; code may not. |

## 2. Functional requirements

### 2.1 Simulation loop

| ID | Requirement | Status | Evidence |
| --- | --- | --- | --- |
| FR-01 | The system runs a periodic loop at `GAIA_TICKS_PER_SECOND` (clamped 1–30). Each tick produces one `SimulationFrame`. | Implemented | `simulation_runner.py::_loop`, `config.py` |
| FR-02 | Start and stop are idempotent. Reset clears history and state and restarts if the loop was running. | Implemented | `SimulationRunner.start/stop/reset`; `test_controls.py::test_start_stop_are_idempotent`, `test_reset_endpoint` |
| FR-03 | A bounded in-memory history (`GAIA_HISTORY_LIMIT`, min 10) is served via `/api/history?limit=1..5000`. | Implemented | `test_controls.py::test_history_limit` |
| FR-04 | An error inside one tick is recorded as `last_error` and does not stop the loop. | Implemented | `_loop` `except Exception` |
| FR-05 | Optional autostart when the application starts; clean adapter shutdown when it stops. | Implemented | `main.py::lifespan` |

### 2.2 Planet data

| ID | Requirement | Status | Evidence |
| --- | --- | --- | --- |
| FR-10 | `demo` mode produces deterministic-shaped synthetic signals for 22 raw indices. | Implemented | `planet_data.py::_mock_inputs`; `test_planet_data.py` |
| FR-11 | `live` mode starts from a neutral baseline, overlays only real values from active sources, and reports provenance per field. | Implemented | `_live_inputs`, `SimulationFrame.signal_provenance` |
| FR-12 | Seven derived scores (climate pressure, human pressure, recovery potential, planetary stress, biosphere stability, chaos, resilience) are computed in [0, 1] from the raw fields. | Implemented | `_compose` |
| FR-13 | Ten demo event types can be injected with intensity [0, 1] and duration 1–300 s. Their effect decays linearly. | **Partial**: effective only in `demo` mode; the duration assumes 10 ticks per second (F1, F2) | `inject_event`, `_event_effects`; `test_simulation.py::test_demo_event_injection` |

### 2.3 Encoding, neural adapter, decoding

| ID | Requirement | Status | Evidence |
| --- | --- | --- | --- |
| FR-20 | Planet inputs are encoded into a `StimulationIntent`: an 8-value signature, target channels 0–63, intensity [0, 1], burst frequency 8–50 Hz, SHA-1 signature, `simulator_non_causal` flag. | Implemented | `encoder.py`; `test_encoder.py` |
| FR-21 | A `NeuralAdapter` abstraction with a CL SDK Simulator implementation and a deterministic synthetic fallback. | Implemented | `neural_adapter.py`, `cortical_simulator_adapter.py`, `fallback_synthetic_adapter.py`; `test_fallback_adapter.py` |
| FR-22 | If the CL SDK cannot start and `GAIA_ALLOW_FALLBACK=true`, the runner switches to the fallback adapter and labels it as such. Otherwise start fails with HTTP 500. | Implemented | `SimulationRunner.start`, `routes.py::start` |
| FR-23 | Optional CL SDK recording (HDF5 to `backend/data/recordings/`) and a data stream `gaia_earth_dreams_state`. | Implemented (untested here; SDK-dependent) | `_start_optional_recording`, `_start_optional_data_stream` |
| FR-24 | Physical stimulation happens only when `GAIA_ENABLE_CL_STIMULATION=true`. | Implemented | `_try_physical_stim` |
| FR-25 | Spikes are decoded into `NeuralMetrics` (rate, active channels, entropy, synchrony, burstiness, stability/chaos/recovery signals, latency, tick rate) and a `DecodedAction` with a 9-key action vector, primary action, confidence, and metaphor notice. | Implemented | `spike_decoder.py`; `test_decoder.py` |
| FR-26 | `PlanetSimulation` evolves 8 bounded state variables plus `visual_intensity` and a mood label. | Implemented | `planet_simulation.py`; `test_simulation.py` |

### 2.4 Real-data sources

| ID | Requirement | Status | Evidence |
| --- | --- | --- | --- |
| FR-30 | A declarative catalog of 10 sources (7 key-free) is exposed via `GET /api/sources` with configured, enabled, active, health, and masked credentials. | Implemented | `catalog.py`, `registry.py`; `test_sources_api.py::test_list_sources` |
| FR-31 | Users save, delete, toggle, and test credentials per source. Testing runs one real fetch and can validate unsaved keys. | Implemented | `api/sources.py`; `test_sources_api.py`, `test_registry.py` |
| FR-32 | Credentials persist to a local JSON file with atomic writes. Environment variables `GAIA_KEY_<SOURCE>_<FIELD>` are used as a fallback. | Implemented | `credentials.py`; `test_credentials.py` |
| FR-33 | Signal connectors are polled at most every 120 s, geo connectors every 60 s, and never on every tick. A settings change triggers a background refresh. | Implemented | `SignalService`, `GeoEventService`, `rebuild_sources` |
| FR-34 | When several sources feed the same field, ground stations win: OpenAQ > OpenWeather > Open-Meteo. | Implemented | `_SIGNAL_PRIORITY`; `test_signals.py` |
| FR-35 | Scalar fields are derived from geo events: earthquakes (USGS), wildfire risk (FIRMS), volcanic activity (EONET/GDACS). | Implemented | `derive_geo_signals`; `test_signals.py` |
| FR-36 | Geolocated events are normalized to `GeoPlanetEvent` with valid coordinates, sorted by status and intensity, and capped at 80. | Implemented | `normalizer.py`, `geo_event.py`; `test_geo_events.py` |
| FR-37 | Source health reflects fetch success. | **Partial**: geo sources returning empty lists are marked `ok` (F3) | `GeoEventService.refresh_live` |

### 2.5 API and streaming

| ID | Requirement | Status | Evidence |
| --- | --- | --- | --- |
| FR-40 | REST endpoints: `/`, `/health`, `/api/status`, `/api/state`, `/api/history`, `/api/config`, `/api/sessions`, `/api/control/*`, `/api/events/live`, `/api/sources*`. | Implemented | `api/*.py`; `test_health.py` |
| FR-41 | `WS /ws/live` sends the current frame on connect, then every new frame. Dead sockets are dropped. | Implemented | `main.py`, `websocket.py` |
| FR-42 | When enabled, frames are logged as JSONL per session. `/api/sessions` lists the latest 100 sessions. | Implemented | `session_logger.py`, `list_sessions` |

### 2.6 Dashboard

| ID | Requirement | Status | Evidence |
| --- | --- | --- | --- |
| FR-50 | A real-time 3D globe with atmosphere, clouds, stars, and event markers, pulses, and arcs that react to planet state and neural activity. | Implemented | `components/Visuals/*` |
| FR-51 | Event priority: WebSocket snapshot → REST polling → local demo events (demo mode only). | Implemented | `hooks/useGeoEvents.ts` |
| FR-52 | Panels for planet metrics (unsourced fields disabled), neural activity, the event list and detail, a timeline, and controls with 10 demo events. | Implemented | `components/*` |
| FR-53 | A Settings panel for data-source keys, toggles, and connection tests. | Implemented | `components/Settings/*`, `hooks/useSources.ts` |
| FR-54 | WebSocket reconnection with backoff and REST polling while disconnected. | Implemented | `App.tsx` |
| FR-55 | A permanent ethics banner and explicit simulator-mode copy. | Implemented | `EthicsBanner.tsx`, `App.tsx` |
| FR-56 | Optional photographic Earth textures with a procedural fallback. | Implemented | `useEarthTextures.ts`, `proceduralEarth.ts` |

## 3. Non-functional requirements

| ID | Requirement | Status |
| --- | --- | --- |
| NFR-01 | **Honesty:** mode, metaphor notice, and non-causality flags appear in the API and UI. | Implemented |
| NFR-02 | **Resilience:** connectors never raise to the loop. Network failure degrades to "unsourced", never to a crash. | Implemented |
| NFR-03 | **Secret handling:** secrets are write-only over the API, masked on read, and stored in a gitignored file. | Implemented (local scope only; see S1, S2) |
| NFR-04 | **Testability:** the suite runs offline without `cl-sdk`. | Implemented (44 tests) |
| NFR-05 | **Portability:** Unix (Makefile) and Windows (PowerShell) launch paths. | Implemented |
| NFR-06 | **Reproducible installs.** | **Partial**: unpinned Python deps; npm lockfile out of sync (B1–B3) |

## 4. Data contract (summary)

`SimulationFrame` = `{ timestamp, session_id, tick, mode, adapter_status, planet_inputs: PlanetInputs, encoded_signal: StimulationIntent, neural_metrics: NeuralMetrics, decoded_action: DecodedAction, planet_state: PlanetState, events: string[], events_geo: GeoPlanetEvent[], signal_provenance: {field: source_id} }`.

The authoritative definitions are in `backend/app/models/`, with TypeScript mirrors in `frontend/src/api/types.ts` and `frontend/src/types/`.

## 5. Acceptance criteria (as-built)

| ID | Criterion | How to verify |
| --- | --- | --- |
| AC-1 | All backend tests pass offline. | `pytest backend/tests` → 44 passed |
| AC-2 | A running backend advances ticks and records history. | `python scripts/smoke_test.py` exits 0 |
| AC-3 | The frontend type-checks and builds. | `cd frontend && npm install && npm run build` |
| AC-4 | Without `cl-sdk`, `/health` reports the fallback mode after start. | `GET /health` after `POST /api/control/start` |
| AC-5 | No endpoint returns a raw secret. | `test_sources_api.py::test_put_credentials_masks_secret` |

## 6. Out of scope

See [intent.md §5](intent.md#5-non-goals). Real-neuron adapters, replay, export, and public deployment are roadmap items ([plan.md §4](plan.md#4-future-phases-from-the-original-roadmap)).
