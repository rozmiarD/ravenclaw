from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from runtime_economics_aggregate import aggregate_runtime_economics  # type: ignore


def test_aggregate_runtime_economics_produces_family_and_host_efficiency() -> None:
    runs = [
        {
            'target': 'https://a.example.com/',
            'task_family': 'recon',
            'brain': {'capability': 'fingerprint_probe'},
            'runtime_utility': {'net_utility_score': 0.7},
            'signal_contract': {'success_outcome': {'status': 'partial'}},
            'promising': True,
            'qualification': {'verdict': 'probable'},
            'decision_flags': {'confirm': True},
            'decision_economics': {'cost_weight': 0.4, 'value_estimate': 0.9, 'priority_score': 0.5},
            'decision_explain': {'why': []},
        },
        {
            'target': 'https://a.example.com/',
            'task_family': 'recon',
            'brain': {'capability': 'fingerprint_probe'},
            'runtime_utility': {'net_utility_score': 0.1},
            'signal_contract': {'success_outcome': {'status': 'failed'}},
            'promising': False,
            'qualification': {'verdict': 'none'},
            'decision_flags': {'confirm': False},
            'decision_economics': {'cost_weight': 0.6, 'value_estimate': 0.2, 'priority_score': -0.4},
            'decision_explain': {'why': []},
        },
        {
            'target': 'https://ignored.example.com/',
            'task_family': 'authz',
            'brain': {'capability': 'response_diff'},
            'runtime_utility': {'net_utility_score': 0.9},
            'promising': True,
            'decision_economics': {'cost_weight': 0.1, 'value_estimate': 0.9, 'priority_score': 0.8},
            'decision_explain': {'why': []},
            'run_contamination': {'learning_excluded': True},
        },
    ]
    out = aggregate_runtime_economics(runs)
    assert 'family_efficiency' in out
    assert 'host_efficiency' in out
    assert 'capability_efficiency' in out
    assert out['family_efficiency'][0]['key'] == 'recon'
    assert out['host_efficiency'][0]['key'] == 'a.example.com'
    assert 'explain' in out['host_efficiency'][0]
    assert out['capability_efficiency'][0]['key'] == 'fingerprint_probe'
    assert 'explain' in out['capability_efficiency'][0]
    assert out['empirical_steering']['excluded_runs'] == 1
    assert out['empirical_steering']['family_prior_top']
    assert out['empirical_steering']['capability_prior_top']
