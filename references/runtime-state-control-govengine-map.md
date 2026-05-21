# Runtime State and Control GovEngine Map

This note is the 0.11 planning map for projecting Ravenclaw runtime state and
Logdash control semantics onto GovEngine-compatible contracts.

It is not an implementation claim. Ravenclaw still owns local state storage,
Logdash behavior, campaign UX, and security-runtime semantics. GovEngine 0.3
provides the runtime-shell validation surface for neutral control actions,
queue snapshots, runtime snapshots, and scheduler-tick metadata. It still does
not own Ravenclaw's runtime persistence, queue mutation, Logdash UI state, or
campaign lifecycle.

## Current validation baseline

Before this map was written, these gates passed in a clean validation virtualenv:

- `python scripts/validate_public_install.py --dev`
- `python scripts/run_security_contract_validation.py --structural-only --include-pytest`
- `python -m pytest -q engine/tests/test_runtime_loop_control.py engine/tests/test_runtime_plan_control.py engine/tests/test_runtime_override_control.py engine/tests/test_runtime_runner_controls.py engine/tests/test_runtime_session_state.py engine/tests/test_runtime_runner_session_state_builders.py tests/test_logdash_control_paths.py tests/test_logdash_services_state_view.py`

The initial mapping baseline used `govengine==0.2.0` and
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

| Ravenclaw source | Current owner | 0.11 projected shape | GovEngine 0.3 fit | Next action |
| --- | --- | --- | --- | --- |
| `reports/.auto_campaign.state.json` | `engine/runtime_campaign_state.py`, runtime loop, Logdash control | runtime-shell state projection | Fits through `GovRuntimeSnapshot.state` plus host metadata | Keep persistence Ravenclaw-owned |
| `reports/.orchestrator.state.json` | `engine/runtime_campaign_state.py`, Logdash selected-campaign state | `GovOrchestratorState` | Partial via `GovernanceContext.metadata`; no canonical orchestrator-state model | Keep selected-campaign persistence Ravenclaw-owned; define neutral projection fields |
| `reports/.auto_campaign.queues.json` | `engine/auto_campaign_state.py`, `logdash/services.py` | `GovQueueSnapshot` | Fits through redaction-bounded lane previews | Keep queue mutation Ravenclaw-owned |
| `reports/.runtime_snapshot.json` | `engine/auto_campaign_state.py`, `logdash/services.py` | `GovRuntimeSnapshot` | Fits for neutral state/control/queue projection | Keep campaign/host/security telemetry Ravenclaw-owned |
| `reports/.runtime_plan.meta.json` | `engine/runtime_plan_service.py` | `GovPlanState` or runtime snapshot sub-block | Gap; current GovEngine task/planning contract is not the owner of Ravenclaw plan metadata | Wait for 0.12 task-contract mapping before extracting |
| `reports/.campaign.settings.json` | Logdash/runtime campaign settings | Host policy/profile settings | Not a GovEngine state model | Keep in Ravenclaw; pass selected booleans into GovEngine gate/context only when needed |
| `reports/.host_state.json` and `reports/learning_store.json` | Ravenclaw runtime learning and host heuristics | Security profile telemetry | Not a GovEngine state model | Keep in Ravenclaw security profile; do not extract generic state prematurely |
| `reports/state/public_targets_plan.json` | `engine/runtime_plan_service.py` | Task-plan projection | Deferred to 0.12 | Keep canonical path handling through `engine/paths.py` |

## Control action map

| Logdash/runtime action | Current behavior | 0.11 GovEngine-compatible projection | Notes |
| --- | --- | --- | --- |
| `start` | Validates selected runtime plan, spawns runtime when not alive, persists running state | `GovControlAction(action="start", requested_state="running")` | Spawning remains Ravenclaw-owned |
| `pause` | Requires live runtime, writes paused control state, runtime loop polls and blocks | `GovControlAction(action="pause", requested_state="paused")` | Pause is control evidence, not a GovEngine scheduler |
| `resume` | Clears paused state or reports existing live runtime as resumed | `GovControlAction(action="resume", requested_state="running")` | Preserve no-spawn resume semantics for already-live runtime |
| `stop` | Sets stopped state and terminates live runtime when present; clean stop allowed without live PID | `GovControlAction(action="stop", requested_state="stopped")` | Termination remains Ravenclaw host authority |
| `cancel` / archive-style cleanup | Removes or archives local generated state depending on endpoint | `GovControlAction(action="cancel", requested_state="cancelled")` when lifecycle-backed | Must not erase durable planner history |
| `replan` / activate blueprint | Resets selected campaign to idle and regenerates/activates runtime plan | `GovControlAction(action="replan", requested_state="idle")` | Planning semantics defer to 0.12 task-contract work |
| cooldown / skip / gate block | Runtime loop records skip/gate/cooldown summaries and host counters | `GovControlAction(action="cooldown", requested_state="cooldown")` | Host still owns cooldown counters and queue behavior |

## First implementation slice

Status: implemented as the Ravenclaw-owned helper
`engine/govengine_state_control_projection.py` with focused tests in
`engine/tests/test_govengine_state_control_projection.py`.

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

The helper now validates the control/queue/runtime projection against GovEngine
0.3 `runtime_shell` shapes. Earlier 0.2 projection gaps for `stopped`, `start`,
`resume`, `stop`, `cancel`, `replan`, `archive`, and `cooldown` are resolved as
first-class neutral control/state records.

The code names of the current host projections are
`gov_run_state_projection`, `gov_orchestrator_state_projection`,
`gov_queue_snapshot_projection`, and `gov_runtime_snapshot_projection`.
`engine/runtime_state_truth.py` and
`scripts/validate_runtime_state_truth.py` keep these projected state sources
aligned with `STATE_FILES.md` without moving persistence into GovEngine.

Stop if the projection requires moving Logdash behavior, live process control,
host-learning internals, or local state persistence into GovEngine.

## GovEngine 0.3 outcome

The initial promoted surface is `govengine.runtime_shell`:

- `GovControlAction`: `start`, `pause`, `resume`, `stop`, `cancel`, `replan`,
  `degrade_to_dry_run`, `cooldown`, `retry`, `archive`, and `record_only`.
- `GovQueueSnapshot`: lanes, counts, redaction-bounded preview items, saved
  timestamp, telemetry, and host metadata.
- `GovRuntimeSnapshot`: neutral state, control actions, queue snapshot,
  updated timestamp, non-claims, and host metadata.
- `GovSchedulerTick`: deterministic tick metadata without becoming a scheduler.

The remaining non-promoted areas are orchestrator-specific selected campaign
state and task-plan semantics; those defer to later mapping work rather than
being forced into GovEngine 0.3.
