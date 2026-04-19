from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from decision_quality import compute_decision_quality, aggregate_campaign_learning  # type: ignore


def test_compute_decision_quality_rewards_signal_and_exact_execution() -> None:
    score = compute_decision_quality({
        'promising': False,
        'signal_contract': {'workflow_promotion': {'status': 'promotable'}},
        'brain': {'planner_alignment': 'override', 'redundancy_risk': 'low', 'action_type': 'differential_probe'},
        'analysis_contract': {'expected_signal_observed': 'yes', 'evidence_goal_met': 'yes', 'hypothesis_support': 'strengthened'},
        'engine_compiler': {'semantic_loss_detected': False, 'semantic_loss_policy': {'loss_class': 'none'}},
    })
    assert score['decision_quality_score'] > 0.7
    assert score['information_gain_score'] > 0.3
    assert score['semantic_loss_penalty'] == 0.0


def test_compute_decision_quality_uses_semantic_loss_policy_penalty() -> None:
    score = compute_decision_quality({
        'promising': True,
        'brain': {'planner_alignment': 'aligned', 'redundancy_risk': 'low', 'action_type': 'fingerprint_probe'},
        'analysis_contract': {'expected_signal_observed': 'partial', 'evidence_goal_met': 'partial', 'hypothesis_support': 'inconclusive'},
        'engine_compiler': {'semantic_loss_detected': True, 'semantic_loss_policy': {'loss_class': 'degraded_semantics'}},
    })
    assert score['semantic_loss_penalty'] == -0.25


def test_aggregate_campaign_learning_tracks_action_yield_and_override_success() -> None:
    learning = aggregate_campaign_learning([
        {
            'promising': False,
            'signal_contract': {'workflow_promotion': {'status': 'promotable'}, 'success_outcome': {'status': 'partial'}},
            'brain': {'action_type': 'differential_probe', 'planner_alignment': 'override', 'capability': 'http_probe'},
            'engine_compiler': {'compiler_tool_choice': 'curl'},
            'campaign_state': {'host_stage': 'active_validation'},
            'runtime_task': {
                'planning_ladder': {'current_stage': 'control_boundary_confirmation', 'next_stage': 'bounded_exploit_proof'},
                'planner_rationale': {'target_profile_summary': {'target_type': 'api'}, 'target_surface_rationale': ['authenticated_or_boundary_mapping']},
            },
            'analysis_contract': {'expected_signal_observed': 'no'},
        },
        {'promising': False, 'brain': {'action_type': 'single_probe', 'planner_alignment': 'aligned'}, 'analysis_contract': {'expected_signal_observed': 'no'}},
    ])
    assert learning['action_type_yield']['differential_probe']['promising'] == 1
    assert learning['capability_yield']['http_probe']['runs'] == 1
    assert learning['tool_yield']['curl']['runs'] == 1
    assert learning['host_stage_yield']['active_validation']['runs'] == 1
    assert learning['planning_stage_yield']['control_boundary_confirmation']['runs'] == 1
    assert learning['next_stage_yield']['bounded_exploit_proof']['runs'] == 1
    assert learning['target_type_yield']['api']['runs'] == 1
    assert learning['target_surface_signal_yield']['authenticated_or_boundary_mapping']['runs'] == 1
    assert learning['planner_override_success']['count'] == 1
