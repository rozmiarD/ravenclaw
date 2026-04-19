from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from decision_quality import aggregate_campaign_learning  # type: ignore
from runtime_utility import compute_runtime_utility  # type: ignore


def test_learning_and_utility_foundations_are_nonempty() -> None:
    learning = aggregate_campaign_learning([
        {'promising': True, 'brain': {'action_type': 'differential_probe', 'planner_alignment': 'override'}, 'analysis_contract': {'expected_signal_observed': 'partial'}},
    ])
    utility = compute_runtime_utility(action_type='differential_probe', decision_quality={'information_gain_score': 0.2, 'redundancy_penalty': 0.0}, economics={'priority_score': 0.3}, promising=True, host_state_band='healthy', task_family='authz')
    assert learning['action_type_yield']['differential_probe']['runs'] == 1
    assert utility['net_utility_score'] > 0.4


def test_learning_excludes_contaminated_runs_and_utility_records_penalty() -> None:
    learning = aggregate_campaign_learning([
        {'promising': True, 'brain': {'action_type': 'differential_probe'}, 'analysis_contract': {'expected_signal_observed': 'partial'}, 'run_contamination': {'status': 'contaminated', 'learning_excluded': True, 'tags': ['request_shape_cross_host_mismatch']}},
        {'promising': True, 'brain': {'action_type': 'confirmatory_probe'}, 'analysis_contract': {'expected_signal_observed': 'partial'}},
    ])
    assert 'differential_probe' not in learning['action_type_yield']
    assert learning['action_type_yield']['confirmatory_probe']['runs'] == 1
    assert learning['contamination_summary']['excluded_runs'] == 1
    assert learning['contamination_summary']['tags']['request_shape_cross_host_mismatch'] == 1

    utility = compute_runtime_utility(
        action_type='confirmatory_probe',
        decision_quality={'information_gain_score': 0.18, 'redundancy_penalty': 0.0},
        economics={'priority_score': 0.26},
        promising=False,
        host_state_band='healthy',
        task_family='recon',
        contamination={'status': 'contaminated', 'score': 0.4, 'learning_excluded': True},
    )
    assert utility['contamination_status'] == 'contaminated'
    assert utility['contamination_penalty'] > 0
    assert utility['learning_excluded'] is True
