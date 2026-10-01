# Intent: GAIA-1: Earth Dreams

> **Document type:** Intent (the *why*). This is the first artifact of the intent → spec → plan chain.
> **Status:** *Reconstructed.* It was written after the fact from the existing repository: code, original docs, UI copy, and git history. It records what the project set out to do; it is not a new direction.
> **Downstream:** [spec.md](spec.md) (the *what*) → [plan.md](plan.md) (the *how* and *when*).

## 1. Intent statement

Build a **neuron-ready planetary simulator**. It closes a real-time loop between Earth's live signals and a neural system:

1. encode planetary data into stimulation intents;
2. read neural spikes;
3. decode them into planet-level actions;
4. visualize a living digital Earth.

Today the loop runs on the Cortical Labs CL SDK Simulator. The design lets a real CL1 / Cortical Cloud adapter replace the simulator later without redesigning the rest of the system.

## 2. Problem

Biological computing platforms need software that turns messy real-world data into stimulation patterns and turns neural activity back into something meaningful and visible. Real neurons are not available during development, and that kind of demo can easily overstate what it shows. The project addresses both problems: it gives the whole pipeline a working shape, and it bakes honesty about its limits into the product.

## 3. Desired outcomes

| ID | Outcome | Source |
| --- | --- | --- |
| O1 | The complete loop (data → encoder → neural adapter → decoder → planet simulation → UI) runs locally in real time. | README "What This Is" |
| O2 | The neural layer can be swapped through one interface (`NeuralAdapter`). It works with the CL SDK Simulator and degrades gracefully without it. | README, `ARCHITECTURE.md` |
| O3 | Real planetary data, supplied with each user's own keys, drives the planet. Missing data is shown as missing, never faked. | Commit `2f164bb`, README "Real data" |
| O4 | A compelling, understandable visualization (3D globe, metrics, events) suitable for demos. | Dashboard, roadmap phase 4 |
| O5 | Every surface communicates that no real neurons are involved and that decoded actions are metaphors. | `ETHICS_AND_LIMITATIONS.md` |

## 4. Users and stakeholders (inferred)

- **The author / developer:** explores the architecture and prepares a future biological deployment.
- **Demo audiences** (public, artistic, scientific): see the globe and the loop, and must not be misled.
- **Future integrators:** would implement the CL1 / Cortical Cloud adapter and the safety gates.

## 5. Non-goals

- Connecting to or stimulating real neurons in this version.
- Claiming learning, cognition, consciousness, sentience, emotion, or a causal neural response.
- Scientific validity of channel-group meanings or decoded actions.
- Multi-user hosting, authentication, or production deployment.

## 6. Guardrails (must always hold)

| ID | Guardrail |
| --- | --- |
| G1 | Physical stimulation stays **off by default**. Intents are recorded with `simulator_non_causal: True`. |
| G2 | The mode is always visible: "CL SDK Simulator Mode" or "Fallback Synthetic Mode". |
| G3 | Strict live mode never substitutes simulated data for real data. |
| G4 | Secrets never leave the backend unmasked. |
| G5 | Any future biological deployment requires safety, ethics, and approval review first. |

## 7. Success signals

- The backend test suite passes without `cl-sdk` and without network access (observed: 44/44).
- `scripts/smoke_test.py` reports ticks greater than 0 and a non-empty history against a running backend.
- The dashboard shows live events from key-free sources out of the box (USGS, EONET, GDACS, ISS).

## 8. Open questions (Unknown)

- Whether the simulator path was exercised with the real `cl-sdk` package.
- Target venue for the public demo or installation.
- Licensing.
