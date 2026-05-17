from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from govengine.contracts.analysis import build_analysis_contract  # type: ignore


def test_build_analysis_contract_maps_success_semantics() -> None:
    contract = build_analysis_contract(
        result={
            'brain': {
                'action_type': 'differential_probe',
                'hypothesis': 'authz delta exists',
                'expected_signal': 'status/header delta',
                'evidence_goal': 'confirm authz asymmetry',
                'planner_alignment': 'aligned',
                'redundancy_risk': 'low',
            },
            'engine_compiler': {'semantic_loss_detected': False, 'compiler_strategy': 'differential_lowering', 'compiler_variant_count': 2},
            'success_criteria': {'typed_family_eval': 'authz_boundary', 'gap': 'need_clear_allow_deny_or_boundary_evidence', 'evidence': ['engine_ok'], 'success_model': 'differential_or_stateful_signal', 'expected_signal_type': 'behavior_delta', 'evidence_goal_type': 'controlled_comparison', 'required_evidence_hits': ['http_status']},
        },
        task_ctx={'task_family': 'authz', 'success_semantics': {'success_model': 'differential_or_stateful_signal', 'expected_signal_type': 'behavior_delta', 'evidence_goal_type': 'controlled_comparison'}},
        success_eval_status='partial',
        engine_status='ok',
    )
    assert contract['action_type'] == 'differential_probe'
    assert contract['expected_signal_observed'] == 'partial'
    assert contract['evidence_goal_met'] == 'partial'
    assert contract['hypothesis_support'] == 'inconclusive'
    assert contract['semantic_execution_fit'] == 'exact'
    assert contract['semantic_loss_class'] == 'none'
    assert contract['semantic_loss_policy_response'] == 'proceed'
    assert contract['approved_under_degradation'] is False
    assert contract['typed_family_eval'] == 'authz_boundary'
    assert contract['success_gap'] == 'need_clear_allow_deny_or_boundary_evidence'
    assert contract['success_evidence'] == ['engine_ok']
