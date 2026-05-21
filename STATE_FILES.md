# RAVENCLAW State Files

This document catalogs the main persisted state and artifact files used by the live runtime.

Goal: make it clear which files are authoritative, what they are for, and which component is expected to read/write them.

The public state-truth manifest is `engine/runtime_state_truth.py`.
`python scripts/validate_runtime_state_truth.py` checks this catalog against
that manifest, canonical path helpers, and the GovEngine projection map.

---

## 1. State-file design rules

- Shared state should be treated as a contract, not an implementation accident.
- UI and runtime must prefer helper/service functions over ad hoc file mutation.
- Append-only histories should stay append-only where possible.
- Ephemeral logs and durable control state should remain clearly separated.

## 1.1 Artifact classes

RAVENCLAW currently persists several different kinds of files. They should not all be treated the same in git or during cleanup.

- **Durable source/config** — operator-authored or system-defining inputs that belong in git.
- **Durable planning history** — versioned planner outputs intended to remain inspectable over time.
- **Runtime control-plane state** — live local state used by Logdash/runtime; authoritative locally, but not durable repo history.
- **Generated snapshots/cache** — rolling current-state artifacts derived from runtime activity.
- **Generated history/archive** — append-only or archived outputs that may need retention rules, but are not core source inputs.
- **Local operational logs/db** — process logs, SQLite event stores, pid files, and similar local runtime debris.

---

## 2. Core shared state

## `reports/.planner.ui.state.json`
Class:
- runtime control-plane state (ignore in git by default)

Purpose:
- stores planner/control-plane UI selections and workflow context

Typical owner:
- `engine/runtime_plan_service.py`
- Logdash planner/control-plane surfaces

Typical fields:
- `selected_campaign_key`
- scope input path or planner-related UI fields
- planner workflow state needed by the dashboard

## `reports/.campaign.settings.json`
Class:
- runtime control-plane state (ignore in git by default)

Purpose:
- persisted campaign runtime settings and selected control values

Typical owner:
- `logdash/app.py`
- `engine/runtime_campaign_state.py`

Typical fields:
- campaign-scoped settings
- global settings
- credentials policy toggles and approval state
- aggression override / owner override related values

## `reports/.orchestrator.state.json`
Class:
- runtime control-plane state (ignore in git by default)

Purpose:
- control-plane/orchestrator state for current selected campaign

Typical owner:
- `engine/runtime_campaign_state.py`
- Logdash control-plane surfaces

Typical fields:
- `selected_campaign_key`
- campaign lifecycle markers
- runtime activation context

## `reports/.auto_campaign.state.json`
Class:
- runtime control-plane state (ignore in git by default)

Purpose:
- current live state of the auto-campaign runner

Typical owner:
- `engine/auto_campaign_runner.py`
- `logdash/app.py`

Typical fields:
- `paused`
- `stopped`
- `owner_override`
- timestamps / updated markers

## `reports/.auto_campaign.queues.json`
Class:
- runtime control-plane state (ignore in git by default)

Purpose:
- queue/backlog snapshot used by auto-campaign runtime and dashboard queue views

Typical owner:
- `engine/auto_campaign_runner.py`
- `logdash/services.py`

## `reports/.runtime_plan.meta.json`
Class:
- runtime control-plane state (ignore in git by default)

Purpose:
- metadata for the active generated runtime plan

Typical owner:
- `engine/runtime_plan_service.py`
- read by runtime and Logdash through shared helpers

Typical fields:
- generated count
- target count
- selected campaign key
- timestamps
- quality block / plan validity notes
- planner-input-source lineage summary

## `reports/state/public_targets_plan.json`
Class:
- generated runtime snapshot/state (ignore in git by default)

Purpose:
- active runtime task list derived from selected blueprint

Typical owner:
- `engine/runtime_plan_service.py`
- read by orchestrator/runtime and Logdash

Compatibility note:
- `engine/public_targets_plan.json` remains a legacy compatibility mirror during the Phase-6 transition
- canonical path resolution should go through `engine/paths.py` rather than hard-coded path guesses
- see `references/runtime-artifact-ownership.md` for the short ownership guide

Typical fields per entry:
- `objective`
- `target`
- `task_family`
- `acceptance_checks`
- `evidence_required`
- `recommended_tools`
- `priority_score`
- runtime metadata / planner rationale / lineage / planner-input-source ownership
- planner-governed execution hints such as `expected_depth`, `activation_phase`, `activation_mode`, `conditional_gate`, `surface_role`, and `target_cluster`

## `reports/.host_state.json`
Class:
- runtime control-plane / learned local state (ignore in git by default)

Purpose:
- per-host learned behavior/runtime heuristics

Typical owner:
- `engine/auto_campaign_runner.py`
- supporting runtime orchestration modules

Typical fields:
- host-level state
- degradation markers
- prior-family performance or cooldown hints

## `reports/cache/context_summary.json`
Class:
- generated runtime cache (ignore in git by default)

Purpose:
- compact recent per-run context passed back into the governed pipeline

Typical owner:
- `engine/run_pipeline.py`
- `engine/pipeline_context.py`

Compatibility note:
- `engine/context_summary.json` remains a legacy compatibility mirror during the Phase-6 transition
- see `references/runtime-artifact-ownership.md` for the short ownership guide

Typical fields:
- recent objective/target/status records
- truncated engine output previews
- recent auditor decision summary
- compact analysis summary

---

## 3. Findings and historical artifacts

## `reports/findings-history.jsonl`
Class:
- generated durable local history (default: ignore in git, retain locally with archive policy)

Purpose:
- append-only findings/events history

Typical owner:
- auto-campaign qualification/reporting flow

Notes:
- should be treated as durable historical evidence
- good candidate for future schema validation

## `reports/auto-campaign-latest.json`
Class:
- generated current snapshot (ignore in git by default)

Purpose:
- latest campaign output snapshot

Typical owner:
- orchestrator/reporting flow

Notes:
- often acts as the most recent summary-vector/evaluation source for Logdash views when a richer archive is not consulted

## `reports/auto-campaign-summary.md`
Class:
- generated current snapshot/summary (ignore in git by default)

Purpose:
- operator-readable current summary

## `reports/latest/<run_id>/evaluation-replay.json`
Class:
- generated archive artifact (ignore in git by default)

Purpose:
- deterministic replay output for archived campaign summary vectors

## `reports/latest/<run_id>/evaluation-metrics.json`
Class:
- generated archive artifact (ignore in git by default)

Purpose:
- Phase-5 effectiveness/governance metric snapshot derived from replay results

## `reports/learning_store.json`
Class:
- generated durable local history/memory (default: ignore in git, retain locally with archive policy)

Purpose:
- persisted learning/heuristics from campaign runtime

## `reports/campaign_registry/<campaign_key>/...`
Class:
- durable planning history (keep tracked)

Purpose:
- immutable planner outputs and version history

Contents typically include:
- `latest.json`
- `versions/vXXXX/blueprint.json`
- `versions/vXXXX/blueprint.yaml`
- `versions/vXXXX/templates/*`

Design intent:
- this registry is the durable planning truth
- runtime plans should be derivable from it
- new registry keys prefer `planner_identity_hash` semantics (source hash + operator flags + planner semantics), while legacy source-hash-keyed entries remain readable

Typical `latest.json` metadata now includes:
- `source_program_hash_sha256`
- `operator_flags_hash_sha256`
- `planner_semantics_hash_sha256`
- `planner_identity_hash_sha256`
- `planner_provenance_mode`

---

## 4. Logs and transient operational files

## `logs/execution.log`
Purpose:
- executor runtime logging

## `logdash/logs.db`
Class:
- local operational log database (ignore in git by default)

Purpose:
- SQLite event log for dashboard/visibility

## `reports/.logdash.stdout.log` / `reports/.logdash.stderr.log`
Purpose:
- process/service logs for Logdash runtime when captured that way

## `reports/.auto_campaign.stdout.log` / `reports/.auto_campaign.stderr.log`
Purpose:
- runner stdout/stderr log capture

## `reports/.auto_campaign.pid`
Class:
- local operational process state (ignore in git by default)

Purpose:
- PID synchronization hint for live runner process

## `reports/.runtime_snapshot.json`
Class:
- runtime control-plane snapshot/state (ignore in git by default)

Purpose:
- consolidated runtime snapshot used by Logdash/runtime views when present

Typical owner:
- runtime persistence/reporting flow
- Logdash shared service helpers read/project it

Notes:
- selected-campaign filtering and projection for snapshot-backed API responses should be centralized in shared helpers, not reimplemented independently per endpoint

---

## `reports/.tool_registry.state.json`
Class:
- runtime control-plane state (ignore in git by default)

Purpose:
- selected planner tooling profile / registry UI state

Typical owner:
- `govengine.tool_registry` plus Logdash tool-registry surfaces
- Logdash tool-registry surfaces

---

## 5. Owner approval and review state

## `reports/.owner_approval_actions.json`
Class:
- runtime control-plane approval state (ignore in git by default)

Purpose:
- records approved/deleted owner-gated actions surfaced in UI/runtime

## `reports/.owner.vector.approvals.json`
Class:
- runtime approval memory/state (ignore in git by default)

Purpose:
- per-host/per-vector preapproval memory used by runtime normalization paths

---

## 6. Recommended contract hardening

Future formalization targets:
- JSON schema for `reports/state/public_targets_plan.json`
- JSON schema for `.runtime_plan.meta.json`
- JSON schema for `.auto_campaign.state.json`
- JSON schema for `.host_state.json`
- JSON schema for findings history line objects

Minimum invariants worth preserving now:
- files should always contain JSON objects/lists of expected top-level type
- missing files should be handled as empty/default state, not as silent corruption
- write helpers should preserve backward compatibility where practical
- canonical path ownership should be explicit whenever a legacy compatibility mirror still exists
