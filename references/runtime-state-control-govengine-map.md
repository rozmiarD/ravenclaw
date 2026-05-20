# Runtime State and Control GovEngine Map

This note is the 0.11 planning map for projecting Ravenclaw runtime state and
Logdash control semantics onto GovEngine-compatible contracts.

It is not an implementation claim. Ravenclaw still owns local state storage,
Logdash behavior, campaign UX, and security-runtime semantics. GovEngine 0.2
currently provides generic governance context, transition decisions, execution
gate inputs, runner receipts, artifact state indexes, and controlled-execution
dry-run helpers. It does not yet own Ravenclaw's runtime persistence, queues,
Logdash UI state, or campaign lifecycle.

## Current validation baseline

Before this map was written, these gates passed in a clean validation virtualenv:

- `python scripts/validate_public_install.py --dev`
- `python scripts/run_security_contract_validation.py --structural-only --include-pytest`
- `python -m pytest -q engine/tests/test_runtime_loop_control.py engine/tests/test_runtime_plan_control.py engine/tests/test_runtime_override_control.py engine/tests/test_runtime_runner_controls.py engine/tests/test_runtime_session_state.py engine/tests/test_runtime_runner_session_state_builders.py tests/test_logdash_control_paths.py tests/test_logdash_services_state_view.py`

The installed package boundary was `govengine==0.2.0` and
`sclite-core==0.5.1`.

## Ownership rules

- Ravenclaw owns state files under `reports/`, local process state, selected
  campaign state, queue snapshots, host learning, runtime snapshots, and Logdash
  control endpoints.
- GovEngine should own only reusable neutral shapes once they are proven useful:
  run state, orchestrator state, queue snapshots, runtime snapshots, control
  actions, and transition decisions.
- SCLite remains the lifecycle/proof/review validation layer.
- No Logdash UI behavior, live subprocess ownership, local paths, private state,
  or public snapshot machinery moves into GovEngine.

## State file map

| Ravenclaw source | Current owner | 0.11 projected shape | GovEngine 0.2 fit | Next action |
| --- | --- | --- | --- | --- |
| `reports/.auto_campaign.state.json` | `engine/runtime_campaign_state.py`, runtime loop, Logdash control | `GovRunState` | Partial via `TransitionDecision`; no dedicated run-state model yet | Add Ravenclaw adapter/test first; consider GovEngine 0.3 model only after field parity is clear |
| `reports/.orchestrator.state.json` | `engine/runtime_campaign_state.py`, Logdash selected-campaign state | `GovOrchestratorState` | Partial via `GovernanceContext.metadata`; no canonical orchestrator-state model | Keep selected-campaign persistence Ravenclaw-owned; define neutral projection fields |
| `reports/.auto_campaign.queues.json` | `engine/auto_campaign_state.py`, `logdash/services.py` | `GovQueueSnapshot` | Gap; GovEngine 0.2 has no queue snapshot type | Map lane/count/preview semantics in Ravenclaw before proposing generic GovEngine queue fields |
| `reports/.runtime_snapshot.json` | `engine/auto_campaign_state.py`, `logdash/services.py` | `GovRuntimeSnapshot` | Partial through `ArtifactStateIndex` for governed artifact state only | Keep campaign/host/security telemetry Ravenclaw-owned; project only neutral status/queue/control summary |
| `reports/.runtime_plan.meta.json` | `engine/runtime_plan_service.py` | `GovPlanState` or runtime snapshot sub-block | Gap; current GovEngine task/planning contract is not the owner of Ravenclaw plan metadata | Wait for 0.12 task-contract mapping before extracting |
| `reports/.campaign.settings.json` | Logdash/runtime campaign settings | Host policy/profile settings | Not a GovEngine state model | Keep in Ravenclaw; pass selected booleans into GovEngine gate/context only when needed |
| `reports/.host_state.json` and `reports/learning_store.json` | Ravenclaw runtime learning and host heuristics | Security profile telemetry | Not a GovEngine state model | Keep in Ravenclaw security profile; do not extract generic state prematurely |
| `reports/state/public_targets_plan.json` | `engine/runtime_plan_service.py` | Task-plan projection | Deferred to 0.12 | Keep canonical path handling through `engine/paths.py` |

## Control action map

| Logdash/runtime action | Current behavior | 0.11 GovEngine-compatible projection | Notes |
| --- | --- | --- | --- |
| `start` | Validates selected runtime plan, spawns runtime when not alive, persists running state | `TransitionDecision(status="allowed", from_state="idle", to_state="running")` plus context metadata | Spawning remains Ravenclaw-owned |
| `pause` | Requires live runtime, writes paused control state, runtime loop polls and blocks | `TransitionDecision(status="allowed", to_state="paused")` | Pause is control evidence, not a GovEngine scheduler |
| `resume` | Clears paused state or reports existing live runtime as resumed | `TransitionDecision(status="allowed", from_state="paused", to_state="running")` | Preserve no-spawn resume semantics for already-live runtime |
| `stop` | Sets stopped state and terminates live runtime when present; clean stop allowed without live PID | `TransitionDecision(status="allowed", to_state="stopped")` | Termination remains Ravenclaw host authority |
| `cancel` / archive-style cleanup | Removes or archives local generated state depending on endpoint | `TransitionDecision(status="allowed", to_state="cancelled")` when lifecycle-backed | Must not erase durable planner history |
| `replan` / activate blueprint | Resets selected campaign to idle and regenerates/activates runtime plan | `TransitionDecision(status="requires_replan", to_state="idle")` | Planning semantics defer to 0.12 task-contract work |
| cooldown / skip / gate block | Runtime loop records skip/gate/cooldown summaries and host counters | `TransitionDecision(status="blocked" or "degraded", reason_code=...)` | Generic reason codes may belong in GovEngine 0.3 if repeated across profiles |

## First implementation slice

The smallest useful 0.11 code change is a Ravenclaw-owned projection helper with
focused tests:

1. Convert normalized `.auto_campaign.state.json`, selected campaign metadata,
   queue snapshot, and runtime snapshot summary into a public-safe dictionary
   shaped like `gov_run_state`, `gov_orchestrator_state`,
   `gov_queue_snapshot`, and `gov_runtime_snapshot`.
2. Convert Logdash control actions into `govengine.core.TransitionDecision`
   dictionaries without changing endpoint behavior.
3. Test parity against existing Logdash control behavior and runtime snapshot
   fields.

Stop if the projection requires moving Logdash behavior, live process control,
host-learning internals, or local state persistence into GovEngine.

## GovEngine 0.3 candidates

Only promote a shape into GovEngine after the Ravenclaw projection proves stable:

- `GovRunState`: neutral lifecycle state, pid/process presence, paused/stopped
  flags, selected run/campaign id, updated timestamp.
- `GovOrchestratorState`: selected work id, active plan id/hash, lifecycle
  marker, updated timestamp.
- `GovQueueSnapshot`: lanes, counts, preview items, saved timestamp, redaction
  boundary.
- `GovRuntimeSnapshot`: run summary, queue summary, artifact state summary,
  latest transition decision, non-claims.
- `GovControlAction`: `start`, `pause`, `resume`, `stop`, `cancel`,
  `replan`, `cooldown`, with deterministic allow/block/requires-review
  outcomes.

The promotion criterion is reuse across more than Ravenclaw. Until then, these
remain Ravenclaw projection names, not public GovEngine API claims.
