from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import learning_store  # type: ignore


def test_infer_archetypes_maps_compact_operational_categories() -> None:
    out = learning_store.infer_archetypes(
        target_type='api',
        target_surface_rationale=['authenticated_or_boundary_mapping', 'admin', 'tenant'],
        family='workflow',
        next_stage='bounded_exploit_proof',
    )
    assert 'auth_heavy' in out
    assert 'api_first' in out
    assert 'workflow_app' in out


def test_learning_store_tracks_capability_tool_and_host_stage(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(learning_store, 'LEARNING_PATH', tmp_path / 'learning_store.json')
    learning_store.update_learning(
        'api.example.com',
        'authz',
        'medium',
        True,
        'ok',
        capability='http_probe',
        tool='curl',
        action_type='differential_probe',
        host_stage='active_validation',
        planning_stage='control_boundary_confirmation',
        next_stage='bounded_exploit_proof',
        next_action_type='confirm_probe',
        next_family='authz',
        reconsult_tier='structural',
        target_type='api',
        target_surface_rationale=['authenticated_or_boundary_mapping', 'account'],
    )
    summary = learning_store.summarize_learning(limit=3)
    assert summary['top_families'][0]['family'] == 'authz'
    assert summary['top_capabilities'][0]['capability'] == 'http_probe'
    assert summary['top_family_capabilities'][0]['family_capability'] == 'authz::http_probe'
    assert summary['top_host_capability_pairs'][0]['host_capability'] == 'api.example.com::http_probe'
    assert summary['top_tools'][0]['tool'] == 'curl'
    assert summary['top_action_types'][0]['action_type'] == 'differential_probe'
    assert summary['top_host_stages'][0]['host_stage'] == 'active_validation'
    assert summary['top_planning_stages'][0]['planning_stage'] == 'control_boundary_confirmation'
    assert summary['top_next_stages'][0]['next_stage'] == 'bounded_exploit_proof'
    assert summary['top_target_types'][0]['target_type'] == 'api'
    assert summary['top_target_surface_signals'][0]['target_surface_signal'] == 'authenticated_or_boundary_mapping'
    assert summary['top_transitions'][0]['transition'] == 'authz::http_probe::differential_probe::bounded_exploit_proof::confirm_probe'
    assert summary['top_host_transitions'][0]['host_transition'] == 'api.example.com::authz::http_probe::differential_probe::bounded_exploit_proof::confirm_probe'
    assert summary['top_progression_priors'][0]['progression'] == 'authz::api::authenticated_or_boundary_mapping|account::bounded_exploit_proof::authz::structural'
    assert summary['top_host_progression_priors'][0]['host_progression'] == 'api.example.com::authz::api::authenticated_or_boundary_mapping|account::bounded_exploit_proof::authz::structural'
    assert summary['top_archetype_priors'][0]['archetype_key'] == 'api::auth_heavy'
    assert summary['top_host_archetype_priors'][0]['host_archetype_key'] == 'api.example.com::api::auth_heavy'


def test_summarize_branch_threads_groups_thread_identity_with_pressure() -> None:
    learning_store._save({
        'branch_priors': {
            'k1': {
                'branch_thread_key': 'authz::bounded_exploit_proof::deepen::proof_path_ready',
                'branch_thread_label': 'authz:bounded_exploit_proof:deepen',
                'branch_action': 'deepen',
                'branch_reason': 'proof_path_ready',
                'next_stage': 'bounded_exploit_proof',
                'productive': 2,
                'dead_end': 1,
                'seen': 3,
                'branch_lifecycle_status': 'productive',
            },
            'k2': {
                'branch_thread_key': 'authz::bounded_exploit_proof::deepen::proof_path_ready',
                'branch_thread_label': 'authz:bounded_exploit_proof:deepen',
                'branch_action': 'deepen',
                'branch_reason': 'proof_path_ready',
                'next_stage': 'bounded_exploit_proof',
                'productive': 1,
                'dead_end': 2,
                'seen': 3,
                'branch_lifecycle_status': 'dead_end',
            },
        }
    })
    out = learning_store.summarize_branch_threads(limit=3)
    assert out[0]['branch_thread_key'] == 'authz::bounded_exploit_proof::deepen::proof_path_ready'
    assert out[0]['branch_thread_label'] == 'authz:bounded_exploit_proof:deepen'
    assert out[0]['productive'] == 3
    assert out[0]['dead_end'] == 3
    assert out[0]['seen'] == 6
    assert out[0]['dominant_lifecycle_status'] in {'productive', 'dead_end'}


def test_learning_store_tracks_branch_priors_and_dead_end_history(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(learning_store, 'LEARNING_PATH', tmp_path / 'learning_store.json')
    learning_store.update_learning(
        'api.example.com',
        'authz',
        'medium',
        False,
        'not_met',
        next_stage='bounded_exploit_proof',
        branch_state='branch_candidate',
        branch_action='deepen',
        branch_reason='proof_path_ready',
        branch_outcome='dead_end',
    )
    learning_store.update_learning(
        'api.example.com',
        'authz',
        'medium',
        True,
        'ok',
        next_stage='bounded_exploit_proof',
        branch_state='branch_candidate',
        branch_action='deepen',
        branch_reason='proof_path_ready',
        branch_outcome='productive',
        branch_thread_key='authz::bounded_exploit_proof::deepen::proof_path_ready',
        branch_thread_label='authz:bounded_exploit_proof:deepen',
    )
    summary = learning_store.summarize_learning(limit=3)
    assert any(item['branch_key'].startswith('branch_candidate::deepen::proof_path_ready::bounded_exploit_proof::') for item in summary['top_branch_priors'])
    assert any(item['host_branch_key'].startswith('api.example.com::branch_candidate::deepen::proof_path_ready::bounded_exploit_proof::') for item in summary['top_host_branch_priors'])
    hints = learning_store.top_branch_hints(
        branch_state='branch_candidate',
        branch_action='deepen',
        branch_reason='proof_path_ready',
        next_stage='bounded_exploit_proof',
        host='api.example.com',
        limit=2,
    )
    assert hints
    assert hints[0]['branch_reason'] == 'proof_path_ready'
    assert any(item['branch_outcome'] in {'dead_end', 'productive'} for item in hints)
    assert any(item['branch_lifecycle_status'] in {'dead_end', 'productive'} for item in hints)
    assert any(item['branch_thread_key'] for item in hints)
    assert any(item['branch_thread_key'] == 'authz::bounded_exploit_proof::deepen::proof_path_ready' for item in summary['top_branch_threads'])
