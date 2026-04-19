# Planner → runtime contract map

Status: active
Purpose: show which fields are authoritative in planner output, which ones are normalized by runtime, and where each field is consumed.

## Canonical planner output contract (experiment intent)
Primary source after this slice:
- `engine/planer/planner_intent_contract.py`
- `engine/planer/blueprint.py`
- `engine/planer/schema.py`

Required experiment-intent fields now include:
- targeting / identity:
  - `intent_id`, `target`, `target_host`, `target_type`, `task_family`, `objective`
- intent guidance:
  - `capability_candidates`, `recommended_action_types`, `evidence_contract`, `success_model`
  - `planner_constraints`, `planner_preferences`, `ambiguity_flags`, `open_questions`
- mirrored runtime contract:
  - `runtime_task_contract`
  - `action_type`, `capability`, `experiment_shape`, `evidence_goal`
  - `exploit_ladder`, `actor_requirements`, `session_requirements`, `promotion_policy`, `contamination_policy`, `approval_sensitivity`
  - `expected_depth`, `activation_phase`, `activation_mode`, `conditional_gate`, `surface_role`, `target_cluster`
- ladder-like planner view:
  - `planning_ladder`

## `planning_ladder` meaning
`planning_ladder` is a planner-side, runtime-safe summary derived from the canonical runtime-task semantics.

Current fields:
- `planning_mode`
- `task_family`
- `success_model`
- `current_stage`
- `next_stage`
- `stage_progression`
- `proof_strategy`
- `stateful`
- `auth_context`
- `differential`
- `bounded_only`
- `prerequisites`
- `recommended_action_types`

This is the first Phase 2 step away from “family seed only” planning and toward explicit ladder-shaped planning state.

## Ownership split

### Planner authoritative
- target selection / intent identity
- candidate action lanes
- planner constraints/preferences
- task-family-specific semantic intent
- planning ladder summary
- bounded execution-shaping hints (`expected_depth`, `activation_*`, conditional gate, surface role, target cluster)

### Runtime canonicalizer
- normalizes runtime-task contract via `normalize_runtime_task_v2(...)`
- preserves planner-authored fields
- backfills defaults only where planner omitted valid values
- normalizes semantic execution-shaping fields into canonical runtime values consumed by orchestration/gating layers

### Runtime consumers
- decision / escalation: `runtime_decision_engine.py`, `runtime_effective_decision.py`
- queue ordering: `runtime_queue_strategy.py`
- runner / dispatch handoff: `auto_campaign_runner.py`, `runtime_task_execution.py`
- admission/gating: `runtime_execution_gate.py`, `auto_campaign_precheck.py`
- state/UI observability: `auto_campaign_state.py`, `logdash/services.py`

## Current bridge rule
When experiment intents are present:
1. planner output is treated as canonical intent guidance
2. runtime plan service preserves the semantic mirror and planning ladder
3. runner/runtime hot path consume normalized runtime-task fields, not ad-hoc family guesses
4. bounded runtime admission/execution now honors planner-governed shaping fields instead of treating them as planner-only decoration

## Current note on remaining work
The biggest remaining work after this contract-mapping slice is no longer basic planner/runtime field transport.
The harder remaining problems are:
1. reducing duplicated semantic summaries between planner/runtime artifacts where canonical `semantic_lineage` / `semantic_lineage_summary` can replace parallel fields
2. tightening archival/report persistence rules so lineage hashes remain the stable join key across artifacts and future exports
3. selectively exposing semantic-lineage traces in operator/reporting views only where they improve auditability without clutter, preferring summary views over raw lineage parsing wherever possible
