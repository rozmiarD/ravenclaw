from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from runtime_utility import compute_runtime_utility  # type: ignore


def test_compute_runtime_utility_combines_quality_and_noise() -> None:
    utility = compute_runtime_utility(
        action_type='differential_probe',
        decision_quality={'information_gain_score': 0.4, 'novelty_gain_score': 0.15, 'reproducibility_score': 0.08, 'redundancy_penalty': 0.0},
        economics={'priority_score': 0.5},
        promising=True,
        host_state_band='healthy',
    )
    assert utility['net_utility_score'] > 0.9
    assert utility['novelty_gain_score'] == 0.15

    degraded = compute_runtime_utility(
        action_type='state_transition_probe',
        decision_quality={'information_gain_score': 0.1, 'false_positive_risk_penalty': 0.14, 'redundancy_penalty': -0.1},
        economics={'priority_score': 0.2},
        promising=False,
        host_state_band='degraded',
    )
    assert degraded['net_utility_score'] < utility['net_utility_score']
    assert degraded['false_positive_risk_penalty'] == 0.14


def test_compute_runtime_utility_rewards_high_leverage_actions_in_exploitation_band() -> None:
    exploit = compute_runtime_utility(
        action_type='state_transition_probe',
        decision_quality={'information_gain_score': 0.22, 'redundancy_penalty': 0.0},
        economics={'priority_score': 0.32},
        promising=True,
        host_state_band='exploitation',
        task_family='authz',
    )
    baseline = compute_runtime_utility(
        action_type='state_transition_probe',
        decision_quality={'information_gain_score': 0.22, 'redundancy_penalty': 0.0},
        economics={'priority_score': 0.32},
        promising=True,
        host_state_band='healthy',
        task_family='recon',
    )
    assert exploit['net_utility_score'] > baseline['net_utility_score']
    assert exploit['family_action_bias'] > 0
    assert exploit['exploitation_bonus'] > 0
