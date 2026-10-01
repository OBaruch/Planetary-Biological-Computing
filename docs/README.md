# Documentation Index

This folder holds two kinds of documentation, kept clearly apart:

| Type | Files | Notes |
| --- | --- | --- |
| **Original** (written together with the code, June 2026) | [ARCHITECTURE.md](ARCHITECTURE.md), [ETHICS_AND_LIMITATIONS.md](ETHICS_AND_LIMITATIONS.md), [ROADMAP.md](ROADMAP.md), [original/README-original.md](original/README-original.md) | Left unchanged. |
| **Added later** (repository documentation pass) | [project-context.md](project-context.md), [code-overview.md](code-overview.md), [possible-improvements.md](possible-improvements.md), [sdlc/](sdlc/) | Describes the original project; does not change it. |

## Suggested reading order

1. [project-context.md](project-context.md): what the project is, where it comes from, and its scope.
2. [ETHICS_AND_LIMITATIONS.md](ETHICS_AND_LIMITATIONS.md): what the system does **not** claim.
3. [code-overview.md](code-overview.md): how the code is organized and how a tick flows.
4. [sdlc/intent.md](sdlc/intent.md) → [sdlc/spec.md](sdlc/spec.md) → [sdlc/plan.md](sdlc/plan.md): intent, requirements with traceability to code and tests, and the delivery plan.
5. [possible-improvements.md](possible-improvements.md): known issues and ideas (none applied).
6. [ROADMAP.md](ROADMAP.md): the author's original future phases.

## Evidence convention

The added documents label statements as follows:

- **Confirmed**: directly supported by a file, the code, the tests, or git history.
- **Inferred**: a reasonable deduction from the repository.
- **Unknown**: not determinable from the repository.
