from __future__ import annotations

from typing import Any, Dict

from evaluation_bundle import normalize_variant_ref  # type: ignore
from evaluation_metrics import aggregate_replay_metrics  # type: ignore


VARIANT_COMPARISON_SCHEMA_VERSION = 'phase5-variant-comparison-v1'


def _safe_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _metric_rate(metrics: Dict[str, Any], group: str, name: str) -> float:
    return float((((metrics.get(group) or {}).get(name) or {}).get('rate') or 0.0))


def compare_variant_outputs(
    baseline_output: Dict[str, Any] | None,
    candidate_output: Dict[str, Any] | None,
    *,
    baseline_variant: Dict[str, Any] | None = None,
    candidate_variant: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    baseline_output = _safe_dict(baseline_output)
    candidate_output = _safe_dict(candidate_output)
    baseline_results = [item for item in list(baseline_output.get('results') or []) if isinstance(item, dict)]
    candidate_results = [item for item in list(candidate_output.get('results') or []) if isinstance(item, dict)]
    baseline_map = {str(item.get('bundle_id') or ''): item for item in baseline_results if str(item.get('bundle_id') or '')}
    candidate_map = {str(item.get('bundle_id') or ''): item for item in candidate_results if str(item.get('bundle_id') or '')}
    shared_ids = sorted(set(baseline_map) & set(candidate_map))

    decision_deltas = []
    for bundle_id in shared_ids:
        left = baseline_map[bundle_id]
        right = candidate_map[bundle_id]
        if (
            str(left.get('requested_action') or '') != str(right.get('requested_action') or '')
            or str(left.get('effective_action') or '') != str(right.get('effective_action') or '')
            or str(left.get('status') or '') != str(right.get('status') or '')
        ):
            decision_deltas.append({
                'bundle_id': bundle_id,
                'target': _safe_dict(left.get('run_identity')).get('target') or _safe_dict(right.get('run_identity')).get('target'),
                'objective': _safe_dict(left.get('run_identity')).get('objective') or _safe_dict(right.get('run_identity')).get('objective'),
                'baseline_requested_action': left.get('requested_action'),
                'candidate_requested_action': right.get('requested_action'),
                'baseline_effective_action': left.get('effective_action'),
                'candidate_effective_action': right.get('effective_action'),
                'baseline_status': left.get('status'),
                'candidate_status': right.get('status'),
            })

    baseline_metrics = aggregate_replay_metrics(baseline_results)
    candidate_metrics = aggregate_replay_metrics(candidate_results)

    tracked = [
        ('yield_metrics', 'candidate_to_confirmed_conversion'),
        ('yield_metrics', 'confirmed_to_exploit_proof_conversion'),
        ('yield_metrics', 'exploit_proof_to_report_quality_conversion'),
        ('governance_metrics', 'policy_block_rate'),
        ('governance_metrics', 'blocked_evidence_rate'),
        ('governance_metrics', 'replay_divergence_rate'),
        ('governance_metrics', 'contamination_hit_rate'),
        ('auth_state_metrics', 'stateful_branch_success_rate'),
        ('semantic_class_metrics', 'weak_evidence_rate'),
        ('semantic_class_metrics', 'stronger_evidence_rate'),
        ('queue_metrics', 'repeat_probe_waste_rate'),
        ('intelligence_quality_metrics', 'branch_quality_rate'),
        ('intelligence_quality_metrics', 'dead_end_avoidance_rate'),
        ('intelligence_quality_metrics', 'recon_to_exploit_conversion_rate'),
        ('intelligence_quality_metrics', 'signal_to_confirmation_efficiency'),
    ]
    metric_deltas = []
    governance_regressions = []
    for group, name in tracked:
        left_rate = _metric_rate(baseline_metrics, group, name)
        right_rate = _metric_rate(candidate_metrics, group, name)
        delta = round(right_rate - left_rate, 3)
        row = {'group': group, 'name': name, 'baseline_rate': left_rate, 'candidate_rate': right_rate, 'delta': delta}
        metric_deltas.append(row)
        if name in {'policy_block_rate', 'blocked_evidence_rate', 'replay_divergence_rate', 'contamination_hit_rate', 'repeat_probe_waste_rate'} and delta > 0:
            governance_regressions.append(row)

    return {
        'schema_version': VARIANT_COMPARISON_SCHEMA_VERSION,
        'baseline_variant': normalize_variant_ref(baseline_variant or baseline_output.get('variant')),
        'candidate_variant': normalize_variant_ref(candidate_variant or candidate_output.get('variant')),
        'shared_bundle_count': len(shared_ids),
        'decision_delta_count': len(decision_deltas),
        'decision_deltas': decision_deltas,
        'metrics_baseline': baseline_metrics,
        'metrics_candidate': candidate_metrics,
        'metric_deltas': metric_deltas,
        'governance_regressions': governance_regressions,
    }
