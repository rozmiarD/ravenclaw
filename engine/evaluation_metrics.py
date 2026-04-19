from __future__ import annotations

from typing import Any, Dict, Iterable

from learning_store import summarize_branch_threads  # type: ignore


METRICS_SCHEMA_VERSION = 'phase5-metrics-v2'


def _safe_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _metric(numerator: int, denominator: int) -> Dict[str, Any]:
    return {
        'count': int(numerator),
        'denominator': int(denominator),
        'rate': round(int(numerator) / max(1, int(denominator)), 3),
    }


def _count(results: Iterable[Dict[str, Any]], predicate) -> int:
    return sum(1 for item in results if predicate(item))


def aggregate_replay_metrics(results: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    results_list = [dict(item) for item in results if isinstance(item, dict)]
    total = len(results_list)
    yield_excluded = [item for item in results_list if list(item.get('metric_exclusion_reasons') or [])]
    yield_eligible = [item for item in results_list if not list(item.get('metric_exclusion_reasons') or [])]

    candidate_count = _count(yield_eligible, lambda x: bool(x.get('candidate', False)))
    confirmed_count = _count(yield_eligible, lambda x: bool(x.get('confirmed', False)))
    exploit_proof_count = _count(yield_eligible, lambda x: bool(x.get('exploit_proof', False)))
    report_artifact_count = _count(yield_eligible, lambda x: bool(x.get('report_artifact', False)))
    useful_negative_count = _count(yield_eligible, lambda x: bool(x.get('useful_negative', False)))
    request_total = sum(int(item.get('request_count_estimate') or 1) for item in yield_eligible)
    useful_signal_runs = _count(yield_eligible, lambda x: bool(x.get('candidate', False) or x.get('useful_negative', False) or x.get('exploit_proof', False)))
    branch_completed_count = _count(yield_eligible, lambda x: bool(x.get('branch_completed', False)))
    weak_evidence_count = _count(results_list, lambda x: str(x.get('semantic_outcome_class') or '') == 'weak_evidence')
    blocked_evidence_count = _count(results_list, lambda x: str(x.get('semantic_outcome_class') or '') == 'blocked_evidence')
    stronger_evidence_count = _count(results_list, lambda x: str(x.get('semantic_outcome_class') or '') == 'stronger_evidence')

    policy_blocked_count = _count(results_list, lambda x: bool(x.get('policy_blocked', False)))
    owner_gate_count = _count(results_list, lambda x: bool(x.get('owner_gate_pending', False)))
    contamination_count = _count(results_list, lambda x: bool(x.get('contamination_excluded', False)))
    mismatch_count = _count(results_list, lambda x: 'cross_host_mismatch' in list(x.get('contamination_tags') or []))
    divergence_count = _count(results_list, lambda x: str(x.get('status') or '') == 'divergent')
    lineage_complete_count = _count(results_list, lambda x: bool(x.get('lineage_complete', False)))
    fallback_degraded_count = _count(results_list, lambda x: bool(x.get('fallback_degraded', False)))
    contract_gap_count = _count(results_list, lambda x: str(x.get('status') or '') in {'partial', 'invalid'})

    auth_branch_total = _count(results_list, lambda x: bool(x.get('auth_branch', False)))
    auth_branch_success = _count(results_list, lambda x: bool(x.get('auth_branch', False) and not x.get('auth_prereq_missing', False) and x.get('success_status') in {'partial', 'met'}))
    stateful_branch_total = _count(results_list, lambda x: bool(x.get('stateful_branch', False)))
    stateful_branch_success = _count(results_list, lambda x: bool(x.get('stateful_branch', False) and not x.get('state_prereq_missing', False) and x.get('success_status') in {'partial', 'met'}))
    actor_asymmetry_total = _count(results_list, lambda x: bool(x.get('actor_asymmetry_branch', False)))
    actor_asymmetry_success = _count(results_list, lambda x: bool(x.get('actor_asymmetry_success', False)))
    prereq_blocked_count = _count(results_list, lambda x: bool(x.get('auth_prereq_missing', False) or x.get('state_prereq_missing', False)))
    retry_waste_count = _count(results_list, lambda x: bool(x.get('repeat_probe_waste', False)))

    dead_branch_retry_count = _count(results_list, lambda x: bool(x.get('dead_branch_retry', False)))
    suppression_total = _count(results_list, lambda x: bool(x.get('policy_blocked', False) or x.get('auth_prereq_missing', False) or x.get('state_prereq_missing', False)))
    suppression_correct = _count(
        results_list,
        lambda x: bool((x.get('policy_blocked', False) or x.get('auth_prereq_missing', False) or x.get('state_prereq_missing', False)) and not (x.get('effective_action') or '')),
    )
    branch_candidate_total = _count(results_list, lambda x: bool(x.get('branch_candidate', False)))
    branch_quality_positive = _count(results_list, lambda x: bool(x.get('branch_quality_positive', False)))
    dead_end_branch_count = _count(results_list, lambda x: bool(x.get('dead_end_branch', False)))
    recon_to_exploit_candidate = _count(results_list, lambda x: bool(x.get('recon_to_exploit_candidate', False)))
    recon_to_exploit_success = _count(results_list, lambda x: bool(x.get('recon_to_exploit_success', False)))
    signal_bearing_total = _count(results_list, lambda x: bool(x.get('signal_bearing', False)))
    confirmation_reached = _count(results_list, lambda x: bool(x.get('confirmation_reached', False)))
    synthesis_alignment_count = _count(results_list, lambda x: bool(x.get('synthesis_alignment', False)))
    synthesis_positive_count = _count(results_list, lambda x: bool(x.get('synthesis_positive', False)))
    synthesis_pivot_total = _count(results_list, lambda x: str(x.get('synthesis_recommended_action') or '') == 'pivot')
    synthesis_pivot_avoidance_count = _count(results_list, lambda x: bool(x.get('synthesis_pivot_avoidance', False)))

    excluded_counts: dict[str, int] = {}
    for item in yield_excluded:
        for reason in list(item.get('metric_exclusion_reasons') or []):
            excluded_counts[str(reason)] = int(excluded_counts.get(str(reason), 0)) + 1

    return {
        'schema_version': METRICS_SCHEMA_VERSION,
        'totals': {
            'results_total': total,
            'yield_eligible_total': len(yield_eligible),
            'yield_excluded_total': len(yield_excluded),
            'excluded_by_reason': excluded_counts,
            'request_count_estimate_total': request_total,
        },
        'yield_metrics': {
            'candidate_to_confirmed_conversion': _metric(confirmed_count, candidate_count),
            'confirmed_to_exploit_proof_conversion': _metric(exploit_proof_count, confirmed_count),
            'exploit_proof_to_report_quality_conversion': _metric(report_artifact_count, exploit_proof_count),
            'useful_negative_result_rate': _metric(useful_negative_count, len(yield_eligible)),
            'novelty_gain_rate_proxy': _metric(useful_signal_runs, len(yield_eligible)),
            'signal_per_request': {
                'count': useful_signal_runs,
                'denominator': request_total,
                'rate': round(useful_signal_runs / max(1, request_total), 3),
            },
            'branch_completion_efficiency': _metric(branch_completed_count, len(yield_eligible)),
            'bounded_proof_capture_rate': _metric(report_artifact_count, len(yield_eligible)),
        },
        'governance_metrics': {
            'policy_block_rate': _metric(policy_blocked_count, total),
            'owner_gated_dependency_rate': _metric(owner_gate_count, total),
            'blocked_evidence_rate': _metric(blocked_evidence_count, total),
            'cross_host_mismatch_rate': _metric(mismatch_count, total),
            'contamination_hit_rate': _metric(contamination_count, total),
            'replay_divergence_rate': _metric(divergence_count, total),
            'lineage_completeness_rate': _metric(lineage_complete_count, total),
            'fallback_degraded_resolution_rate': _metric(fallback_degraded_count, total),
            'semantic_contract_gap_rate': _metric(contract_gap_count, total),
        },
        'auth_state_metrics': {
            'auth_required_branch_success_rate': _metric(auth_branch_success, auth_branch_total),
            'stateful_branch_success_rate': _metric(stateful_branch_success, stateful_branch_total),
            'actor_asymmetry_conversion_rate': _metric(actor_asymmetry_success, actor_asymmetry_total),
            'prerequisite_blocked_branch_rate': _metric(prereq_blocked_count, total),
            'retry_without_new_state_waste_rate': _metric(retry_waste_count, total),
        },
        'semantic_class_metrics': {
            'weak_evidence_rate': _metric(weak_evidence_count, total),
            'blocked_evidence_rate': _metric(blocked_evidence_count, total),
            'stronger_evidence_rate': _metric(stronger_evidence_count, total),
        },
        'queue_metrics': {
            'repeat_probe_waste_rate': _metric(retry_waste_count, total),
            'dead_branch_persistence_rate': _metric(dead_branch_retry_count, total),
            'branch_suppression_correctness_rate': _metric(suppression_correct, suppression_total),
            'capability_lane_yield_rate_proxy': _metric(useful_signal_runs, len(yield_eligible)),
        },
        'intelligence_quality_metrics': {
            'branch_quality_rate': _metric(branch_quality_positive, branch_candidate_total),
            'dead_end_avoidance_rate': _metric(max(0, branch_candidate_total - dead_end_branch_count), branch_candidate_total),
            'recon_to_exploit_conversion_rate': _metric(recon_to_exploit_success, recon_to_exploit_candidate),
            'signal_to_confirmation_efficiency': _metric(confirmation_reached, signal_bearing_total),
        },
        'synthesis_quality_metrics': {
            'synthesis_alignment_rate': _metric(synthesis_alignment_count, total),
            'synthesis_positive_rate': _metric(synthesis_positive_count, total),
            'synthesis_pivot_avoidance_rate': _metric(synthesis_pivot_avoidance_count, synthesis_pivot_total),
        },
        'branch_thread_summary': summarize_branch_threads(limit=5),
    }
