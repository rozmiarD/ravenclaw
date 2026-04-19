# OPEN_SOURCE_1_0_PLAN.md

## Purpose

This document captures a high-level roadmap for moving Ravenclaw toward `1.0.0` and preparing an eventual public GitHub release.
It is intentionally broad and strategic rather than implementation-heavy.

---

## Overall direction

The recommended direction is:

1. continue shaping Ravenclaw into a stable governance-first runtime,
2. reach a credible `1.0.0` milestone,
3. prepare a public-facing open-source release only after the system is structurally clean and publication boundaries are deliberate.

The goal is not simply to publish code.
The goal is to publish something coherent, trustworthy, and useful.

---

## Phase 1 — reach `0.9.0`

### Objective
Move from active bounded refactor work to a runtime architecture that feels intentionally shaped and maintainable.

### Broad focus
- finish the current runtime/runner cleanup work
- reduce remaining architectural hotspots
- keep contracts and state ownership clear
- maintain strong regression coverage
- keep documentation aligned with reality

### Desired outcome
By `0.9.0`, Ravenclaw should look like a mature runtime architecture rather than an active decomposition project.

---

## Phase 2 — reach `1.0.0`

### Objective
Turn the shaped runtime into a stable production-grade governance runtime.

### Broad focus
- harden policy and control behavior
- validate operator-facing runtime control paths
- improve recovery, restart, and partial-failure handling
- ensure state, artifacts, and reporting are predictable
- strengthen release-quality documentation

### Desired outcome
By `1.0.0`, the system should feel stable, inspectable, and trustworthy under normal operator use.

Current posture after the 2026-04-18 hardening pass:
- operator control semantics have direct regression coverage
- restart/recovery truth has focused regression coverage around stale PID, paused persistence, and stopped-state precedence
- operator-visible source/provenance labels have been tightened in key fallback payloads
- release-quality operator truth docs now exist for these semantics

---

## Phase 3 — prepare open-source release

### Objective
Prepare a public GitHub release in a deliberate way.

### Broad focus
- define what belongs in the public repository
- remove or isolate anything too sensitive, too private, or too environment-specific
- improve public-facing docs and onboarding
- ensure licensing, contribution, conduct, and security reporting surfaces are clear
- present the project as a governance-first research platform, not an uncontrolled offensive tool

Current public-release prep posture:
- a short publication-boundary reference now exists in `references/public-release-boundary.md`
- licensing, conduct, contribution, and security surfaces now exist at the repo root
- the next publication-prep waves should review mixed local artifact areas such as `reports/`, `memory/`, `logs/`, `pending/`, `tmp/`, and `state/` rather than assuming the working tree is publishable as-is

### Desired outcome
The public repository should be understandable, safe to inspect, and aligned with the intended public story of the project.

---

## Publication stance

The recommended default is to publish a serious open-core or public research shell, not necessarily every high-leverage internal capability.

That means:
- public release should maximize clarity, credibility, and long-term value,
- private components may remain private if they are too sensitive, too environment-specific, or strategically premature to release.

---

## Milestone summary

### `0.9.0`
Runtime architecture maturity milestone.

### `1.0.0`
Stable governance-first production milestone.

### public GitHub release
A deliberate open-source release built on top of `1.0.0` readiness, with clear publication boundaries.

---

## Guiding rule

Do not rush public release just because the code works.
Release publicly when the architecture, documentation, safety posture, and publication boundary are all coherent enough to represent Ravenclaw well.
