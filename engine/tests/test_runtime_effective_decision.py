from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import learning_store
from runtime_effective_decision import apply_effective_decision, branch_lifecycle, branch_thread_identity  # type: ignore


BASE_KWARGS = {
    'task': {'name': 'Task', 'task_family': 'authz'},
    'result': {},
    'qual': {'vuln_class': 'idor', 'verdict': 'probable'},
    'classification': 'medium',
    'auditor': 'approve',
    'engine_status': 'ok',
    'success_eval_status': 'partial',
    'summary_text': 'partial signal',
    'reason_code': 'interesting_signal',
    'target': 'https://api.example.com/',
    'objective': 'Probe',
    'aggression': 5,
    'owner_auth': False,
    'owner_override': False,
    'retry_counts': {},
    'retry_limit': 2,
    'followup_queue': [],
    'followup_counts': {},
    'followup_recent': {},
    'max_followups_per_target': 2,
    'scheduled_keys': set(),
    'host_weak_count': {'api.example.com': 2},
    'host_family_owner_gate': {},
    'confirm_counts': {},
    'confirm_recent': {},
    'confirm_total': 0,
    'confirm_class_counts': {},
    'max_confirm_jobs_per_target': 2,
    'max_confirm_jobs_total': 5,
    'max_confirm_jobs_per_class': 5,
    'confirm_job_cooldown_sec': 900,
    'quality_telemetry': {},
    'toggles': {'enable_confirm_jobs': True, 'enable_followups': True, 'followup_cooldown_sec': 900},
    'promising': True,
    'signal_contract': {},
    'runtime_decision': {'intent_flags': {'retry': False, 'confirm': False, 'followup': False, 'precision': False}},
    'dedup_key_fn': lambda objective, target: (objective, target),
    'attack_family_fn': lambda objective, target, family='': family or 'authz',
    'host_from_target_fn': lambda target: 'api.example.com',
    'next_followup_family_fn': lambda family, result: family or 'authz',
    'clamp_aggression_fn': lambda n: n,
    'capped_aggression_fn': lambda family, target, aggression: aggression,
    'adaptive_aggression_fn': lambda aggression, classification, reason_code, owner_override: aggression,
    'post_run_decision_fn': lambda *args, **kwargs: {'retry': False, 'confirm': False, 'followup': False, 'precision': False},
    'log_event_fn': lambda *args, **kwargs: None,
}


def _kwargs(**overrides):
    data = {}
    for k, v in BASE_KWARGS.items():
        if isinstance(v, dict):
            data[k] = dict(v)
        elif isinstance(v, list):
            data[k] = list(v)
        elif isinstance(v, set):
            data[k] = set(v)
        else:
            data[k] = v
    data['enqueue_followup_task_fn'] = lambda task, high_priority=False, _queue=data['followup_queue']: _queue.append(dict(task, high_priority=high_priority))
    data.update(overrides)
    return data


def test_effective_decision_returns_noop_when_no_intent_flags() -> None:
    confirm_total, effective = apply_effective_decision(**_kwargs())
    assert confirm_total == 0
    assert effective['effective_status'] == 'noop'
    assert effective['effective_flags'] == {'retry': False, 'confirm': False, 'followup': False, 'precision': False}


def test_effective_decision_returns_blocked_when_confirm_duplicate_suppressed_without_side_effects() -> None:
    runtime_decision = {'intent_flags': {'retry': False, 'confirm': True, 'followup': False, 'precision': False}}
    kwargs = _kwargs(
        runtime_decision=runtime_decision,
        scheduled_keys={('Probe [CONFIRM:idor]', 'https://api.example.com/')},
    )
    confirm_total, effective = apply_effective_decision(**kwargs)
    assert confirm_total == 0
    assert effective['effective_status'] == 'blocked'
    assert effective['effective_flags']['confirm'] is False
    assert effective['effective_blockers']['confirm'] == ['confirm_duplicate_suppressed']
    assert kwargs['confirm_counts'] == {}
    assert kwargs['confirm_recent'] == {}


def test_effective_decision_returns_blocked_when_followup_duplicate_suppressed_without_side_effects() -> None:
    runtime_decision = {'intent_flags': {'retry': False, 'confirm': False, 'followup': True, 'precision': False}}
    kwargs = _kwargs(
        runtime_decision=runtime_decision,
        scheduled_keys={('Probe [FOLLOWUP:medium]', 'https://api.example.com/')},
    )
    _confirm_total, effective = apply_effective_decision(**kwargs)
    assert effective['effective_status'] == 'blocked'
    assert effective['effective_flags']['followup'] is False
    assert effective['effective_blockers']['followup'] == ['followup_duplicate_suppressed']
    assert kwargs['followup_counts'] == {}
    assert kwargs['followup_recent'] == {}


def test_effective_decision_returns_applied_when_followup_queued() -> None:
    runtime_decision = {'intent_flags': {'retry': False, 'confirm': False, 'followup': True, 'precision': False}}
    kwargs = _kwargs(runtime_decision=runtime_decision)
    _confirm_total, effective = apply_effective_decision(**kwargs)
    assert effective['effective_status'] == 'applied'
    assert effective['effective_flags']['followup'] is True
    assert kwargs['followup_counts']['https://api.example.com/'.strip().lower()] == 1
    assert len(kwargs['followup_queue']) == 1


def test_effective_decision_returns_partial_when_retry_queued_but_followup_blocked() -> None:
    runtime_decision = {'intent_flags': {'retry': True, 'confirm': False, 'followup': True, 'precision': False}}
    kwargs = _kwargs(runtime_decision=runtime_decision, promising=False)
    _confirm_total, effective = apply_effective_decision(**kwargs)
    assert effective['effective_status'] == 'partial'
    assert effective['effective_flags']['retry'] is True
    assert effective['effective_flags']['followup'] is False
    assert effective['effective_blockers']['followup'] == ['workflow_not_promotable:none']


def test_effective_decision_prefers_selected_primary_action_over_raw_intent_flags() -> None:
    runtime_decision = {
        'selected_primary_action': 'confirm',
        'intent_flags': {'retry': False, 'confirm': True, 'followup': True, 'precision': False},
        'economics': {'priority_score': 0.9},
    }
    kwargs = _kwargs(runtime_decision=runtime_decision)
    confirm_total, effective = apply_effective_decision(**kwargs)
    assert confirm_total == 1
    assert effective['effective_flags']['confirm'] is True
    assert effective['effective_flags']['followup'] is False
    assert kwargs['followup_queue'][0]['priority_score'] == 0.9


def test_effective_decision_uses_signal_contract_for_followup_gate() -> None:
    runtime_decision = {'intent_flags': {'retry': False, 'confirm': False, 'followup': True, 'precision': False}}
    kwargs = _kwargs(
        runtime_decision=runtime_decision,
        promising=False,
        signal_contract={
            'workflow_promotion': {'status': 'promotable'},
            'success_outcome': {'status': 'partial'},
        },
    )
    _confirm_total, effective = apply_effective_decision(**kwargs)
    assert effective['effective_status'] == 'applied'
    assert effective['effective_flags']['followup'] is True
    assert len(kwargs['followup_queue']) == 1


def test_effective_decision_preserves_capability_metadata_on_followup_queue() -> None:
    runtime_decision = {'intent_flags': {'retry': False, 'confirm': False, 'followup': True, 'precision': False}}
    kwargs = _kwargs(
        runtime_decision=runtime_decision,
        task={
            'name': 'Task',
            'task_family': 'authz',
            'capability_candidates': ['http_probe', 'response_diff'],
            'recommended_action_types': ['differential_probe'],
            'hypothesis_candidates': ['idor'],
            'planner_constraints': {'campaign_bound_context': True},
            'planner_preferences': {'preferred_vector_families': ['authz']},
            'open_questions': ['role inheritance unclear'],
            'success_semantics': {'success_model': 'differential_or_stateful_signal', 'success_gap': 'missing_success_criteria'},
            'experiment_intent_id': 'intent-authz-1',
        },
        signal_contract={
            'workflow_promotion': {'status': 'promotable'},
            'success_outcome': {'status': 'partial'},
        },
    )
    _confirm_total, effective = apply_effective_decision(**kwargs)
    assert effective['effective_flags']['followup'] is True
    queued = kwargs['followup_queue'][0]
    assert queued['experiment_intent_id'] == 'intent-authz-1'
    assert queued['capability_candidates'] == ['http_probe', 'response_diff']
    assert queued['recommended_action_types'][:2] == ['differential_probe', 'state_transition_probe']
    assert queued['success_semantics']['success_model'] == 'differential_or_stateful_signal'
    assert queued['planner_preferences']['followup_strategy'] == 'evidence_gap_first'
    assert queued['planner_preferences']['evidence_lane'] == 'authz_boundary'
    assert queued['followup_evidence_gap'] == 'missing_success_criteria'
    assert 'evidence_gap:missing_success_criteria' in queued['open_questions']
    assert 'evidence_lane:authz_boundary' in queued['open_questions']


def test_effective_decision_allows_evidence_bearing_followup_bridge_when_success_not_partial() -> None:
    runtime_decision = {
        'selected_primary_action': 'followup',
        'intent_flags': {'retry': False, 'confirm': False, 'followup': True, 'precision': False},
    }
    kwargs = _kwargs(
        runtime_decision=runtime_decision,
        success_eval_status='not_met',
        qual={'vuln_class': 'idor', 'verdict': 'weak_signal', 'false_positive_guards_passed': True},
        signal_contract={
            'workflow_promotion': {'status': 'promotable'},
            'success_outcome': {'status': 'not_met'},
            'finding_signal': {'status': 'weak', 'evidence_bearing': True},
        },
    )
    _confirm_total, effective = apply_effective_decision(**kwargs)
    assert effective['effective_status'] == 'applied'
    assert effective['effective_flags']['followup'] is True
    assert len(kwargs['followup_queue']) == 1


def test_effective_decision_uses_transition_memory_to_frontload_followup_actions(tmp_path, monkeypatch) -> None:
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
    runtime_decision = {'intent_flags': {'retry': False, 'confirm': False, 'followup': True, 'precision': False}}
    kwargs = _kwargs(
        runtime_decision=runtime_decision,
        task={
            'name': 'Task',
            'task_family': 'authz',
            'target': 'https://api.example.com/',
            'capability': 'http_probe',
            'action_type': 'differential_probe',
            'recommended_action_types': ['differential_probe'],
            'planning_ladder': {'next_stage': 'bounded_exploit_proof'},
            'success_semantics': {
                'success_model': 'differential_or_stateful_signal',
                'success_gap': 'missing_success_criteria',
            },
        },
        signal_contract={
            'workflow_promotion': {'status': 'promotable'},
            'success_outcome': {'status': 'partial'},
        },
    )
    _confirm_total, effective = apply_effective_decision(**kwargs)
    queued = kwargs['followup_queue'][0]
    assert effective['effective_flags']['followup'] is True
    assert queued['recommended_action_types'][0] == 'confirm_probe'
    assert queued['planner_preferences']['transition_prior_strategy'] == 'learning_store_transition_memory'
    assert queued['planner_preferences']['transition_prior_actions'] == ['confirm_probe']



def test_effective_decision_guides_inventory_growth_families_with_enumeration_first() -> None:
    runtime_decision = {'intent_flags': {'retry': False, 'confirm': False, 'followup': True, 'precision': False}}
    kwargs = _kwargs(
        runtime_decision=runtime_decision,
        task={
            'name': 'Content Discovery',
            'task_family': 'content_discovery',
            'recommended_action_types': ['confirmatory_probe'],
            'success_semantics': {
                'success_model': 'surface_expansion',
                'typed_family_eval': 'inventory_growth',
                'success_gap': 'need_reproducible_inventory_growth_evidence',
                'evidence_required': ['endpoint_or_header_inventory'],
            },
        },
        signal_contract={
            'workflow_promotion': {'status': 'promotable'},
            'success_outcome': {'status': 'partial', 'gap': 'need_reproducible_inventory_growth_evidence', 'typed_family_eval': 'inventory_growth'},
        },
    )
    _confirm_total, effective = apply_effective_decision(**kwargs)
    queued = kwargs['followup_queue'][0]
    assert effective['effective_flags']['followup'] is True
    assert queued['recommended_action_types'][:2] == ['enumeration_probe', 'fingerprint_probe']
    assert queued['planner_preferences']['evidence_lane'] == 'inventory_growth'



def test_effective_decision_uses_typed_family_eval_to_upgrade_recon_into_authz_boundary_guidance() -> None:
    runtime_decision = {'intent_flags': {'retry': False, 'confirm': False, 'followup': True, 'precision': False}}
    kwargs = _kwargs(
        runtime_decision=runtime_decision,
        task={
            'name': 'Recon with auth semantics',
            'task_family': 'recon',
            'recommended_action_types': ['enumeration_probe'],
            'success_semantics': {
                'typed_family_eval': 'authz_boundary',
                'success_model': 'differential_or_stateful_signal',
                'success_gap': 'need_clear_allow_deny_or_boundary_evidence',
                'evidence_required': ['http_status', 'response_diff'],
                'acceptance_checks': ['negative_control'],
            },
        },
        signal_contract={
            'workflow_promotion': {'status': 'promotable'},
            'success_outcome': {'status': 'partial', 'gap': 'need_clear_allow_deny_or_boundary_evidence', 'typed_family_eval': 'authz_boundary'},
        },
    )
    _confirm_total, effective = apply_effective_decision(**kwargs)
    queued = kwargs['followup_queue'][0]
    assert effective['effective_flags']['followup'] is True
    assert queued['recommended_action_types'][:3] == ['differential_probe', 'confirmatory_probe', 'state_transition_probe']
    assert queued['planner_preferences']['evidence_lane'] == 'authz_boundary'
    assert 'evidence_lane:authz_boundary' in queued['open_questions']



def test_effective_decision_guides_exposure_families_with_fingerprint_lane() -> None:
    runtime_decision = {'intent_flags': {'retry': False, 'confirm': False, 'followup': False, 'precision': True}}
    kwargs = _kwargs(
        runtime_decision=runtime_decision,
        task={
            'name': 'TLS Posture',
            'task_family': 'tls_assessment',
            'recommended_action_types': ['confirmatory_probe'],
            'success_semantics': {
                'success_model': 'fingerprint_or_exposure_signal',
                'success_gap': 'need_stronger_repro_or_impact_evidence',
            },
        },
        signal_contract={
            'workflow_promotion': {'status': 'promotable'},
            'success_outcome': {'status': 'partial', 'gap': 'need_stronger_repro_or_impact_evidence'},
        },
    )
    _confirm_total, effective = apply_effective_decision(**kwargs)
    queued = kwargs['followup_queue'][0]
    assert effective['effective_flags']['precision'] is True
    assert queued['high_priority'] is True
    assert queued['recommended_action_types'][:2] == ['fingerprint_probe', 'confirmatory_probe']
    assert queued['planner_preferences']['evidence_lane'] == 'exposure_or_fingerprint'



def test_effective_decision_applies_secondary_followup_after_confirm() -> None:
    runtime_decision = {
        'selected_primary_action': 'confirm',
        'selection_reason': 'confirmable_signal',
        'selected_secondary_action': 'followup',
        'secondary_selection_reason': 'dual_action_confirm_followup',
        'intent_flags': {'retry': False, 'confirm': True, 'followup': True, 'precision': False},
    }
    kwargs = _kwargs(
        runtime_decision=runtime_decision,
        task={'name': 'Authz', 'task_family': 'authz'},
        signal_contract={
            'workflow_promotion': {'status': 'confirmable'},
            'success_outcome': {'status': 'partial'},
        },
    )
    confirm_total, effective = apply_effective_decision(**kwargs)
    assert confirm_total == 1
    assert effective['effective_action'] == 'confirm'
    assert effective['effective_secondary_action'] == 'followup'
    assert effective['effective_flags']['confirm'] is True
    assert effective['effective_flags']['followup'] is True
    assert len(kwargs['followup_queue']) == 1



def test_effective_decision_applies_secondary_precision_after_followup() -> None:
    runtime_decision = {
        'selected_primary_action': 'followup',
        'selection_reason': 'promotable_signal',
        'selected_secondary_action': 'precision',
        'secondary_selection_reason': 'dual_action_followup_precision',
        'intent_flags': {'retry': False, 'confirm': False, 'followup': True, 'precision': False},
    }
    kwargs = _kwargs(
        runtime_decision=runtime_decision,
        task={
            'name': 'Workflow',
            'task_family': 'workflow',
            'recommended_action_types': ['differential_probe'],
            'success_semantics': {'success_gap': 'missing_success_criteria'},
        },
        signal_contract={
            'workflow_promotion': {'status': 'promotable'},
            'success_outcome': {'status': 'partial'},
        },
    )
    _confirm_total, effective = apply_effective_decision(**kwargs)
    assert effective['effective_action'] == 'followup'
    assert effective['effective_secondary_action'] == 'precision'
    assert effective['effective_flags']['followup'] is True
    assert effective['effective_flags']['precision'] is True
    assert len(kwargs['followup_queue']) == 2
    assert kwargs['followup_queue'][1]['high_priority'] is True


def test_branch_lifecycle_derives_open_productive_and_dead_end_states() -> None:
    open_out = branch_lifecycle(
        branch_metadata={'branch_state': 'branch_candidate', 'branch_action': 'confirm', 'branch_reason': 'confirmation_gap', 'branch_evidence_score': 0.32},
        signal_contract={'workflow_promotion': {'status': 'candidate'}, 'success_outcome': {'status': 'partial'}},
        success_status='partial',
        engine_status='ok',
    )
    dead_out = branch_lifecycle(
        branch_metadata={'branch_state': 'branch_candidate', 'branch_action': 'deepen', 'branch_reason': 'proof_path_ready', 'branch_evidence_score': 0.5},
        signal_contract={'adaptation_feedback': {'status': 'negative'}, 'success_outcome': {'status': 'not_met'}},
        success_status='not_met',
        engine_status='ok',
    )
    productive_out = branch_lifecycle(
        branch_metadata={'branch_state': 'branch_candidate', 'branch_action': 'deepen', 'branch_reason': 'proof_path_ready', 'branch_evidence_score': 0.5},
        signal_contract={'workflow_promotion': {'status': 'confirmable'}, 'success_outcome': {'status': 'partial'}},
        success_status='partial',
        engine_status='ok',
    )
    assert open_out['branch_lifecycle_status'] in {'open', 'productive'}
    assert dead_out['branch_lifecycle_status'] == 'dead_end'
    assert productive_out['branch_lifecycle_status'] == 'productive'


def test_branch_thread_identity_derives_stable_key_and_label() -> None:
    out = branch_thread_identity(
        family='authz',
        next_stage='bounded_exploit_proof',
        branch_metadata={'branch_action': 'deepen', 'branch_reason': 'proof_path_ready'},
    )
    assert out['branch_thread_key'] == 'authz::bounded_exploit_proof::deepen::proof_path_ready'
    assert out['branch_thread_label'] == 'authz:bounded_exploit_proof:deepen'


def test_effective_decision_attaches_branch_state_metadata_to_followup_queue() -> None:
    kwargs = _kwargs(
        runtime_decision={'intent_flags': {'retry': False, 'confirm': False, 'followup': True, 'precision': False}},
        task={
            'name': 'Authz',
            'task_family': 'authz',
            'target': 'https://api.example.com/',
            'planning_ladder': {'current_stage': 'control_boundary_confirmation', 'next_stage': 'bounded_exploit_proof'},
            'planner_rationale': {'target_profile_summary': {'target_type': 'api'}, 'target_surface_rationale': ['authenticated_or_boundary_mapping']},
            'success_semantics': {'success_gap': 'missing_success_criteria'},
            'exploit_ladder': {'stage': 'control_boundary_confirmation'},
        },
        signal_contract={'workflow_promotion': {'status': 'promotable'}, 'success_outcome': {'status': 'partial'}},
    )
    _confirm_total, effective = apply_effective_decision(**kwargs)
    queued = kwargs['followup_queue'][0]
    assert effective['effective_action'] == 'followup'
    assert queued['branch_state'] == 'branch_candidate'
    assert queued['branch_action'] in {'confirm', 'deepen'}
    assert queued['branch_reason']
    assert queued['branch_evidence_score'] > 0.0
    assert queued['branch_evidence_signals']
    assert queued['branch_lifecycle_status'] in {'open', 'productive', 'deferred'}
    assert queued['branch_lifecycle_reason']
    assert queued['branch_thread_key']
    assert queued['branch_thread_label']
    assert queued['planner_preferences']['branch_state'] == queued['branch_state']
    assert queued['planner_preferences']['branch_action'] == queued['branch_action']
    assert queued['planner_preferences']['branch_lifecycle_status'] == queued['branch_lifecycle_status']
    assert queued['planner_preferences']['branch_thread_key'] == queued['branch_thread_key']



def test_effective_decision_propagates_runtime_semantics_to_followup_queue() -> None:
    kwargs = _kwargs(
        runtime_decision={'intent_flags': {'retry': False, 'confirm': False, 'followup': True, 'precision': False}},
        task={
            'name': 'Authz',
            'task_family': 'authz',
            'exploit_ladder': {'stage': 'control_boundary_confirmation'},
            'planning_ladder': {'current_stage': 'control_boundary_confirmation', 'next_stage': 'bounded_exploit_proof', 'stage_progression': ['discovery', 'validation', 'control_boundary_confirmation', 'bounded_exploit_proof'], 'planning_mode': 'laddered'},
            'planner_rationale': {'target_profile_summary': {'target_type': 'api'}, 'planner_preferences': {'surface_keywords': ['api', 'account']}, 'target_surface_rationale': ['authenticated_or_boundary_mapping', 'api'], 'recommended_progression': ['authenticated_or_boundary_mapping', 'control_boundary_confirmation', 'bounded_exploit_proof']},
            'actor_requirements': {'required': True, 'differential': True},
            'session_requirements': {'stateful': False, 'auth_context': True, 'prerequisites': ['establish comparison identities']},
            'promotion_policy': {'followup_allowed': True, 'confirm_preferred': True, 'bounded_only': True},
            'contamination_policy': {'learning_excluded_on_cross_host_mismatch': True},
            'approval_sensitivity': {'owner_approval_required': True, 'auth_sensitive': True},
            'action_type': 'differential_probe',
            'capability': 'http_probe',
            'experiment_shape': 'differential',
            'evidence_goal': 'controlled_comparison',
        },
        signal_contract={'workflow_promotion': {'status': 'promotable'}, 'success_outcome': {'status': 'partial'}},
    )
    _confirm_total, effective = apply_effective_decision(**kwargs)
    queued = kwargs['followup_queue'][0]
    assert effective['effective_action'] == 'followup'
    assert queued['exploit_ladder']['stage'] == 'control_boundary_confirmation'
    assert queued['actor_requirements']['differential'] is True
    assert queued['session_requirements']['prerequisites'] == ['establish comparison identities']
    assert queued['action_type'] == 'differential_probe'
    assert queued['capability'] == 'http_probe'
    assert queued['evidence_goal'] == 'controlled_comparison'
    assert 'establish comparison identities' in queued['open_questions']
    assert queued['planning_ladder']['current_stage'] == 'control_boundary_confirmation'
    assert queued['planner_rationale']['target_profile_summary']['target_type'] == 'api'
    assert queued['target_surface_rationale'][0] == 'authenticated_or_boundary_mapping'


def test_effective_decision_blocks_followup_when_policy_disables_it() -> None:
    kwargs = _kwargs(
        runtime_decision={'intent_flags': {'retry': False, 'confirm': False, 'followup': True, 'precision': False}},
        task={
            'name': 'Recon',
            'task_family': 'recon',
            'promotion_policy': {'followup_allowed': False, 'confirm_preferred': False},
        },
        signal_contract={'workflow_promotion': {'status': 'promotable'}, 'success_outcome': {'status': 'partial'}},
    )
    _confirm_total, effective = apply_effective_decision(**kwargs)
    assert effective['effective_flags']['followup'] is False
    assert 'followup' in effective['effective_blockers']
    assert 'followup_policy_disabled' in effective['effective_blockers']['followup']


def test_effective_decision_blocks_confirm_when_stateful_preconditions_unresolved() -> None:
    kwargs = _kwargs(
        runtime_decision={'intent_flags': {'retry': False, 'confirm': True, 'followup': False, 'precision': False}},
        task={
            'name': 'Workflow',
            'task_family': 'workflow',
            'exploit_ladder': {'stage': 'state_transition_confirmation'},
            'session_requirements': {'stateful': True, 'prerequisites': ['capture workflow state markers']},
            'open_questions': ['capture workflow state markers'],
        },
        signal_contract={'workflow_promotion': {'status': 'confirmable'}, 'success_outcome': {'status': 'partial'}},
    )
    _confirm_total, effective = apply_effective_decision(**kwargs)
    assert effective['effective_flags']['confirm'] is False
    assert 'preconditions_unresolved' in effective['effective_blockers']['confirm']



def test_effective_decision_adds_family_specific_evidence_focus_to_queue() -> None:
    kwargs = _kwargs(
        runtime_decision={'intent_flags': {'retry': False, 'confirm': False, 'followup': True, 'precision': False}},
        task={
            'name': 'Authz',
            'task_family': 'authz',
            'exploit_ladder': {'stage': 'control_boundary_confirmation'},
            'planning_ladder': {'current_stage': 'control_boundary_confirmation', 'next_stage': 'bounded_exploit_proof', 'stage_progression': ['discovery', 'validation', 'control_boundary_confirmation', 'bounded_exploit_proof'], 'planning_mode': 'laddered'},
            'planner_rationale': {'target_profile_summary': {'target_type': 'api'}, 'planner_preferences': {'surface_keywords': ['api', 'account']}, 'target_surface_rationale': ['authenticated_or_boundary_mapping', 'api']},
            'actor_requirements': {'required': True, 'differential': True},
            'session_requirements': {'stateful': False, 'auth_context': True, 'prerequisites': ['establish comparison identities']},
            'open_questions': ['establish comparison identities'],
            'evidence_goal': 'controlled_comparison',
        },
        signal_contract={'workflow_promotion': {'status': 'promotable'}, 'success_outcome': {'status': 'partial'}},
    )
    _confirm_total, effective = apply_effective_decision(**kwargs)
    queued = kwargs['followup_queue'][0]
    assert effective['effective_action'] == 'followup'
    assert 'actor_boundary_delta' in queued['followup_evidence_focus']
    assert 'negative_control' in queued['followup_evidence_focus']
    assert 'authenticated_or_boundary_mapping' in queued['followup_evidence_focus']
    assert 'next_stage:bounded_exploit_proof' in queued['followup_evidence_focus']
    assert any(x.startswith('open_question:') for x in queued['followup_evidence_focus'])


def test_effective_decision_uses_configured_followup_cooldown() -> None:
    kwargs = _kwargs(
        runtime_decision={'intent_flags': {'retry': False, 'confirm': False, 'followup': True, 'precision': False}},
        followup_recent={'api.example.com': 1000.0},
        toggles={'enable_confirm_jobs': True, 'enable_followups': True, 'followup_cooldown_sec': 180},
        signal_contract={'workflow_promotion': {'status': 'promotable'}, 'success_outcome': {'status': 'partial'}},
        host_from_target_fn=lambda target: 'api.example.com',
    )
    _confirm_total, effective = apply_effective_decision(**kwargs)
    assert effective['effective_flags']['followup'] is True
    assert 'followup' not in effective.get('effective_blockers', {})
    assert len(kwargs['followup_queue']) == 1
