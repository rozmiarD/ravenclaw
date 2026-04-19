# Evaluation replay contract (Phase 5)

Status: active
Updated: 2026-03-28

## Purpose
Define the bounded replay contract used by Phase 5 evaluation so Ravenclaw can replay historical runtime decisions and compute metrics without triggering live execution by default.

## Core rule
Replay is **downstream of runtime truth**.
It consumes canonical persisted artifacts; it does not invent a parallel semantic model.

## Primary objects

### Replay bundle
Schema version:
- `phase5-replay-bundle-v1`

Mandatory top-level fields:
- `schema_version`
- `bundle_id`
- `run_identity`
- `runtime_decision`
- `signal_contract`
- `execution`
- `semantic_lineage_summary`
- `variant`

Typical payload areas:
- `run_identity`
  - `run_id`
  - `campaign_key`
  - `index`
  - `plan_name`
  - `objective`
  - `target`
  - `task_family`
- `runtime_task`
- `runtime_decision`
- `signal_contract`
- `semantic_lineage`
- `semantic_lineage_summary`
- `execution`
- `analysis`
- `governance`

### Replay dataset
Schema version:
- `phase5-replay-dataset-v1`

Fields:
- `dataset_id`
- `run_id`
- `campaign_key`
- `variant`
- `bundle_count`
- `bundles`

### Replay result
Schema version:
- `phase5-replay-result-v1`

Result statuses:
- `ok`
- `partial`
- `divergent`
- `invalid`

## Determinism rules
- replay must not trigger live execution by default
- same bundle + same replay variant must produce the same replay result
- missing mandatory truth inputs should raise validation failure or produce explicit partial coverage, not silent guessing

## Replay modes
Current bounded modes:
- decision replay
- dataset replay over a bundle set
- metrics recomputation on replay results

## Variant identity
Every replay dataset should carry explicit variant identity:
- `variant_id`
- `family`
- `metric_version`
- `replay_version`
- optional `overrides`

## Divergence handling
Replay should record divergence reasons when:
- stored action and inferred action disagree
- effective status implies an action that is missing
- required lineage identity is missing or incomplete

## Non-goals
- broad execution simulation
- live target interaction by default
- UI-first replay semantics
