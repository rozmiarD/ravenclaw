from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from runtime_host_model import default_host_state, update_host_state  # type: ignore


def test_update_host_state_promising_success_updates_scores_and_family() -> None:
    prev = default_host_state()
    result = update_host_state(
        host='example.com',
        family='recon',
        previous=prev,
        run_info={
            'promising': True,
            'engine_status': 'ok',
            'success_criteria_eval': 'partial',
            'runtime_task': {
                'planning_ladder': {'current_stage': 'discovery', 'next_stage': 'validation'},
                'planner_rationale': {'target_profile_summary': {'target_type': 'api'}, 'target_surface_rationale': ['authenticated_or_boundary_mapping']},
            },
        },
    )
    hs = result.state
    assert hs['state'] == 'promising'
    assert hs['last_success_family'] == 'recon'
    assert hs['promise_score'] > 1.0
    assert hs['evidence_density'] > 0.5
    assert 'recon' in hs['preferred_families']
    assert 'discovery' in hs['preferred_stages']
    assert 'validation' in hs['preferred_stages']
    assert 'api' in hs['target_types_seen']
    assert 'authenticated_or_boundary_mapping' in hs['target_surface_rationale']
    assert hs['last_planning_stage'] == 'discovery'
    assert hs['last_next_stage'] == 'validation'
    assert result.previous_state_band == 'active'
    assert result.current_state_band == 'promising'
    assert result.state_changed is True
    assert 'promising_signal' in result.reasons
    assert result.deltas['promise_score'] > 0


def test_update_host_state_failed_run_can_degrade_and_suppress_family() -> None:
    prev = default_host_state()
    prev['runs'] = 3
    prev['noise_score'] = 0.83
    result = update_host_state(
        host='auth.example.com',
        family='authz',
        previous=prev,
        run_info={
            'promising': False,
            'engine_status': 'failed',
            'success_criteria_eval': 'failed',
        },
    )
    hs = result.state
    assert hs['noise_score'] < 0.83
    assert hs['state'] == 'degraded'
    assert 'authz' in hs['suppressed_families']
    assert result.regeneration_reason == 'degraded_host_shift'
    assert 'family_suppressed_for_noise' in result.reasons
    assert result.current_state_band == 'degraded'
    assert result.deltas['noise_score'] < 0


def test_update_host_state_can_enter_exploitation_mode_for_repeated_promising_signal() -> None:
    prev = default_host_state()
    prev['runs'] = 4
    prev['promise_score'] = 1.12
    prev['noise_score'] = 1.02
    prev['evidence_density'] = 0.66
    prev['novelty_score'] = 0.64
    prev['exploitation_score'] = 0.48
    prev['last_success_family'] = 'authz'
    result = update_host_state(
        host='api.example.com',
        family='authz',
        previous=prev,
        run_info={
            'promising': True,
            'workflow_promotable': True,
            'engine_status': 'ok',
            'success_criteria_eval': 'partial',
            'runtime_task': {
                'planning_ladder': {'current_stage': 'control_boundary_confirmation', 'next_stage': 'bounded_exploit_proof'},
                'planner_rationale': {'target_profile_summary': {'target_type': 'api'}, 'target_surface_rationale': ['authenticated_or_boundary_mapping']},
            },
            'runtime_utility': {'net_utility_score': 0.72},
            'decision_economics': {'priority_score': 0.44},
        },
    )
    hs = result.state
    assert hs['state'] == 'promising'
    assert hs['state_band'] == 'exploitation'
    assert hs['capability_state'] == 'exploit'
    assert hs['exploit_focus_family'] == 'authz'
    assert 'control_boundary_confirmation' in hs['preferred_stages']
    assert hs['exploitation_score'] > 0.65
    assert result.regeneration_reason == 'promising_exploitation_host_shift'
    assert 'host_entered_exploitation_mode' in result.reasons
    assert result.deltas['exploitation_score'] > 0
