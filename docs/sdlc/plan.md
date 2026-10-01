# Plan: GAIA-1: Earth Dreams

> **Document type:** Plan (the *how* and *when*). Implements [spec.md](spec.md), which serves [intent.md](intent.md).
> **Status:** *Reconstructed.* §2 records how the original project was actually delivered (from git history). §3 documents the repository documentation pass. §4 restates the author's original roadmap. No code changes are planned in this document.

## 1. Approach

The project followed an incremental, vertical-slice approach:

1. **Make the loop exist end-to-end**, with synthetic data and a fallback adapter so it always runs.
2. **Harden** lifecycle, observability, and developer tooling.
3. **Replace synthetic inputs with real data** behind a declarative catalog, without breaking the demo path.

The neural hardware stays isolated behind `NeuralAdapter`. Biological deployment is deferred until safety gates exist (intent guardrail G5).

## 2. Delivery history (as built)

| Phase | Commit / date | Delivered | Spec coverage |
| --- | --- | --- | --- |
| **P0: MVP loop** | `fb46f78`, 2026-06-16 | Settings, models, encoder, decoder, CL SDK + fallback adapters, planet data (mock), planet simulation, runner, session logger, REST + WS, React dashboard, first tests | FR-01, FR-10, FR-12, FR-13, FR-20 … FR-26, FR-40 … FR-42, FR-55, NFR-01 |
| **P1: Hardening** | `3869e08`, 2026-06-16 | Idempotent controls, status/config/sessions endpoints, `last_error`, tick-rate and latency metrics, `check_env` / `run_backend` / `smoke_test` scripts, original `docs/` (architecture, ethics, roadmap), exponential-backoff reconnect + REST polling fallback in the UI | FR-02 … FR-05, FR-54, NFR-05 |
| **P2: Real-data sources** | `2f164bb`, merged as PR #1 (`01bc1b2`), 2026-06-18 | Source catalog (10), credential store, registry, signal service, 5 signal + 5 geo connectors, strict `live` vs `demo` mode, provenance, Settings panel, 3D `RealTimeEarthGlobe`, geo/registry/credential/signal/API tests | FR-11, FR-30 … FR-37, FR-50 … FR-53, FR-56, NFR-02 … NFR-04 |

## 3. Workstream: repository documentation pass (this change)

**Goal:** turn the repository into a clear, navigable, portfolio-ready record *without modifying the original implementation*.

### 3.1 Rules

- **R1.** Do not edit, move, reformat, or "fix" any source, test, script, or config file. The code layout stays as is, because `config.py`, the `Makefile`, the scripts, and the tests resolve paths relative to the repository root.
- **R2.** Preserve the original documents. `docs/ARCHITECTURE.md`, `ETHICS_AND_LIMITATIONS.md`, and `ROADMAP.md` are untouched, and the original README is kept verbatim in `docs/original/`.
- **R3.** Separate *original* from *added* documentation, and label claims as Confirmed, Inferred, or Unknown.
- **R4.** Record defects and ideas in `possible-improvements.md` only. Never apply them as part of this pass.
- **R5.** Add no infrastructure (CI, Docker, linters, …) that the project did not have.

### 3.2 Tasks

| # | Task | Output | Status |
| --- | --- | --- | --- |
| T1 | Inventory every file and classify it (code, tests, scripts, docs, data placeholders) | [project-context.md](../project-context.md) §inventory | Done |
| T2 | Reconstruct origin and timeline from the docs and git history | [project-context.md](../project-context.md) | Done |
| T3 | Read every backend module and the main frontend modules; map the tick pipeline | [code-overview.md](../code-overview.md) | Done |
| T4 | Verify behavior by running the suite and the build | 44 tests passed; frontend built after `npm install`; `npm ci` failed (lockfile drift) | Done |
| T5 | Reverse-engineer intent → spec → plan with traceability to code and tests | `docs/sdlc/*` | Done |
| T6 | Record findings without fixing them | [possible-improvements.md](../possible-improvements.md) | Done |
| T7 | Snapshot the original README; write the new portfolio README and docs index | `README.md`, `docs/README.md`, `docs/original/` | Done |
| T8 | Check that no file outside documentation changed | `git diff --stat main -- backend frontend scripts Makefile .env.example .gitignore` is empty | Done |

### 3.3 Verification commands

```bash
# Original code untouched (should print nothing)
git diff --stat main -- backend frontend scripts Makefile .env.example .gitignore

# Original README preserved byte-for-byte
git show main:README.md | cmp - docs/original/README-original.md

# Behavior unchanged
pytest backend/tests
```

## 4. Future phases (from the original roadmap)

Restated from [ROADMAP.md](../ROADMAP.md). None of these phases has been started.

| Phase | Scope | Entry condition (inferred) |
| --- | --- | --- |
| 1: Robust local simulator | Further runner hardening, expanded events and controls | Mostly delivered by P1/P2 |
| 2: Recording replay | Replay real or shared recordings; JSONL/CSV comparison; charts | Access to recordings |
| 3: Controlled Cortical Cloud session | New CL1/Cortical Cloud adapter; reviewed stimulation plans; safety gates, rate limits, manual approval | Hardware/cloud access **and** ethics review (G5) |
| 4: Public visualization | Deployable demo, presenter mode, video export | Authentication and hosting decisions (see S2) |
| 5: Open dataset and analysis | Synthetic session datasets, schemas, notebooks, benchmarks | Stable frame schema |
| 6: Paper / demo / installation | Write-up, installation-grade visuals, documented ethical boundaries | Phases 2–5 |

## 5. Risks

| Risk | Mitigation already present |
| --- | --- |
| The demo is mistaken for real neural computation | Ethics banner, mode labels, `metaphor_notice`, `simulator_non_causal` |
| External APIs fail or change | Defensive connectors, slow polling, "unsourced" fields shown as disabled |
| CL SDK API differences | `TypeError` fallbacks, `try/except` around optional SDK features |
| Key leakage | Gitignored store, masked responses, write-only secrets |
