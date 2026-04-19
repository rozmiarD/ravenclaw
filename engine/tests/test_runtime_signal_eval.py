from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from runtime_signal_eval import evaluate_success_criteria  # type: ignore


def test_evaluate_success_criteria_uses_authz_typed_family_eval() -> None:
    out = evaluate_success_criteria(
        'Validate authz boundary behavior with clear allow/deny evidence.',
        {'status': 'ok', 'returncode': 0, 'stdout': 'Observed 403 forbidden on control and bypass candidate on variant', 'stderr': ''},
        'authz boundary probe summary',
        {'findings': ['authz delta'], 'risk': 'medium'},
        task_family='authz',
    )
    assert out['status'] == 'met'
    assert out['typed_family_eval'] == 'authz_boundary'
    assert 'engine_ok' in out['evidence']


def test_evaluate_success_criteria_uses_inventory_typed_family_eval() -> None:
    out = evaluate_success_criteria(
        'Produce reproducible endpoint inventory.',
        {'status': 'ok', 'returncode': 0, 'stdout': 'Discovered endpoint /api/v1/users and parameter tenant_id', 'stderr': ''},
        'inventory expansion summary',
        {'observations': ['endpoint inventory expanded']},
        task_family='recon',
    )
    assert out['status'] == 'met'
    assert out['typed_family_eval'] == 'inventory_growth'


def test_evaluate_success_criteria_marks_missing_criteria_with_typed_family() -> None:
    out = evaluate_success_criteria(
        '',
        {'status': 'ok', 'returncode': 0, 'stdout': '', 'stderr': ''},
        'no criteria',
        {},
        task_family='input_tamper',
    )
    assert out['status'] == 'not_provided'
    assert out['typed_family_eval'] == 'input_validation'


def test_evaluate_success_criteria_uses_explicit_success_semantics_contract() -> None:
    out = evaluate_success_criteria(
        'Validate authz boundary behavior with negative control and clear allow/deny evidence.',
        {'status': 'ok', 'returncode': 0, 'stdout': '__RC_METRICS__ code=403 observed response diff and allow/deny delta', 'stderr': ''},
        'authz summary with response diff',
        {'findings': ['authz delta'], 'risk': 'medium'},
        task_family='recon',
        acceptance_checks=['negative_control', 'allow_deny_delta'],
        evidence_required=['http_status', 'response_diff'],
        success_semantics={'success_model': 'differential_or_stateful_signal', 'expected_signal_type': 'behavior_delta', 'evidence_goal_type': 'controlled_comparison'},
    )
    assert out['status'] == 'met'
    assert out['typed_family_eval'] == 'authz_boundary'
    assert out['success_model'] == 'differential_or_stateful_signal'
    assert out['required_evidence_hits'] == ['http_status', 'response_diff']
