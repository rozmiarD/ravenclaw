from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from govengine.planning import validate_plan_intent_contract, validate_planner_port, validate_task_contract  # type: ignore
from govengine_planning_projection import (  # type: ignore
    build_gov_plan_intent_projection,
    build_gov_task_contract_projection,
    ravenclaw_planner_port_projection,
)


def test_runtime_task_projection_redacts_target_and_validates_govengine_contract() -> None:
    projection = build_gov_task_contract_projection({
        'intent_id': 'intent-authz-1',
        'target': 'https://api.example.com/account/123',
        'target_type': 'api',
        'task_family': 'authz',
        'objective': 'AuthZ boundary check',
        'recommended_action_types': ['differential_probe'],
        'planner_constraints': {'campaign_bound_context': True},
        'planner_preferences': {'preferred_vector_families': ['authz']},
        'planner_rationale': {'target_surface_rationale': ['authenticated_or_boundary_mapping']},
        'planning_ladder': {'current_stage': 'control_boundary_confirmation'},
    })
    checked = validate_task_contract(projection)

    assert checked.contract_id == 'intent-authz-1'
    assert checked.target_ref.startswith('sha256:')
    assert checked.target_kind == 'api'
    assert checked.action_type == 'differential_probe'
    assert checked.metadata['target_redacted'] is True
    assert 'https://api.example.com/account/123' not in str(projection)


def test_plan_intent_projection_wraps_runtime_task_contract_without_execution_claim() -> None:
    projection = build_gov_plan_intent_projection({
        'intent_id': 'intent-workflow-1',
        'target': 'https://app.example.com/checkout',
        'target_type': 'web',
        'task_family': 'workflow',
        'objective': 'State transition mapping',
        'recommended_action_types': ['state_transition_probe'],
        'runtime_task_contract': {
            'task_family': 'workflow',
            'recommended_action_types': ['state_transition_probe'],
            'activation_mode': 'if_signal',
        },
    })
    checked = validate_plan_intent_contract(projection)

    assert checked.intent_id == 'intent-workflow-1'
    assert checked.profile == 'ravenclaw-security'
    assert checked.task_contracts[0].action_type == 'state_transition_probe'
    assert 'does_not_grant_execution_authority' in checked.non_claims
    assert 'https://app.example.com/checkout' not in str(projection)


def test_planner_port_projection_is_valid_descriptor() -> None:
    projection = ravenclaw_planner_port_projection()
    checked = validate_planner_port(projection)

    assert checked.name == 'ravenclaw-planner'
    assert checked.supported_contracts == ('gov_task_contract', 'gov_plan_intent_contract')
