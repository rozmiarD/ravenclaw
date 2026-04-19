from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from planer.planner_intent_contract import (  # type: ignore
    build_planning_ladder,
    compose_experiment_intent_contract,
    recommended_progression_from_planning_ladder,
    validate_experiment_intent_contract,
)


def test_build_planning_ladder_tracks_stage_and_prerequisites() -> None:
    ladder = build_planning_ladder(
        runtime_task_contract={
            'task_family': 'workflow',
            'recommended_action_types': ['state_transition_probe', 'confirmatory_probe'],
            'exploit_ladder': {
                'stage': 'state_transition_confirmation',
                'progression': ['discovery', 'validation', 'state_transition_confirmation', 'bounded_exploit_proof'],
                'proof_strategy': 'forbidden_transition_or_invariant_break',
            },
            'session_requirements': {'stateful': True, 'auth_context': True, 'prerequisites': ['capture workflow state markers']},
            'actor_requirements': {'required': True, 'differential': False},
            'promotion_policy': {'bounded_only': True},
        },
        success_model='differential_or_stateful_signal',
        task_family='workflow',
        recommended_action_types=['state_transition_probe', 'confirmatory_probe'],
    )
    assert ladder['planning_mode'] == 'laddered'
    assert ladder['current_stage'] == 'state_transition_confirmation'
    assert ladder['next_stage'] == 'bounded_exploit_proof'
    assert ladder['stateful'] is True
    assert ladder['auth_context'] is True
    assert ladder['prerequisites'] == ['capture workflow state markers']
    assert ladder['recommended_action_types'][:2] == ['state_transition_probe', 'confirmatory_probe']



def test_compose_experiment_intent_contract_mirrors_runtime_task_semantics() -> None:
    out = compose_experiment_intent_contract(
        base_intent={
            'intent_id': 'intent-authz-1',
            'target': 'https://api.example.com/',
            'target_host': 'api.example.com',
            'target_type': 'api',
            'task_family': 'authz',
            'objective': 'AuthN/AuthZ boundary probing (safe)',
            'capability_candidates': ['http_probe', 'response_diff'],
            'recommended_action_types': ['differential_probe', 'confirmatory_probe'],
            'evidence_contract': {'expected_signal_type': 'behavior_delta', 'evidence_goal_type': 'controlled_comparison'},
            'success_model': 'differential_or_stateful_signal',
            'planner_constraints': {'campaign_bound_context': True},
            'planner_preferences': {'preferred_vector_families': ['authz']},
            'ambiguity_flags': ['tenant edge'],
            'open_questions': ['role inheritance unclear'],
        },
        runtime_task_contract={
            'task_family': 'authz',
            'target': 'https://api.example.com/',
            'objective': 'AuthN/AuthZ boundary probing (safe)',
            'recommended_action_types': ['differential_probe', 'confirmatory_probe'],
            'capability_candidates': ['http_probe', 'response_diff'],
            'exploit_ladder': {'stage': 'control_boundary_confirmation', 'progression': ['discovery', 'validation', 'control_boundary_confirmation']},
            'actor_requirements': {'required': True, 'differential': True, 'preferred_roles': ['anonymous', 'baseline_user']},
            'session_requirements': {'stateful': False, 'auth_context': True, 'prerequisites': ['establish comparison identities']},
            'promotion_policy': {'followup_allowed': True, 'confirm_preferred': True, 'bounded_only': True},
            'approval_sensitivity': {'owner_approval_required': True, 'auth_sensitive': True},
        },
        success_model='differential_or_stateful_signal',
    )
    assert out['runtime_task_contract']['schema_version'] == 2
    assert out['action_type'] == out['runtime_task_contract']['action_type']
    assert out['capability'] == out['runtime_task_contract']['capability']
    assert out['planning_ladder']['current_stage'] == 'control_boundary_confirmation'
    assert out['planning_ladder']['differential'] is True
    assert out['planning_ladder']['recommended_action_types'][0] == 'differential_probe'



def test_validate_experiment_intent_contract_rejects_mirror_drift() -> None:
    out = compose_experiment_intent_contract(
        base_intent={
            'intent_id': 'intent-authz-2',
            'target': 'https://api.example.com/',
            'target_host': 'api.example.com',
            'target_type': 'api',
            'task_family': 'authz',
            'objective': 'AuthN/AuthZ boundary probing (safe)',
            'capability_candidates': ['http_probe', 'response_diff'],
            'recommended_action_types': ['differential_probe', 'confirmatory_probe'],
            'evidence_contract': {'expected_signal_type': 'behavior_delta', 'evidence_goal_type': 'controlled_comparison'},
            'success_model': 'differential_or_stateful_signal',
            'planner_constraints': {'campaign_bound_context': True},
            'planner_preferences': {'preferred_vector_families': ['authz']},
            'ambiguity_flags': [],
            'open_questions': [],
        },
        runtime_task_contract={
            'task_family': 'authz',
            'target': 'https://api.example.com/',
            'objective': 'AuthN/AuthZ boundary probing (safe)',
            'recommended_action_types': ['differential_probe', 'confirmatory_probe'],
            'capability_candidates': ['http_probe', 'response_diff'],
            'exploit_ladder': {'stage': 'control_boundary_confirmation', 'progression': ['discovery', 'validation', 'control_boundary_confirmation']},
        },
        success_model='differential_or_stateful_signal',
    )
    out['action_type'] = 'single_probe'
    try:
        validate_experiment_intent_contract(out)
        raise AssertionError('expected mirror drift rejection')
    except ValueError as exc:
        assert 'experiment_intent_mirror_mismatch_action_type' in str(exc)



def test_recommended_progression_from_planning_ladder_prefers_stage_window_and_target_hint() -> None:
    ladder = build_planning_ladder(
        runtime_task_contract={
            'task_family': 'auth_flow',
            'recommended_action_types': ['state_transition_probe', 'differential_probe', 'confirmatory_probe'],
            'exploit_ladder': {
                'stage': 'state_transition_confirmation',
                'progression': ['discovery', 'validation', 'state_transition_confirmation', 'bounded_exploit_proof', 'report_artifact_capture'],
                'proof_strategy': 'authentication_state_transition_validation',
            },
            'session_requirements': {'stateful': True, 'auth_context': True, 'prerequisites': ['capture anti-csrf/state tokens']},
            'actor_requirements': {'required': True, 'differential': False},
            'promotion_policy': {'bounded_only': True},
        },
        success_model='differential_or_stateful_signal',
        task_family='auth_flow',
        recommended_action_types=['state_transition_probe', 'differential_probe', 'confirmatory_probe'],
    )
    progression = recommended_progression_from_planning_ladder(
        planning_ladder=ladder,
        target_type='auth',
        preferred_vector_families=['auth_flow'],
    )
    assert progression[0] == 'authenticated_or_boundary_mapping'
    assert 'state_transition_confirmation' in progression
    assert 'bounded_exploit_proof' in progression
    assert 'state_transition_probe' in progression
