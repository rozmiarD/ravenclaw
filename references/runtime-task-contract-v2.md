# Runtime task contract v2

Status: active
Canonical source: `engine/runtime_task_schema.py`
Primary normalizer: `normalize_runtime_task_v2(...)`
Schema version: `2`

## Purpose
`runtime_task` v2 is the canonical runtime-facing task envelope shared across planner output, runtime plan synthesis, runner normalization, queue escalation, and execution handoff.

It exists to prevent the same semantics from being re-derived differently in multiple modules.

## Canonical fields

### Core identity / targeting
- `schema_version`
- `target`
- `objective`
- `task_family`
- `experiment_intent_id`

### Success / evidence contract
- `task_success_criteria`
- `campaign_success_criteria`
- `acceptance_checks`
- `evidence_required`
- `success_semantics`
- `evidence_goal`
- `open_questions`
- `hypothesis_candidates`

### Planning lineage / ownership
- `planner_constraints`
- `planner_preferences`
- `planner_input_source`
- `planner_field_ownership`
- `planner_rationale`

### Capability / action semantics
- `capability_candidates`
- `recommended_action_types`
- `action_type`
- `capability`
- `experiment_shape`
- `recommended_tools`

### Runtime semantics (Phase 1 canonical set)
- `exploit_ladder`
- `actor_requirements`
- `session_requirements`
- `promotion_policy`
- `contamination_policy`
- `approval_sensitivity`

### Planner-governed execution shaping (current bridge fields)
- `expected_depth`
- `activation_phase`
- `activation_mode`
- `conditional_gate`
- `surface_role`
- `target_cluster`

### Economics / scheduling hints
- `priority_score`
- `cost_band`

## Ownership model

### Planner-owned or planner-originated
These should be emitted intentionally by planner output whenever experiment intents are available:
- `target`
- `objective`
- `task_family`
- `capability_candidates`
- `recommended_action_types`
- `experiment_intent_id`
- `planner_constraints`
- `planner_preferences`
- `success_semantics`
- `evidence_goal`
- `exploit_ladder`
- `actor_requirements`
- `session_requirements`
- `promotion_policy`
- `contamination_policy`
- `approval_sensitivity`
- `expected_depth`
- `activation_phase`
- `activation_mode`
- `conditional_gate`
- `surface_role`
- `target_cluster`

### Runtime-normalized / canonicalized
These may be planner-originated but are normalized centrally by `normalize_runtime_task_v2(...)`:
- `schema_version`
- `action_type`
- `capability`
- `experiment_shape`
- default exploit ladder progression
- default actor/session/promotion/approval booleans
- normalization of semantic/string activation-phase values into canonical runtime form
- list de-duplication / lowercasing for candidate fields

### Runtime-owned / execution-time only
These are not canonical planner contract fields even if they travel alongside `runtime_task` later:
- queue lane metadata
- empirical yield scores
- effective-decision blockers/results
- execution/compiler-specific tool choice artifacts

## Consumer map

### Direct canonical consumers
- `engine/runtime_plan_service.py`
  - builds runtime plan entries from blueprint experiment intents / legacy seeds
- `engine/auto_campaign_runner.py`
  - normalizes queued/runtime tasks and mirrors contract metadata
- `engine/runtime_decision_engine.py`
  - consumes `evidence_goal`, `exploit_ladder`, `actor_requirements`, `session_requirements`, `promotion_policy`, `approval_sensitivity`
- `engine/runtime_effective_decision.py`
  - propagates semantic fields into followup / precision queued tasks
- `engine/runtime_queue_strategy.py`
  - scores by exploit ladder, actor/session semantics, auth sensitivity
- `engine/runtime_task_execution.py`
  - serializes canonical runtime-task context into pipeline dispatch payloads
- `engine/runtime_execution_gate.py`
  - consumes planner-governed execution-shaping fields for bounded runtime admission/execution enforcement
- `engine/auto_campaign_precheck.py`
  - applies planner/runtime admission checks before task execution proceeds down the hot path

### Planner producers
- `engine/planer/blueprint.py`
  - emits experiment intents with mirrored runtime-task contract semantics
- `engine/planer/schema.py`
  - validates that planner output carries the canonical semantic subset

### UI / state observers
- `engine/auto_campaign_state.py`
- `logdash/services.py`
- `tests/test_logdash_smoke.py`

## Invariants
- `runtime_task_contract.schema_version == 2`
- `action_type`, `capability`, `experiment_shape`, `evidence_goal` must be non-empty after normalization
- mirrored experiment-intent semantic fields must match the normalized `runtime_task_contract`
- planner/runtime bridge should preserve planner-emitted semantics instead of reconstructing weaker approximations

## Current truth note
The planner-governed execution-shaping fields above are no longer documentation-only metadata.
In the current runtime they materially affect bounded admission/execution behavior for phase/mode/gate/depth/cluster/surface-role semantics.

## Test coverage anchors
- `engine/tests/test_runtime_task_schema.py`
- `engine/tests/test_runtime_plan_service_contracts.py`
- `engine/tests/test_auto_campaign_runner_facade.py`
- `engine/tests/test_runtime_decision_engine.py`
- `engine/tests/test_runtime_effective_decision.py`
- `engine/tests/test_runtime_queue_strategy.py`
