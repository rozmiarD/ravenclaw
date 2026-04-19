from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from runtime_task_schema import normalize_runtime_task_v2  # type: ignore


def test_normalize_runtime_task_v2_derives_schema_and_ladder_defaults() -> None:
    out = normalize_runtime_task_v2({
        'objective': 'Probe actor boundary',
        'target': 'https://api.example.com/account',
        'task_family': 'authz',
        'recommended_action_types': ['differential_probe'],
        'success_semantics': {'evidence_goal_type': 'controlled_comparison'},
    })
    assert out['schema_version'] == 2
    assert out['action_type'] == 'differential_probe'
    assert out['capability'] == 'http_probe'
    assert out['experiment_shape'] == 'differential'
    assert out['evidence_goal'] == 'controlled_comparison'
    assert out['exploit_ladder']['stage'] == 'control_boundary_confirmation'
    assert out['actor_requirements']['required'] is True
    assert out['actor_requirements']['differential'] is True
    assert out['session_requirements']['auth_context'] is True
    assert out['promotion_policy']['confirm_preferred'] is True


def test_normalize_runtime_task_v2_respects_explicit_stateful_transition_metadata() -> None:
    out = normalize_runtime_task_v2({
        'task_family': 'workflow',
        'recommended_action_types': ['state_transition_probe'],
        'exploit_ladder': {'stage': 'state_transition_confirmation', 'progression': ['validation', 'state_transition_confirmation']},
        'session_requirements': {'prerequisites': ['capture csrf token']},
        'approval_sensitivity': {'owner_approval_required': True},
    })
    assert out['experiment_shape'] == 'state_transition'
    assert out['exploit_ladder']['stage'] == 'state_transition_confirmation'
    assert out['session_requirements']['stateful'] is True
    assert out['session_requirements']['prerequisites'] == ['capture csrf token']
    assert out['approval_sensitivity']['owner_approval_required'] is True


def test_normalize_runtime_task_v2_preserves_planner_execution_hints() -> None:
    out = normalize_runtime_task_v2({
        'task_family': 'authz',
        'priority_tier': 'high',
        'expected_depth': 'deep',
        'activation_phase': 2,
        'activation_mode': 'if_signal',
        'conditional_gate': 'authenticated_or_boundary_mapping',
        'surface_role': 'primary',
        'target_cluster': 'integration_api',
    })
    assert out['priority_tier'] == 'high'
    assert out['expected_depth'] == 'deep'
    assert out['activation_phase'] == 2
    assert out['activation_mode'] == 'if_signal'
    assert out['conditional_gate'] == 'authenticated_or_boundary_mapping'
    assert out['surface_role'] == 'primary'
    assert out['target_cluster'] == 'integration_api'


def test_normalize_runtime_task_v2_accepts_semantic_activation_phase_strings() -> None:
    out = normalize_runtime_task_v2({
        'task_family': 'authz',
        'activation_phase': 'bounded_exploit_proof',
    })
    assert out['activation_phase'] == 3
