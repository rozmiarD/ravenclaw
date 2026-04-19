# Runtime Manifest (production path)

This file is the shortest canonical reference for the currently live Ravenclaw runtime path.
It is intentionally narrower than `ARCHITECTURE.md`: it names the production path, the key supporting seams, and the path/state contracts that new runtime code must respect.

## Active production execution path

1. `logdash/app.py` + `logdash/api_*` + `logdash/services.py`
   - operator control plane
   - planner/runtime/evaluation API surfaces
   - shared state/service projection layer for Logdash

2. `engine/auto_campaign.py` + `engine/auto_campaign_runner.py` + adjacent `engine/runtime_*` modules
   - long-lived campaign loop
   - session/loop control
   - runtime gating, queueing, host-state learning, persistence

3. `engine/runtime_plan_service.py` + `engine/runtime_task_schema.py`
   - blueprint-to-runtime transformation
   - runtime-plan generation and metadata persistence
   - canonical planner/runtime task normalization

4. `engine/run_pipeline.py` + extracted `engine/pipeline_*` stage modules
   - governed single-task path
   - BRAIN -> AUDITOR -> EXECUTION ENGINE -> ANALYSIS -> LIGHT

5. `engine/executor.py`
   - final command construction + execution
   - scope/policy/whitelist constrained invocation only

6. `engine/plan_campaign.py` + `engine/planer/*`
   - deterministic planning and blueprint generation
   - durable planner history under `reports/campaign_registry/`

## Canonical supporting contracts

### Path contracts
Use `engine/paths.py` for canonical generated-artifact paths.
Current preferred locations include:
- runtime plan: `reports/state/public_targets_plan.json`
- pipeline context cache: `reports/cache/context_summary.json`
- live runtime snapshot: `reports/.runtime_snapshot.json`
- runtime-plan metadata: `reports/.runtime_plan.meta.json`

Legacy compatibility mirrors may still exist under `engine/`, but they are not the preferred source of truth.
Use `references/runtime-artifact-ownership.md` as the short ownership guide for canonical-versus-legacy artifact paths.

### Planner/runtime contract
The current production runtime preserves planner-owned semantics into runtime tasks and uses bounded runtime enforcement for fields such as:
- `expected_depth`
- `activation_phase`
- `activation_mode`
- `conditional_gate`
- `surface_role`
- `target_cluster`

These fields are no longer documentation-only hints; they materially affect runtime admission/execution behavior in the current system.

### Control-plane rule
Logdash should prefer shared helper/service/state layers over endpoint-local file logic when projecting runtime truth.
Recent cleanup centralized selected-campaign snapshot filtering/projection rather than duplicating it across multiple APIs.

## Non-production / archived
- `engine/legacy/*` — outdated/retained for history
- compatibility mirrors under `engine/` for paths now canonicalized under `reports/`

## Rules
- new runtime code must be wired into this path explicitly
- new shared state should come with clear ownership and documented path contracts
- legacy code is not executed by default unless explicitly reintroduced into the production path
