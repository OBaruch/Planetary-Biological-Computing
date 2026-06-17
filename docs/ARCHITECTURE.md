# GAIA-1 Architecture

GAIA-1 is organized as a realtime closed-loop simulator. The loop is architectural, not biological causality: planetary inputs become stimulation intents, simulated spikes become decoded visual actions, and the digital planet evolves.

## Layers

1. Planet Data Layer
   - `PlanetDataProvider` generates deterministic mock/offline planetary signals.
   - Optional live-data integration should return the same `PlanetInputs` model and fall back to mock mode.

2. Planet Encoder
   - `PlanetEncoder` normalizes selected variables into an eight-value signature.
   - It emits `StimulationIntent` with target channels, intensity, burst frequency, metadata, and a clear simulator non-causality flag.

3. Neural Adapter
   - `NeuralAdapter` defines `start`, `stop`, `read_tick`, `send_stimulation_intent`, and `get_metrics`.
   - `CorticalSimulatorAdapter` uses `import cl`, `cl.open()`, `neurons.loop(...)`, and `tick.analysis.spikes`.
   - `FallbackSyntheticAdapter` generates deterministic synthetic spikes and clearly reports fallback mode.

4. Spike Decoder
   - `SpikeDecoder` maps simulated spikes into visualization metrics and action vectors.
   - Channel groups are UI metaphors only: climate regulation, biosphere recovery, human pressure, and chaos/stress.

5. Planet Simulation
   - `PlanetSimulation` combines planet inputs, decoded actions, and controlled noise.
   - Output is a JSON-serializable `SimulationFrame`.

6. API And WebSocket
   - FastAPI exposes health, status, config, state, history, sessions, and control endpoints.
   - `/ws/live` broadcasts snapshots without blocking the runner loop.

7. Frontend
   - Vite + React + TypeScript renders the dashboard.
   - Three.js visualizes the planet and responds to temperature, biosphere, ocean, chaos, recovery, and neural pulse intensity.

## Runner Lifecycle

`SimulationRunner` owns one active simulation task. It prevents duplicate loops, keeps a bounded history deque, tracks `started_at`, `ticks`, `last_error`, adapter status, and session ID, and shuts down the adapter during stop/reset/application shutdown.

## Sessions And Logs

When `GAIA_LOG_TO_FILE=true`, snapshots are appended as JSONL under:

- `backend/data/sessions/`
- `backend/data/logs/`

The `/api/sessions` endpoint lists recent session files.

## Future CL1 / Cortical Cloud Adapter

A real deployment should add a new adapter behind the same `NeuralAdapter` interface. That adapter should handle authentication, deployment/session selection, biological safety constraints, reviewed stimulation plans, recording policy, and ethics approvals.
