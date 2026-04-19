# VERSION_ROADMAP.md

## Purpose

This file defines the recommended versioning roadmap for Ravenclaw from the current `0.8.x` line through `2.0.0`.
It is intended to keep release numbers tied to meaningful architectural and operational milestones rather than incidental commit volume.

---

## Versioning principles

- Patch and minor increments inside an active line should reflect bounded implementation progress, stabilization, hardening, and operator-visible improvements.
- Milestone versions should represent a real step-change in architecture maturity, operational trust, or platform capability.
- Internal refactor alone should not force a milestone bump unless it materially changes maintainability, reliability, or operator control.
- Governance, operator control, and runtime inspectability matter as much as raw automation capability.

---

## `0.8.x` — bounded refactor and stabilization line

### Intent
Complete the current runner-thinning and runtime-shaping work without overstating the maturity of the platform.

### Typical changes
- bounded extraction waves in `engine/auto_campaign_runner.py`
- test expansion and regression validation in `engine/tests`
- contract cleanup and runtime seam clarification
- artifact/state ownership cleanup
- changelog, reports, and implementation-plan hygiene
- no major operator-facing semantic shift

### Exit criteria
- the main runner is substantially thinned and no longer the primary architectural debt hotspot
- remaining seams are manageable and explicit
- regression coverage is consistently green
- documentation and operational closeouts track the work accurately

---

## `0.9.0` — stabilization and runtime architecture maturity milestone

### Intent
Mark the point where the runtime becomes architecturally defensible, materially more inspectable, and truthfully documented, even if the whole platform is not yet ready to be called fully production-grade.

### Required characteristics
- Phase B3 / runner-thinning work is effectively complete
- orchestration, policy, execution, persistence, and reporting boundaries are clearer and more durable
- planner to runtime to execution handoff contracts are stable and documented
- runtime artifact ownership is coherent and inspectable
- Logdash and runtime control flow reflect the architecture cleanly
- docs and operator-visible truth surfaces are aligned closely enough with live runtime behavior to avoid major overclaiming

### What should be true
- `engine/auto_campaign_runner.py` is no longer the main structural liability
- the codebase feels intentionally shaped rather than actively being decompressed from historical monolith form
- remaining debt is mostly bounded downstream cleanup, compatibility reduction, and clarity work rather than rescue refactoring
- full engine regression remains green

### What `0.9.0` does **not** need to imply
- that every legacy compatibility path is already removed
- that every consumer reads one perfectly singular truth surface
- that all transition-era fallback behavior is gone

The honest bar is lower and stronger:
- architecture stabilized
- truth surfaces materially improved
- remaining debt clearly bounded

---

## `1.0.0` — production-grade governance runtime

### Intent
Declare the first release that can honestly be treated as a stable production-grade Ravenclaw runtime.

### Required characteristics
- major architectural risk in the orchestration path is retired
- governance and policy gates are explicit, enforced, and inspectable
- planner to runtime to execution flow is stable under normal operator use
- owner approval, stop-loss, pause/resume, and runtime control behavior are dependable
- observability, replayability, and core operator documentation are solid
- restart, resume, and partial-failure behavior are trustworthy enough for real operational usage

### What should be true
- operators can use the system without feeling they are standing on top of an unfinished refactor
- state files and runtime artifacts behave predictably
- safety/control maturity matches automation maturity

---

## `1.1.x` to `1.4.x` — hardening and operator ergonomics

### `1.1.x`
- execution-engine hardening
- stronger policy and admission explanations
- tighter evaluation and replay contracts
- reduced documentation drift

### `1.2.x`
- Logdash/operator UX improvements
- stronger diagnostics and runtime introspection
- clearer campaign controls and state displays
- legacy state-path cleanup

### `1.3.x`
- improved planner/runtime semantic preservation
- more deterministic runtime-plan regeneration
- clearer visibility into host-state learning and queue scoring

### `1.4.x`
- reporting and export improvements
- stronger audit trail visibility
- better artifact explainability
- improved maintenance and hygiene automation

---

## `1.5.0` — adaptive platform milestone

### Intent
Mark the point where Ravenclaw is not only stable, but meaningfully adaptive in how it evaluates, learns, and sequences work.

### Required characteristics
- stronger runtime learning loops
- better decision-quality feedback paths
- more capable followup and qualification orchestration
- better economics and effectiveness visibility

### What should be true
- the system is visibly better at adapting campaign behavior based on prior runtime results
- adaptation is still governance-bound and operator-inspectable

---

## `1.6.x` to `1.9.x` — scale, trust, and operational depth

### Intent
Expand reliability, visibility, and operational trust at larger runtime scope.

### Typical changes
- stronger resilience for longer-running campaigns
- better support across target classes and surface-role variants
- richer governance telemetry
- stronger recovery and operator audit tooling
- possible external control/API surfaces if they preserve the same governance model

---

## `2.0.0` — second-generation Ravenclaw platform

### Intent
Declare a second-generation platform release where the architecture, governance model, control plane, and adaptive runtime form a coherent whole.

### Required characteristics
- modular runtime with minimal legacy drag
- clean planner/runtime/execution contracts across the whole stack
- strong operator inspectability and auditability
- governance enforced in practice across control flow, not just documented in policy text
- evaluation, replay, and learning are native platform capabilities
- Logdash/control plane operates as a first-class operational surface
- artifact ownership and state-path semantics are clear, durable, and low-friction

### What should be true
- the platform feels intentionally designed end-to-end rather than historically accumulated
- operator trust comes from evidence, control, and clarity, not just passing tests
- the system can evolve without reopening the same foundational architectural debt

---

## Short form summary

- `0.8.x` = bounded refactor and stabilization
- `0.9.0` = runtime architecture maturity
- `1.0.0` = production-grade governance runtime
- `1.1.x` to `1.4.x` = hardening and operator ergonomics
- `1.5.0` = adaptive platform milestone
- `1.6.x` to `1.9.x` = scale, trust, and operational depth
- `2.0.0` = second-generation Ravenclaw platform
