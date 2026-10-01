# Project Context

> This document was added during a later documentation pass. It describes the original project and does not change it.
> Statements are labelled **Confirmed**, **Inferred**, or **Unknown** (see [README.md](README.md#evidence-convention)).

## Classification

**Project origin:** Personal Project, specifically a **Proof of Concept / Technical Experiment** with an artistic component.

| Signal | Source | Level |
| --- | --- | --- |
| Described as "a local MVP for a scientific/artistic technology demo" | Original README | Confirmed |
| "The project is educational, experimental, artistic, and technical." | `docs/ETHICS_AND_LIMITATIONS.md` | Confirmed |
| No university, course, professor, assignment, or grading rubric is mentioned in any file | Whole repository | Confirmed (absence) |
| Developed by a single author outside any institutional context | Git history (one author); no institutional references | Inferred |
| Built with a specific future hardware target in mind (Cortical Labs CL1 / Cortical Cloud) | README, `ROADMAP.md`, adapter code | Confirmed |

The repository gives no evidence that this is coursework, so it is **not** classified as an academic project.

## Timeline (from git history)

| Date | Commit | Content | Level |
| --- | --- | --- | --- |
| 2026-06-16 | `fb46f78` *Build GAIA-1 Earth Dreams MVP* | Backend pipeline (encoder, decoder, adapters, simulation, runner), API, React dashboard, first tests | Confirmed |
| 2026-06-16 | `3869e08` *Harden GAIA-1 simulation MVP* | Runner lifecycle, status/config/session endpoints, scripts, original `docs/` | Confirmed |
| 2026-06-18 | `2f164bb` *Add per-user real-data sources with Settings panel* | Source catalog, credential store, 10 connectors, strict live mode, 3D globe | Confirmed |
| 2026-06-18 | `01bc1b2` Merge of PR #1 (`feat/real-data-sources`) | | Confirmed |

The history shows a short, intense build of about three days. A synthetic MVP came first, then hardening, then a real-data layer.

## Motivation

- **Confirmed.** Explore a closed loop between planetary data and neural activity: "Live planetary signals encoded into simulated neural activity, decoded back into a living digital Earth."
- **Confirmed.** Be "neuron-ready": the same architecture should later drive real biological neurons via CL1 / Cortical Cloud through a new `NeuralAdapter`.
- **Inferred.** The presentation goal is a public demo or art installation. Evidence: roadmap phases "Public Visualization" and "Paper / Demo / Installation", the presenter-style UI copy, and the mood labels.

## Scope

**In scope (implemented):**

- A real-time loop at 1–30 ticks per second, with start, stop, and reset.
- The CL SDK Simulator adapter and a deterministic fallback adapter.
- A planet encoder, spike decoder, and planet simulation.
- Two data modes: strict `live` (real sources only) and `demo` (synthetic signals plus injectable events).
- Ten real-data connectors. Credentials are configured per user from the UI, stored locally, and masked over the API.
- A REST + WebSocket API and a React/Three.js dashboard with a 3D globe and event markers.
- JSONL session logging and a pytest suite.

**Explicitly out of scope** (stated by the author):

- Any connection to real neurons.
- Any claim of biological learning, consciousness, sentience, thought, emotion, or causal response to stimulation.
- Physical stimulation. It is disabled by default (`GAIA_ENABLE_CL_STIMULATION=false`) and described as "future-facing".

## Ethical framing

The author built an explicit ethics posture into the product:

- a permanent ethics banner in the UI;
- an `ETHICS_TEXT` returned by the API root;
- `metaphor_notice` on every decoded action;
- a `simulator_non_causal: True` flag on every stimulation intent;
- the status string "Fallback Synthetic Mode" when the CL SDK is absent.

See [ETHICS_AND_LIMITATIONS.md](ETHICS_AND_LIMITATIONS.md).

## What could not be determined

| Question | Status |
| --- | --- |
| Whether the project was ever shown publicly or deployed | Unknown |
| Whether it was run against the actual `cl-sdk` package (vs. fallback only) | Unknown. The code targets the official API surface, but the repository contains no recordings or logs. |
| Whether the CL SDK API calls (`create_data_stream`, `record`, `StimDesign`, …) match the current SDK release | Unknown. The calls are wrapped in `try/except` with fallbacks, which suggests the author expected API variations. |
| Licensing intent | Unknown. The repository has no LICENSE file. |
| Funding, partners, or affiliation with Cortical Labs | Unknown. Nothing in the repository indicates an affiliation. |

## Repository artifacts inventory

| Category | Present? | Notes |
| --- | --- | --- |
| Source code | Yes | `backend/` (Python), `frontend/` (TypeScript/React) |
| Tests | Yes | `backend/tests/` (44 tests) |
| Scripts | Yes | `scripts/` |
| Original Markdown docs | Yes | README, `docs/ARCHITECTURE.md`, `docs/ETHICS_AND_LIMITATIONS.md`, `docs/ROADMAP.md`, `frontend/public/textures/earth/README.md` |
| PDF / Word / PowerPoint | No | |
| Images / diagrams | No (only a Mermaid diagram inside the README) | |
| Datasets / historical outputs | No | `backend/data/*` contains only `.gitkeep` placeholders |
