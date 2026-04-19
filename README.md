# RAVENCLAW

**RAVENCLAW is a governance-first autonomous security research platform for bounded, auditable security operations.**

It is built to explore a simple idea:

> advanced autonomy is only useful when it remains bounded, observable, and accountable.

RAVENCLAW is not designed as unconstrained offensive automation. It is a research-stage system for policy-driven security workflows where operator authority, runtime controls, and evidence quality matter as much as execution speed.

---

## What RAVENCLAW is

RAVENCLAW is an experimental multi-role system for running security workflows under explicit governance.

It combines:

- role-separated agent reasoning,
- deterministic planning and control surfaces,
- runtime policy enforcement,
- constrained execution,
- evidence-based qualification,
- operator-facing observability and recovery.

The goal is not maximum automation.

The goal is **reliable autonomy under governance**.

---

## Why it exists

Most autonomous security tooling tends to fail in one of two ways:

- it is too rigid to stay useful in dynamic environments, or
- it is too unconstrained to be trusted in real operations.

RAVENCLAW explores a different model: intelligent components may propose, prioritize, and adapt, but execution must remain policy-bound, inspectable, and recoverable.

The project is built around the belief that security autonomy should not be judged only by how much it can do, but by how safely, clearly, and accountably it behaves when conditions become messy.

---

## Core design principles

### Governed intelligence
Models may plan, rank, reinterpret, and optimize, but they must not self-authorize beyond policy constraints.

### Role-isolated cognition
Planning, gating, execution, and interpretation are separated to reduce single-point cognitive failure and limit authority concentration.

### Policy as a runtime primitive
Scope rules, tool restrictions, aggression limits, and credential controls are enforced in live execution paths, not treated as documentation-only guidance.

### Deterministic control plane
Critical state transitions should be explicit, inspectable, and recoverable.

### Evidence-centric operations
System outputs should favor traceable artifacts, qualification logic, and confirmation flow over unverifiable narrative.

### Human-in-command
Elevated actions remain under operator authority. Human responsibility is not replaced by system autonomy.

---

## High-level flow

At a high level, RAVENCLAW follows a governed security workflow like this:

`scope input -> planning -> policy review/gating -> constrained execution -> artifact analysis -> qualification/confirmation -> operator visibility and control`

This flow is intentionally layered so that no single component both invents and unrestrictedly authorizes high-impact actions.

---

## System architecture

RAVENCLAW uses a multi-role architecture with separated responsibilities.

### Planner
Transforms campaign scope and operator input into deterministic campaign blueprints, planning hints, and runtime task seeds.

### Orchestrator
Manages campaign lifecycle, queue state, retries, reprioritization, and runtime sequencing.

### Auditor / Policy Gate
Applies scope checks, tool constraints, aggression rules, credential requirements, and approval logic before execution.

### Execution Engine
Runs allowed commands under whitelist and contract constraints, while preserving execution telemetry and output artifacts.

### Analysis
Interprets execution artifacts into structured findings, signals, and operator-usable summaries.

### Qualification / Confirmation Logic
Evaluates whether observed signals meet evidence thresholds for weak, probable, or confirmed outcomes.

### Light Summary Layer
Produces concise operator-facing summaries for situational awareness without replacing underlying artifacts.

This separation is deliberate. In systems like this, collapsing planning, authorization, and execution into one layer is how you get fast nonsense with a confidence score attached.

---

## Governance and safety boundaries

RAVENCLAW is designed around explicit runtime boundaries, including:

- scope-driven host and target validation,
- runtime policy gates before execution,
- whitelist and contract-constrained tool invocation,
- aggression controls and override semantics,
- credential policy enforcement with operator approval surfaces,
- evidence qualification and confirmation flow,
- runtime observability, persistence, and recoverability.

The project is intended for authorized security research and controlled environments. It does not remove legal, ethical, or organizational accountability.

## Release roadmap

Version milestones and their intended meaning are documented in `VERSION_ROADMAP.md`.
Use that file as the canonical guide for deciding when bounded refactor work stays on the current line versus when the project should move to a new milestone release.

Current release posture:
- `0.9.0` marked the runtime-architecture maturity checkpoint
- `1.0.0` is now the active production-grade governance-runtime milestone
- the `1.0.0` bar is dependable operator control semantics, trustworthy restart/recovery behavior, clearer operator-visible provenance, and release-quality control-plane documentation

---

## What RAVENCLAW is not

RAVENCLAW is **not**:

- an unconstrained offensive automation platform,
- a black-box “AI hacker,”
- a replacement for human judgment,
- a guarantee of security outcomes,
- a finished consumer product,
- a claim that autonomy alone improves security work.

Its value, if it has any, comes from disciplined control and reliable operator-facing behavior, not from autonomy theater.

---

## Research orientation

RAVENCLAW is an active systems research effort focused on:

- governance-aware autonomy,
- policy-grounded orchestration,
- bounded behavior under uncertainty,
- evidence-centric vulnerability workflows,
- operator control and recoverability,
- practical human–AI command structures for security operations.

The central question is not just:

> can autonomy act?

It is:

> can autonomy act accountably under real operational constraints?

---

## Runtime path and control plane

Current production execution path:

1. `logdash/app.py` + `logdash/api_*` + `logdash/services.py` — operator control plane and shared state/service projection layer
2. `engine/auto_campaign.py` / `engine/auto_campaign_runner.py` + adjacent `engine/runtime_*` modules — long-lived campaign orchestration, queueing, session flow, runtime control, and persistence
3. `engine/runtime_plan_service.py` + `engine/runtime_task_schema.py` — canonical planner→runtime task shaping and runtime-plan persistence
4. `engine/run_pipeline.py` + extracted `engine/pipeline_*` stage modules — governed single-task pipeline
5. `engine/executor.py` — final command construction + execution from approved artifacts
6. `engine/plan_campaign.py` + `engine/planer/*` — deterministic planning and blueprint generation

Current runtime characteristics worth knowing:
- planner/runtime semantic fields are no longer only advisory metadata; bounded planner-governed admission now exists for activation/gating/depth/cluster/surface-role semantics
- Logdash `Start` / `Pause` / `Stop` are real runtime controls, not UI-only state toggles
- Logdash control/recovery semantics are being hardened explicitly around truthful start/resume/pause/stop behavior, stale PID cleanup, paused persistence, and selected-campaign fallback provenance
- evaluation/replay outputs are first-class archived artifacts rather than ad hoc report extras
- centralized path contracts in `engine/paths.py` define the canonical runtime-artifact locations under `reports/`

Supporting documentation:
- `ARCHITECTURE.md` — current module map, runtime flow, contracts, maturity overview
- `STATE_FILES.md` — shared state and artifact files used by runtime and UI
- `engine/RUNTIME_MANIFEST.md` — canonical production-path reference

---

## Repository guide

The exact layout evolves, but the repository is organized around a few core areas:

### `engine/`
Core runtime logic: planning flow, runtime-plan generation, orchestration, policy gates, execution paths, analysis, qualification, evaluation/replay, contracts, and runtime services.

### `logdash/`
Operator-facing dashboard and control plane for campaign state, findings, controls, logs, plan validation, approval flow, runtime visibility, evaluation summaries, and shared state/service projections.

### `reports/`
Mixed persisted runtime artifacts with clearer internal ownership:
- durable planner history in `reports/campaign_registry/`
- live local control-plane/runtime state in `reports/.*.json`
- canonical generated runtime state in `reports/state/`
- canonical generated caches in `reports/cache/`
- rolling snapshots, latest outputs, and archived summaries under `reports/latest/`, `reports/archive/`, and related files

Treat `campaign_registry/` differently from the rest of `reports/`: it is durable planning history, while most dotfiles and latest/snapshot outputs are local runtime artifacts.

Current path-contract note:
- canonical generated runtime-artifact paths live under `reports/` and are defined via `engine/paths.py`
- primary examples are `reports/state/public_targets_plan.json` and `reports/cache/context_summary.json`
- legacy engine-local mirrors may still exist temporarily for compatibility during the transition, but they are no longer the preferred source of truth
- use `references/runtime-artifact-ownership.md` as the short ownership guide when deciding where generated runtime state belongs
- use `references/logdash-operator-truth-contracts.md` as the short operator-facing guide for control semantics, recovery truth, and source-label interpretation

### Configuration and policy files
Files such as campaign definitions, whitelist/policy settings, scope inputs, and related runtime controls define what the system is allowed to do and how it should behave.

If you are trying to understand the system, start with the runtime flow and policy boundaries before diving into UI details.

---

## Component maturity

RAVENCLAW is a live research platform. Different parts of the repository have different maturity levels.

| Component | Status |
|---|---|
| Planner / blueprint registry | advanced |
| Policy core / whitelist / scope gates | advanced |
| Governed single-task pipeline | advanced |
| Planner→runtime contract + runtime-plan shaping | advanced experimental |
| Evaluation / replay / effectiveness exports | advanced experimental |
| Logdash control plane | advanced experimental |
| Auto-campaign adaptation logic | experimental |
| Qualification / confirmation semantics | experimental |
| Shared state-file contracts | improving / partially formalized |

This means the repository contains real working runtime paths, but also ongoing refactors and evolving semantics.

---

## Current focus areas

Current development is centered on:

- keeping planner/runtime/control-plane truth aligned after the recent semantic hardening waves,
- reducing remaining state-ownership and compatibility seams,
- richer evidence qualification and confirmation semantics,
- improved operator visibility for activation, validation, recovery, and evaluation,
- tighter observability for runtime state and governance decisions,
- more reliable replayability and auditability of campaign behavior.

Near-term milestone framing:
- the repo has crossed the `0.9.0` architecture-maturity checkpoint and the `1.0.0` hardening line has been completed in bounded waves
- remaining work after `1.0.0` should default to selective confidence expansion, ergonomics, compatibility cleanup, and public-release preparation rather than rescue work

---

## Repository status and maturity

This repository reflects an **active experimental platform**.

Expect ongoing changes to architecture, prompts, policies, execution flow, and operator interfaces as the system is refined. Current behavior should be treated as research-stage implementation, not as a blanket production guarantee.

Some parts may be stable enough for repeated internal use; that is not the same thing as broad production readiness. The universe loves edge cases, and security tooling attracts them like a magnet.

---

## Repository bootstrap and local setup

Path assumptions should be treated as env-overridable.
The canonical workspace can be set with:

```bash
export RAVENCLAW_WORKSPACE=/path/to/workspace
```

Current packaging/bootstrap facts:
- root `pyproject.toml` exists
- package name is `ravenclaw`
- current repository version is `1.0.0`
- minimum Python is `>=3.11`

Minimal test/developer dependencies used by CI today are:
- `pytest`
- `Flask`
- `PyYAML`

Repository scaffolding currently includes:
- `pyproject.toml`
- `.editorconfig`
- `.github/workflows/pytest.yml`
- `LICENSE`
- `CODE_OF_CONDUCT.md`
- `SECURITY.md`
- `CONTRIBUTING.md`

Public-release note:
- treat this workspace as a mixed internal working tree, not an automatically publishable snapshot
- use `references/public-release-boundary.md` as the short guide for high-level publication boundaries
- use `references/public-release-review-matrix.md` as the bounded review matrix for deciding what should be public, reviewed, excluded, or replaced with examples in a future public snapshot
- use `references/public-snapshot-plan.md` as the concrete keep/exclude/replace plan for assembling a future public repository snapshot
- use `scripts/assemble_public_snapshot.sh` to build a bounded public-snapshot scaffold instead of trying to publish the live workspace directly

## Contribution and review

Contributions are most useful when they improve one or more of the following:

- governance correctness,
- runtime safety and control integrity,
- evidence quality and reproducibility,
- operator trust and observability,
- failure recoverability,
- policy-to-runtime consistency.

When proposing major changes, include the expected governance impact, runtime implications, likely failure modes, and any shared state or contract changes.

---

## Suggested reading order

1. `README.md`
2. `ARCHITECTURE.md`
3. `STATE_FILES.md`
4. `whitelist.yaml`
5. `policy.yaml`
6. `engine/run_pipeline.py`
7. `engine/executor.py`
8. `engine/runtime_plan_service.py`
9. `engine/auto_campaign_runner.py`
10. `logdash/app.py`

---

## Summary

RAVENCLAW is best understood as a **governance-first autonomous security operations substrate**:

- adaptive, but bounded,
- inspectable, not opaque,
- evidence-driven, not purely narrative,
- operator-governed, not self-authorizing.

It does not aim to prove that autonomy should replace control.

It aims to prove that autonomy can remain **useful without becoming ungovernable**.
