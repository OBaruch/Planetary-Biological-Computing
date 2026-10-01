# Possible Improvements

> **None of the items below have been applied.** The source code is preserved exactly as originally written, to keep the historical implementation intact. This list exists only to record observations made during the documentation pass. If any item is ever addressed, it should be a separate, explicit change.

Each item is labelled with how it was established:

- **Verified**: reproduced or directly confirmed by reading or running the code.
- **Observed**: visible in the code, but its impact was not measured.

## 1. Functional inconsistencies

| # | Finding | Evidence | Level |
| --- | --- | --- | --- |
| F1 | **Demo events have no effect in the default `live` data mode.** `PlanetDataProvider.inject_event()` stores a bias. Only `_mock_inputs()` (demo mode) consumes biases, and `_live_inputs()` passes `active_events=[]`. The API still answers "… injected …", and the dashboard shows the 10 injection buttons in both modes. | `backend/app/services/planet_data.py`, `frontend/src/components/ControlPanel.tsx` | Verified (code reading) |
| F2 | Demo-event duration assumes 10 ticks per second: `ttl = duration_seconds * 10`. With `GAIA_TICKS_PER_SECOND=20`, an event lasts half as long as requested. | `planet_data.py` (`inject_event`) | Verified (code reading) |
| F3 | Geo connectors swallow errors and return `[]`, and `GeoEventService.refresh_live()` then records `ok=True` with `count=0`. A failing geo source therefore looks healthy, while signal sources with no data are marked `ok=False`. | `geo_events/__init__.py`, `data_sources/signal_service.py` | Verified (code reading) |
| F4 | `PlanetSimulation.reset()` calls `self.__init__()`, which silently resets a custom seed to 42. It is not used by the runner, which builds a new instance instead. | `planet_simulation.py` | Observed |
| F5 | In `CorticalSimulatorAdapter.stop()`, the `except TypeError` branch retries the identical `__exit__(None, None, None)` call. | `cortical_simulator_adapter.py` | Observed |

## 2. Documentation drift (inside the original docs and docstrings)

| # | Finding | Level |
| --- | --- | --- |
| D1 | The `GET /api/events/live` docstring says it "falls back to clearly-flagged simulated demo events". In strict live mode it does not: `GeoEventService` returns only real events. | Verified |
| D2 | The original README lists "Local demo events … always available" as the third event source. The frontend uses them only when `dataMode === "demo"`. | Verified |
| D3 | `docs/ARCHITECTURE.md` describes the data layer as "mock/offline" and does not mention the source catalog, credential store, registry, or signal/geo services added on 18 June. | Verified |
| D4 | The version is declared in three places with different values: `APP_VERSION = "0.2.0"` (`config.py`, reported by `/health`), `FastAPI(version="0.1.0")` (`main.py`, OpenAPI), and `"version": "0.1.0"` (`frontend/package.json`). | Verified |

## 3. Build and dependency hygiene

| # | Finding | Level |
| --- | --- | --- |
| B1 | `frontend/package-lock.json` is out of sync with `package.json`. `npm ci` fails (missing `@emnapi/*` entries), while `npm install` followed by `npm run build` succeeds. | Verified (run on Node 22) |
| B2 | `cl-sdk` is a hard line in `requirements.txt` even though the code treats it as optional. On machines where it cannot be installed, the whole `pip install -r` fails. An "extras" or separate requirements file would match the runtime behavior. | Observed |
| B3 | Test-only dependencies (`pytest`) are mixed with runtime dependencies. All versions use open `>=` ranges, so builds are not reproducible. Running the tests already emits a Starlette deprecation warning about `httpx`. | Verified (warning seen) |
| B4 | The production bundle is a single chunk of about 1.1 MB, and `chunkSizeWarningLimit` was raised to 1200 to silence the warning. Code-splitting the Three.js scene would reduce initial load. | Verified (build output) |

## 4. Code-level observations

| # | Finding | Level |
| --- | --- | --- |
| C1 | `SessionLogger` writes every frame twice, to `data/sessions/` and `data/logs/`, with identical payloads. | Verified |
| C2 | `frontend/src/components/PlanetView.tsx` is not imported anywhere. It is probably superseded by `RealTimeEarthGlobe`. | Verified |
| C3 | The connector factory in `registry.py` is an `if` chain keyed by source ID. Adding a source requires editing both the catalog and the registry, even though the catalog is described as the single source of truth. | Observed |
| C4 | The dashboard calls `POST /api/control/start` automatically on every page load. Opening the page from a second browser therefore also "starts" the shared simulation. | Observed |
| C5 | `GAIA_USE_LIVE_DATA` is parsed and reported but no longer drives behavior. It is documented as "legacy". | Verified |
| C6 | The decoder's synchrony uses a fixed 25,000 µs spread constant, and the activity level assumes 18 spikes per tick is "full". Both are tuned for the fallback adapter's output, not for real recordings. | Observed |

## 5. Security and operations (local-MVP context)

| # | Finding | Level |
| --- | --- | --- |
| S1 | API keys are stored as plain text in `backend/data/credentials.json`. The file is gitignored and the API only exposes masked values, which is acceptable for a single-user local MVP but not for multi-user hosting. | Verified |
| S2 | There is no authentication on control or credential endpoints. Anyone who can reach the backend can start or stop the loop or replace keys. CORS limits browsers, not other clients. | Verified |
| S3 | No LICENSE file. Reuse terms are undefined. | Verified |

## 6. Ideas aligned with the original roadmap

These come from [ROADMAP.md](ROADMAP.md) and are repeated here only for convenience: recording replay, session export with charts, a CL1/Cortical Cloud adapter behind `NeuralAdapter`, safety gates and manual approval before any biological stimulation, and the remaining catalog sources (NWS, Smithsonian volcanoes, Electricity Maps, OpenSky, …).
