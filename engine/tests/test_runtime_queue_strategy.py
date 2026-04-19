from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import learning_store
from runtime_queue_strategy import dynamic_family_boost, reprioritize_queues  # type: ignore
from runtime_archetype_inference import infer_runtime_archetypes  # type: ignore


def _attack_family(objective: str, target: str, task_family: str = '') -> str:
    return (task_family or 'generic').lower()


def test_dynamic_family_boost_applies_success_failure_and_toggle_bias() -> None:
    boosts = dynamic_family_boost(
        runs=[
            {'objective': 'Recon', 'target': 'https://a.example.com/', 'task_family': 'recon', 'engine_status': 'ok'},
            {'objective': 'Auth', 'target': 'https://b.example.com/', 'task_family': 'authz', 'engine_status': 'failed'},
        ],
        toggles={'family_lane_boost': ['authz'], 'family_lane_suppress': ['recon']},
        attack_family_fn=_attack_family,
    )
    assert boosts['authz'] > 1.0
    assert boosts['recon'] < 1.1


def test_dynamic_family_boost_relaxes_decay_for_dense_family_with_positive_yield_trend() -> None:
    runs = [
        {'objective': 'Auth', 'target': 'https://a.example.com/', 'task_family': 'authz', 'engine_status': 'failed'},
        {'objective': 'Auth', 'target': 'https://a.example.com/', 'task_family': 'authz', 'engine_status': 'ok', 'workflow_promotable': True, 'runtime_utility': {'net_utility_score': 0.7}, 'decision_economics': {'priority_score': 0.4}},
        {'objective': 'Auth', 'target': 'https://a.example.com/', 'task_family': 'authz', 'engine_status': 'ok', 'workflow_promotable': True, 'finding_lifecycle': 'probable', 'runtime_utility': {'net_utility_score': 0.9}, 'decision_economics': {'priority_score': 0.6}, 'signal_contract': {'success_outcome': {'status': 'partial'}}},
        {'objective': 'Auth', 'target': 'https://a.example.com/', 'task_family': 'authz', 'engine_status': 'ok', 'workflow_promotable': True, 'finding_lifecycle': 'confirmed', 'runtime_utility': {'net_utility_score': 1.0}, 'decision_economics': {'priority_score': 0.7}, 'signal_contract': {'success_outcome': {'status': 'met'}}},
        {'objective': 'Other', 'target': 'https://b.example.com/', 'task_family': 'recon', 'engine_status': 'ok'},
        {'objective': 'Other', 'target': 'https://c.example.com/', 'task_family': 'recon', 'engine_status': 'ok'},
    ]
    boosts = dynamic_family_boost(
        runs=runs,
        toggles={'family_decay_enabled': True, 'family_decay_window_runs': 6, 'family_decay_penalty': 0.2},
        attack_family_fn=_attack_family,
    )
    assert boosts['authz'] >= 1.0



def test_dynamic_family_boost_penalizes_dense_family_with_flat_noisy_trend() -> None:
    runs = [
        {'objective': 'Recon', 'target': 'https://a.example.com/', 'task_family': 'recon', 'engine_status': 'failed'},
        {'objective': 'Recon', 'target': 'https://a.example.com/', 'task_family': 'recon', 'engine_status': 'failed'},
        {'objective': 'Recon', 'target': 'https://a.example.com/', 'task_family': 'recon', 'engine_status': 'timeout'},
        {'objective': 'Recon', 'target': 'https://a.example.com/', 'task_family': 'recon', 'engine_status': 'error'},
        {'objective': 'Other', 'target': 'https://b.example.com/', 'task_family': 'authz', 'engine_status': 'ok'},
        {'objective': 'Other', 'target': 'https://c.example.com/', 'task_family': 'authz', 'engine_status': 'ok'},
    ]
    boosts = dynamic_family_boost(
        runs=runs,
        toggles={'family_decay_enabled': True, 'family_decay_window_runs': 6, 'family_decay_penalty': 0.2},
        attack_family_fn=_attack_family,
    )
    assert boosts['recon'] < 0.95



def test_dynamic_family_boost_ignores_learning_excluded_contaminated_runs() -> None:
    runs = [
        {'objective': 'Auth', 'target': 'https://a.example.com/', 'task_family': 'authz', 'engine_status': 'failed', 'run_contamination': {'learning_excluded': True}},
        {'objective': 'Auth', 'target': 'https://a.example.com/', 'task_family': 'authz', 'engine_status': 'failed', 'run_contamination': {'learning_excluded': True}},
        {'objective': 'Other', 'target': 'https://b.example.com/', 'task_family': 'recon', 'engine_status': 'ok'},
    ]
    boosts = dynamic_family_boost(
        runs=runs,
        toggles={'family_decay_enabled': True, 'family_decay_window_runs': 6, 'family_decay_penalty': 0.2},
        attack_family_fn=_attack_family,
    )
    assert boosts.get('authz', 1.0) == 1.0


def test_reprioritize_queues_sorts_higher_scored_task_first() -> None:
    followup_queue = [
        {'objective': 'Probe A', 'target': 'https://a.example.com/', 'task_family': 'recon', 'target_score': 1.0},
        {'objective': 'Probe B', 'target': 'https://b.example.com/', 'task_family': 'authz', 'target_score': 1.4},
    ]
    precision_queue = []
    reprioritize_queues(
        followup_queue=followup_queue,
        precision_queue=precision_queue,
        runs=[{'objective': 'Old', 'target': 'https://b.example.com/', 'task_family': 'authz', 'engine_status': 'ok', 'promising': True, 'finding_lifecycle': 'probable'}],
        toggles={},
        planner_hints_cache={},
        host_state={'hosts': {'b.example.com': {'promise_score': 1.2, 'noise_score': 1.0}}},
        host_family_owner_gate={},
        attack_family_fn=_attack_family,
        family_allowed_for_host_stage_fn=lambda host_state, target, fam: True,
        planner_vector_weight_fn=lambda task, hints: 1.0,
        host_from_target_fn=lambda target: target.split('//', 1)[-1].split('/')[0],
    )
    assert followup_queue[0]['target'] == 'https://b.example.com/'


def test_reprioritize_queues_uses_utility_score_when_present() -> None:
    followup_queue = [
        {'objective': 'Probe A', 'target': 'https://a.example.com/', 'task_family': 'recon', 'priority_score': 0.6, 'utility_score': 0.1},
        {'objective': 'Probe B', 'target': 'https://b.example.com/', 'task_family': 'authz', 'priority_score': 0.5, 'utility_score': 1.1},
    ]
    reprioritize_queues(
        followup_queue=followup_queue,
        precision_queue=[],
        runs=[],
        toggles={},
        planner_hints_cache={},
        host_state={'hosts': {}},
        host_family_owner_gate={},
        attack_family_fn=_attack_family,
        family_allowed_for_host_stage_fn=lambda host_state, target, fam: True,
        planner_vector_weight_fn=lambda task, hints: 1.0,
        host_from_target_fn=lambda target: target.split('//', 1)[-1].split('/')[0],
    )
    assert followup_queue[0]['target'] == 'https://b.example.com/'


def test_reprioritize_queues_respects_planner_execution_hints() -> None:
    followup_queue = [
        {
            'objective': 'Background static discovery',
            'target': 'https://cdn.example.com/',
            'task_family': 'content_discovery',
            'priority_score': 1.0,
            'priority_tier': 'low',
            'expected_depth': 'light',
            'activation_phase': 3,
            'activation_mode': 'background',
            'surface_role': 'background',
        },
        {
            'objective': 'Primary account authz validation',
            'target': 'https://api.example.com/',
            'task_family': 'authz',
            'priority_score': 1.0,
            'priority_tier': 'high',
            'expected_depth': 'deep',
            'activation_phase': 1,
            'activation_mode': 'immediate',
            'surface_role': 'primary',
        },
    ]
    reprioritize_queues(
        followup_queue=followup_queue,
        precision_queue=[],
        runs=[],
        toggles={},
        planner_hints_cache={},
        host_state={'hosts': {}},
        host_family_owner_gate={},
        attack_family_fn=_attack_family,
        family_allowed_for_host_stage_fn=lambda host_state, target, fam: True,
        planner_vector_weight_fn=lambda task, hints: 1.0,
        host_from_target_fn=lambda target: target.split('//', 1)[-1].split('/')[0],
    )
    assert followup_queue[0]['target'] == 'https://api.example.com/'
    assert followup_queue[0]['planner_execution_multiplier'] > followup_queue[1]['planner_execution_multiplier']


def test_reprioritize_queues_prefers_capability_lane_with_better_recent_yield() -> None:
    followup_queue = [
        {'objective': 'Probe A', 'target': 'https://a.example.com/', 'task_family': 'authz', 'priority_score': 1.0, 'capability_candidates': ['http_probe']},
        {'objective': 'Probe B', 'target': 'https://b.example.com/', 'task_family': 'authz', 'priority_score': 1.0, 'capability_candidates': ['response_diff']},
    ]
    runs = [
        {'objective': 'Old A', 'target': 'https://x.example.com/', 'task_family': 'authz', 'engine_status': 'ok', 'workflow_promotable': False, 'brain': {'capability': 'http_probe'}},
        {'objective': 'Old B', 'target': 'https://y.example.com/', 'task_family': 'authz', 'engine_status': 'ok', 'workflow_promotable': True, 'finding_lifecycle': 'probable', 'brain': {'capability': 'response_diff'}, 'runtime_utility': {'net_utility_score': 0.8}, 'decision_economics': {'priority_score': 0.7}},
    ]
    reprioritize_queues(
        followup_queue=followup_queue,
        precision_queue=[],
        runs=runs,
        toggles={},
        planner_hints_cache={},
        host_state={'hosts': {}},
        host_family_owner_gate={},
        attack_family_fn=_attack_family,
        family_allowed_for_host_stage_fn=lambda host_state, target, fam: True,
        planner_vector_weight_fn=lambda task, hints: 1.0,
        host_from_target_fn=lambda target: target.split('//', 1)[-1].split('/')[0],
    )
    assert followup_queue[0]['target'] == 'https://b.example.com/'
    assert followup_queue[0]['capability_lane'] == 'response_diff'


def test_infer_runtime_archetypes_returns_compact_canonical_shape() -> None:
    inferred = infer_runtime_archetypes(
        target_type='api',
        host='api.example.com',
        top_archetype_hints_fn=lambda **_kwargs: [
            {'archetype': 'api_first', 'score': 1.4},
            {'archetype': 'admin_surface', 'score': 1.1},
        ],
    )
    assert inferred['primary_archetype'] == 'api_first'
    assert inferred['archetypes'] == ['api_first', 'admin_surface']
    assert inferred['confidence'] == 1.4
    assert inferred['flags']['api_first'] is True
    assert inferred['flags']['admin_surface'] is True
    assert inferred['flags']['static_edge'] is False


def test_reprioritize_queues_prefers_exploitation_focus_family_on_hot_host() -> None:
    followup_queue = [
        {'objective': 'Probe Recon', 'target': 'https://api.example.com/', 'task_family': 'recon', 'priority_score': 1.0},
        {'objective': 'Probe Authz', 'target': 'https://api.example.com/', 'task_family': 'authz', 'priority_score': 1.0},
    ]
    reprioritize_queues(
        followup_queue=followup_queue,
        precision_queue=[],
        runs=[],
        toggles={},
        planner_hints_cache={},
        host_state={'hosts': {'api.example.com': {'state_band': 'exploitation', 'promise_score': 1.22, 'noise_score': 1.04, 'exploitation_score': 0.94, 'exploit_focus_family': 'authz'}}},
        host_family_owner_gate={},
        attack_family_fn=_attack_family,
        family_allowed_for_host_stage_fn=lambda host_state, target, fam: True,
        planner_vector_weight_fn=lambda task, hints: 1.0,
        host_from_target_fn=lambda target: target.split('//', 1)[-1].split('/')[0],
    )
    assert followup_queue[0]['task_family'] == 'authz'



def test_reprioritize_queues_applies_canonical_archetype_multiplier() -> None:
    followup_queue = [
        {'objective': 'Probe TLS', 'target': 'https://cdn.example.com/', 'task_family': 'tls_assessment', 'priority_score': 1.0, 'planner_rationale': {'target_profile_summary': {'target_type': 'static'}}},
        {'objective': 'Probe Authz', 'target': 'https://api.example.com/', 'task_family': 'authz', 'priority_score': 1.0, 'planner_rationale': {'target_profile_summary': {'target_type': 'api'}}},
    ]
    learning_store.update_learning('cdn.example.com', 'tls_assessment', 'medium', True, 'ok', target_type='static', archetypes=['static_edge'])
    learning_store.update_learning('api.example.com', 'authz', 'medium', True, 'ok', target_type='api', archetypes=['api_first'])
    reprioritize_queues(
        followup_queue=followup_queue,
        precision_queue=[],
        runs=[],
        toggles={},
        planner_hints_cache={},
        host_state={'hosts': {}},
        host_family_owner_gate={},
        attack_family_fn=_attack_family,
        family_allowed_for_host_stage_fn=lambda host_state, target, fam: True,
        planner_vector_weight_fn=lambda task, hints: 1.0,
        host_from_target_fn=lambda target: target.split('//', 1)[-1].split('/')[0],
    )
    assert followup_queue[0]['target'] in {'https://cdn.example.com/', 'https://api.example.com/'}
    assert followup_queue[0]['archetype_multiplier'] >= 1.05
    assert followup_queue[1]['archetype_multiplier'] >= 1.05


def test_reprioritize_queues_prefers_preferred_stage_over_family_focus_when_available() -> None:
    followup_queue = [
        {
            'objective': 'Probe Recon',
            'target': 'https://api.example.com/',
            'task_family': 'recon',
            'priority_score': 1.0,
            'planning_ladder': {'current_stage': 'discovery', 'next_stage': 'validation'},
            'planner_rationale': {'target_surface_rationale': ['authenticated_or_boundary_mapping']},
        },
        {
            'objective': 'Probe Authz',
            'target': 'https://api.example.com/',
            'task_family': 'authz',
            'priority_score': 1.0,
            'planning_ladder': {'current_stage': 'control_boundary_confirmation', 'next_stage': 'bounded_exploit_proof'},
            'planner_rationale': {'target_surface_rationale': ['authenticated_or_boundary_mapping']},
        },
    ]
    reprioritize_queues(
        followup_queue=followup_queue,
        precision_queue=[],
        runs=[],
        toggles={},
        planner_hints_cache={},
        host_state={'hosts': {'api.example.com': {'state_band': 'exploitation', 'promise_score': 1.22, 'noise_score': 1.04, 'exploitation_score': 0.94, 'exploit_focus_family': 'recon', 'preferred_stages': ['control_boundary_confirmation', 'bounded_exploit_proof'], 'target_surface_rationale': ['authenticated_or_boundary_mapping']}}},
        host_family_owner_gate={},
        attack_family_fn=_attack_family,
        family_allowed_for_host_stage_fn=lambda host_state, target, fam: True,
        planner_vector_weight_fn=lambda task, hints: 1.0,
        host_from_target_fn=lambda target: target.split('//', 1)[-1].split('/')[0],
    )
    assert followup_queue[0]['task_family'] == 'authz'



def test_reprioritize_queues_ignores_contaminated_family_history_when_scoring() -> None:
    followup_queue = [
        {'objective': 'Probe Authz', 'target': 'https://api.example.com/', 'task_family': 'authz', 'priority_score': 1.0},
        {'objective': 'Probe Recon', 'target': 'https://api.example.com/', 'task_family': 'recon', 'priority_score': 1.0},
    ]
    runs = [
        {'objective': 'Auth old', 'target': 'https://api.example.com/', 'task_family': 'authz', 'engine_status': 'failed', 'run_contamination': {'learning_excluded': True}},
        {'objective': 'Recon old', 'target': 'https://api.example.com/', 'task_family': 'recon', 'engine_status': 'ok', 'workflow_promotable': True, 'runtime_utility': {'net_utility_score': 0.8}, 'decision_economics': {'priority_score': 0.5}},
    ]
    reprioritize_queues(
        followup_queue=followup_queue,
        precision_queue=[],
        runs=runs,
        toggles={},
        planner_hints_cache={},
        host_state={'hosts': {}},
        host_family_owner_gate={},
        attack_family_fn=_attack_family,
        family_allowed_for_host_stage_fn=lambda host_state, target, fam: True,
        planner_vector_weight_fn=lambda task, hints: 1.0,
        host_from_target_fn=lambda target: target.split('//', 1)[-1].split('/')[0],
    )
    assert followup_queue[0]['task_family'] == 'recon'



def test_reprioritize_queues_uses_transition_prior_multiplier_for_matching_task(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(learning_store, 'LEARNING_PATH', tmp_path / 'learning_store.json')
    learning_store.update_learning(
        'api.example.com',
        'authz',
        'medium',
        True,
        'ok',
        capability='http_probe',
        action_type='differential_probe',
        next_stage='bounded_exploit_proof',
        next_action_type='confirm_probe',
    )
    followup_queue = [
        {
            'objective': 'Authz followup',
            'target': 'https://api.example.com/proof',
            'task_family': 'authz',
            'priority_score': 1.0,
            'capability': 'http_probe',
            'action_type': 'differential_probe',
            'planning_ladder': {'next_stage': 'bounded_exploit_proof'},
        },
        {
            'objective': 'Recon followup',
            'target': 'https://api.example.com/recon',
            'task_family': 'recon',
            'priority_score': 1.0,
            'capability': 'fingerprinting',
            'action_type': 'fingerprint_probe',
            'planning_ladder': {'next_stage': 'validation'},
        },
    ]
    reprioritize_queues(
        followup_queue=followup_queue,
        precision_queue=[],
        runs=[],
        toggles={},
        planner_hints_cache={},
        host_state={'hosts': {}},
        host_family_owner_gate={},
        attack_family_fn=_attack_family,
        family_allowed_for_host_stage_fn=lambda host_state, target, fam: True,
        planner_vector_weight_fn=lambda task, hints: 1.0,
        host_from_target_fn=lambda target: target.split('//', 1)[-1].split('/')[0],
    )
    assert followup_queue[0]['task_family'] == 'authz'
    assert followup_queue[0]['transition_prior_multiplier'] > 1.0
    assert followup_queue[0]['transition_prior_actions'] == ['confirm_probe']



def test_reprioritize_queues_uses_branch_state_multiplier_for_stronger_branch_candidate() -> None:
    followup_queue = [
        {
            'target': 'https://api.example.com/defer',
            'task_family': 'recon',
            'mode': 'followup',
            'priority_score': 1.0,
            'utility_score': 1.0,
            'branch_state': 'continuation',
            'branch_action': 'defer',
            'branch_reason': 'insufficient_branch_evidence',
            'branch_evidence_score': 0.05,
            'runtime_task': {'cost_band': 'medium'},
        },
        {
            'target': 'https://api.example.com/proof',
            'task_family': 'authz',
            'mode': 'followup',
            'priority_score': 1.0,
            'utility_score': 1.0,
            'branch_state': 'branch_candidate',
            'branch_action': 'deepen',
            'branch_reason': 'proof_path_ready',
            'branch_evidence_score': 0.8,
            'runtime_task': {'cost_band': 'medium'},
        },
    ]
    reprioritize_queues(
        followup_queue=followup_queue,
        precision_queue=[],
        host_state={},
        toggles={},
    )
    assert followup_queue[0]['target'].endswith('/proof')
    assert followup_queue[0]['branch_state_multiplier'] > followup_queue[1]['branch_state_multiplier']
    assert followup_queue[0]['branch_reason_scored'] == 'proof_path_ready'



def test_reprioritize_queues_uses_branch_history_to_suppress_dead_end_paths(tmp_path, monkeypatch) -> None:
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
        branch_lifecycle_status='dead_end',
        branch_lifecycle_reason='negative_or_failed_branch_outcome',
        branch_thread_key='authz::bounded_exploit_proof::deepen::proof_path_ready',
        branch_thread_label='authz:bounded_exploit_proof:deepen',
    )
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
        branch_lifecycle_status='dead_end',
        branch_lifecycle_reason='negative_or_failed_branch_outcome',
        branch_thread_key='authz::bounded_exploit_proof::deepen::proof_path_ready',
        branch_thread_label='authz:bounded_exploit_proof:deepen',
    )
    followup_queue = [
        {
            'target': 'https://api.example.com/proof',
            'task_family': 'authz',
            'mode': 'followup',
            'priority_score': 1.0,
            'utility_score': 1.0,
            'branch_state': 'branch_candidate',
            'branch_action': 'deepen',
            'branch_reason': 'proof_path_ready',
            'planning_ladder': {'next_stage': 'bounded_exploit_proof'},
            'runtime_task': {'cost_band': 'medium'},
        },
        {
            'target': 'https://api.example.com/confirm',
            'task_family': 'authz',
            'mode': 'followup',
            'priority_score': 1.0,
            'utility_score': 1.0,
            'branch_state': 'branch_candidate',
            'branch_action': 'confirm',
            'branch_reason': 'confirmation_gap',
            'planning_ladder': {'next_stage': 'control_boundary_confirmation'},
            'runtime_task': {'cost_band': 'medium'},
        },
    ]
    reprioritize_queues(
        followup_queue=followup_queue,
        precision_queue=[],
        host_state={},
        toggles={},
        host_from_target_fn=lambda target: target.split('//', 1)[-1].split('/')[0],
    )
    assert followup_queue[0]['target'].endswith('/confirm')
    suppressed = next(item for item in followup_queue if item['target'].endswith('/proof'))
    assert suppressed['branch_history_multiplier'] < 1.0
    assert 'proof_path_ready' in suppressed['branch_history_reasons']
    assert 'authz:bounded_exploit_proof:deepen' in suppressed['branch_history_reasons']



def test_reprioritize_queues_boosts_bounded_exploit_proof_semantics() -> None:
    followup_queue = [
        {
            'target': 'https://api.example.com/discovery',
            'task_family': 'recon',
            'mode': 'followup',
            'priority_score': 1.0,
            'utility_score': 1.0,
            'runtime_task': {'cost_band': 'medium'},
            'exploit_ladder': {'stage': 'discovery'},
        },
        {
            'target': 'https://api.example.com/proof',
            'task_family': 'authz',
            'mode': 'followup',
            'priority_score': 1.0,
            'utility_score': 1.0,
            'runtime_task': {'cost_band': 'medium'},
            'exploit_ladder': {'stage': 'bounded_exploit_proof'},
            'actor_requirements': {'differential': True},
            'session_requirements': {'auth_context': True},
            'promotion_policy': {'confirm_preferred': True},
            'approval_sensitivity': {'auth_sensitive': True},
        },
    ]
    reprioritize_queues(
        followup_queue=followup_queue,
        precision_queue=[],
        host_state={},
        family_yield={},
        host_success_count={},
        host_fail_count={},
        high_signal_targets={},
        family_empirical_score={},
        host_tool_hints={},
        toggles={},
    )
    assert followup_queue[0]['target'].endswith('/proof')
    assert followup_queue[0]['semantic_multiplier'] > followup_queue[1]['semantic_multiplier']


def test_reprioritize_queues_boosts_target_surface_and_ladder_rationale() -> None:
    followup_queue = [
        {
            'target': 'https://static.example.com/report',
            'task_family': 'tls_assessment',
            'mode': 'followup',
            'priority_score': 1.0,
            'utility_score': 1.0,
            'planner_rationale': {
                'target_profile_summary': {'target_type': 'static'},
                'recommended_progression': ['artifact_capture', 'report_artifact_capture'],
                'target_surface_rationale': ['artifact_capture'],
            },
            'planning_ladder': {'current_stage': 'discovery', 'next_stage': 'report_artifact_capture'},
            'followup_evidence_focus': ['exposure_artifact'],
            'runtime_task': {'cost_band': 'medium'},
            'exploit_ladder': {'stage': 'discovery'},
        },
        {
            'target': 'https://api.example.com/recon',
            'task_family': 'recon',
            'mode': 'followup',
            'priority_score': 1.0,
            'utility_score': 1.0,
            'planner_rationale': {
                'target_profile_summary': {'target_type': 'api'},
                'recommended_progression': ['authenticated_or_boundary_mapping', 'validation'],
                'target_surface_rationale': ['authenticated_or_boundary_mapping'],
            },
            'planning_ladder': {'current_stage': 'discovery', 'next_stage': 'validation'},
            'runtime_task': {'cost_band': 'medium'},
            'exploit_ladder': {'stage': 'discovery'},
        },
    ]
    reprioritize_queues(
        followup_queue=followup_queue,
        precision_queue=[],
        host_state={},
        family_yield={},
        host_success_count={},
        host_fail_count={},
        high_signal_targets={},
        family_empirical_score={},
        host_tool_hints={},
        toggles={},
    )
    assert followup_queue[0]['target'].endswith('/report')
    assert followup_queue[0]['semantic_multiplier'] > followup_queue[1]['semantic_multiplier']



def test_reprioritize_queues_uses_archetype_multiplier_for_matching_host_context(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(learning_store, 'LEARNING_PATH', tmp_path / 'learning_store.json')
    learning_store.update_learning(
        'api.example.com',
        'authz',
        'medium',
        True,
        'ok',
        target_type='api',
        target_surface_rationale=['authenticated_or_boundary_mapping', 'admin'],
    )
    followup_queue = [
        {
            'target': 'https://static.example.com/report',
            'task_family': 'tls_assessment',
            'mode': 'followup',
            'priority_score': 1.0,
            'utility_score': 1.0,
            'planner_rationale': {'target_profile_summary': {'target_type': 'static'}},
            'runtime_task': {'cost_band': 'medium'},
        },
        {
            'target': 'https://api.example.com/proof',
            'task_family': 'authz',
            'mode': 'followup',
            'priority_score': 1.0,
            'utility_score': 1.0,
            'planner_rationale': {'target_profile_summary': {'target_type': 'api'}},
            'runtime_task': {'cost_band': 'medium'},
        },
    ]
    reprioritize_queues(
        followup_queue=followup_queue,
        precision_queue=[],
        host_state={},
        toggles={},
        host_from_target_fn=lambda target: target.split('//', 1)[-1].split('/')[0],
    )
    assert followup_queue[0]['target'].endswith('/proof')
    assert followup_queue[0]['archetype_multiplier'] > followup_queue[1]['archetype_multiplier']
    assert 'auth_heavy' in followup_queue[0]['archetype_hints']
    assert followup_queue[0]['archetype_primary'] == 'auth_heavy'
    assert followup_queue[0]['archetype_confidence'] > 0.0



def test_reprioritize_queues_penalizes_unresolved_stateful_prerequisites() -> None:
    followup_queue = [
        {
            'target': 'https://api.example.com/ready',
            'task_family': 'workflow',
            'mode': 'followup',
            'priority_score': 1.0,
            'utility_score': 1.0,
            'runtime_task': {'cost_band': 'medium'},
            'exploit_ladder': {'stage': 'state_transition_confirmation'},
            'session_requirements': {'stateful': True, 'prerequisites': ['capture workflow state markers']},
            'open_questions': [],
        },
        {
            'target': 'https://api.example.com/blocked',
            'task_family': 'workflow',
            'mode': 'followup',
            'priority_score': 1.0,
            'utility_score': 1.0,
            'runtime_task': {'cost_band': 'medium'},
            'exploit_ladder': {'stage': 'state_transition_confirmation'},
            'session_requirements': {'stateful': True, 'prerequisites': ['capture workflow state markers']},
            'open_questions': ['capture workflow state markers'],
        },
    ]
    reprioritize_queues(
        followup_queue=followup_queue,
        precision_queue=[],
        host_state={},
        family_yield={},
        host_success_count={},
        host_fail_count={},
        high_signal_targets={},
        family_empirical_score={},
        host_tool_hints={},
        toggles={},
    )
    assert followup_queue[0]['target'].endswith('/ready')
    assert followup_queue[0]['semantic_multiplier'] > followup_queue[1]['semantic_multiplier']
