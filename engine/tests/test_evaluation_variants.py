from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from evaluation_variants import compare_variant_outputs  # type: ignore


def test_compare_variant_outputs_reports_decision_deltas_and_governance_regressions() -> None:
    bundle_id = 'bundle-1'
    baseline = {
        'variant': {'variant_id': 'baseline'},
        'results': [
            {
                'bundle_id': bundle_id,
                'run_identity': {'target': 'https://api.example.com', 'objective': 'Probe'},
                'requested_action': 'confirm',
                'effective_action': 'confirm',
                'status': 'ok',
                'candidate': True,
                'confirmed': True,
                'exploit_proof': False,
                'report_artifact': False,
                'useful_negative': False,
                'policy_blocked': False,
                'owner_gate_pending': False,
                'contamination_excluded': False,
                'contamination_tags': [],
                'lineage_complete': True,
                'fallback_degraded': False,
                'auth_branch': False,
                'auth_prereq_missing': False,
                'stateful_branch': False,
                'state_prereq_missing': False,
                'actor_asymmetry_branch': False,
                'actor_asymmetry_success': False,
                'repeat_probe_waste': False,
                'dead_branch_retry': False,
                'branch_completed': True,
                'request_count_estimate': 1,
                'metric_exclusion_reasons': [],
                'success_status': 'partial',
            }
        ],
    }
    candidate = {
        'variant': {'variant_id': 'candidate'},
        'results': [
            {
                'bundle_id': bundle_id,
                'run_identity': {'target': 'https://api.example.com', 'objective': 'Probe'},
                'requested_action': 'followup',
                'effective_action': 'followup',
                'status': 'divergent',
                'candidate': True,
                'confirmed': False,
                'exploit_proof': False,
                'report_artifact': False,
                'useful_negative': False,
                'policy_blocked': True,
                'owner_gate_pending': False,
                'contamination_excluded': False,
                'contamination_tags': [],
                'lineage_complete': True,
                'fallback_degraded': False,
                'auth_branch': False,
                'auth_prereq_missing': False,
                'stateful_branch': False,
                'state_prereq_missing': False,
                'actor_asymmetry_branch': False,
                'actor_asymmetry_success': False,
                'repeat_probe_waste': True,
                'dead_branch_retry': True,
                'branch_completed': False,
                'request_count_estimate': 1,
                'metric_exclusion_reasons': ['policy_blocked'],
                'success_status': 'not_met',
            }
        ],
    }
    comparison = compare_variant_outputs(baseline, candidate)
    assert comparison['decision_delta_count'] == 1
    assert comparison['decision_deltas'][0]['baseline_requested_action'] == 'confirm'
    assert any(item['name'] == 'policy_block_rate' and item['delta'] > 0 for item in comparison['governance_regressions'])
    assert any(item['name'] == 'branch_quality_rate' for item in comparison['metric_deltas'])
    assert any(item['name'] == 'signal_to_confirmation_efficiency' for item in comparison['metric_deltas'])
