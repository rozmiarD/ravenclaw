# Effectiveness metrics contract (Phase 5)

Status: active
Updated: 2026-03-28

## Purpose
Define the versioned metric groups used by Phase 5 evaluation so effectiveness claims remain traceable and governance-aware.

Schema version:
- `phase5-metrics-v1`

## Design rules
- blocked, gated, or contaminated branches must not be silently mixed into low-yield outcomes
- metric groups should expose numerator, denominator, and rate
- metric definitions are downstream of replay results, not ad-hoc dashboard logic

## Metric groups

### 1. Yield metrics
Examples:
- `candidate_to_confirmed_conversion`
- `confirmed_to_exploit_proof_conversion`
- `exploit_proof_to_report_quality_conversion`
- `useful_negative_result_rate`
- `novelty_gain_rate_proxy`
- `signal_per_request`
- `branch_completion_efficiency`
- `bounded_proof_capture_rate`

### 2. Governance metrics
Examples:
- `policy_block_rate`
- `owner_gated_dependency_rate`
- `cross_host_mismatch_rate`
- `contamination_hit_rate`
- `replay_divergence_rate`
- `lineage_completeness_rate`
- `fallback_degraded_resolution_rate`
- `semantic_contract_gap_rate`

### 3. Auth/state realism metrics
Examples:
- `auth_required_branch_success_rate`
- `stateful_branch_success_rate`
- `actor_asymmetry_conversion_rate`
- `prerequisite_blocked_branch_rate`
- `retry_without_new_state_waste_rate`

### 4. Queue/adaptation quality metrics
Examples:
- `repeat_probe_waste_rate`
- `dead_branch_persistence_rate`
- `branch_suppression_correctness_rate`
- `capability_lane_yield_rate_proxy`

## Exclusion rules
Yield metrics should exclude replay results marked with reasons such as:
- `policy_blocked`
- `owner_gate_pending`
- `contamination_excluded`

These remain visible in governance metrics and exclusion summaries.

## Interpretation rule
A drop in yield is not equivalent to a governance regression, and a governance regression is not equivalent to low exploitability. Both must remain separately inspectable.
