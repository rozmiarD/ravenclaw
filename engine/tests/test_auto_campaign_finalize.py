from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from auto_campaign_finalize import qualify_and_finalize_run  # type: ignore


BASE_TOGGLES = {
    'enable_confirm_jobs': True,
    'enable_followups': True,
    'qualification_followup_threshold': 'probable',
    'qualification_shadow_workflow_bridge': True,
    'candidate_partial_followup_bridge': True,
    'weak_signal_positive_bridge': True,
}


def test_finalize_updates_probable_and_next_aggression_hint() -> None:
    host_weak_count = {}
    quality_telemetry = {'probable': 0, 'confirmed': 0, 'downgraded_confirm': 0}
    events = []

    qual, promising, run_info = qualify_and_finalize_run(
        post={
            'reason_code': 'interesting_signal',
            'summary_text': '[interesting_signal] Base summary',
            'classification': 'mid',
            'planned_cmd': ['curl', 'https://example.com'],
            'signal_codes': ['interesting_signal'],
            'metrics_obj': {'code': 200},
            'control_cmp': {'performed': True, 'control_delta_observed': True, 'reason': 'delta'},
            'run_info': {'engine_status': 'ok', 'auditor_decision': 'approved', 'target': 'https://example.com/', 'objective': 'Recon'},
        },
        objective='Recon',
        target='https://example.com/',
        mode='fast',
        run_index=1,
        decision_label='Run 1',
        owner_override=False,
        aggression=3,
        error_flag=False,
        policy_diag_logging=True,
        force_auth_like_weak_on_http_controls=False,
        repeated_consistency=True,
        host_weak_count=host_weak_count,
        quality_telemetry=quality_telemetry,
        decision_toggles=BASE_TOGGLES,
        qualification_mode='enforce',
        qualification_promising_threshold='probable',
        qualify_fn=lambda payload: {'verdict': 'probable', 'confidence': 'medium', 'reason_code': payload['reason_code']},
        can_be_confirmed_fn=lambda qual: True,
        compute_promising_fn=lambda qual, summary_text, classification: True,
        finding_lifecycle_fn=lambda mode, qual: 'probable',
        adaptive_aggression_fn=lambda base, classification, reason_code, owner_override: base + 1,
        normalize_pipeline_status_fn=lambda engine_status, auditor_decision, error_flag: 'in_progress',
        log_event_fn=lambda *args, **kwargs: events.append((args, kwargs)),
    )
    assert qual['verdict'] == 'probable'
    assert promising is True
    assert run_info['finding_lifecycle'] == 'probable'
    assert run_info['next_aggression_hint'] == 5
    assert quality_telemetry['probable'] == 1
    assert run_info['runtime_decision']['verdict'] == 'probable'
    assert isinstance(run_info['signal_assessment'], dict)
    assert isinstance(run_info['signal_contract'], dict)
    assert run_info['signal_contract']['workflow_promotion']['status'] == 'confirmable'
    assert run_info['signal_contract']['legacy_bridges']['promising'] is True
    assert run_info['signal_contract']['success_outcome']['success_model'] == ''
    assert isinstance(run_info['decision_flags'], dict)
    assert isinstance(run_info['decision_explain'], dict)
    assert isinstance(run_info['decision_economics'], dict)
    assert 'priority_score' in run_info['decision_economics']
    assert run_info['decision_effective_status'] == 'pending'
    assert len(events) >= 3


def test_finalize_downgrades_unconfirmed_confirmed_verdict() -> None:
    host_weak_count = {}
    quality_telemetry = {'probable': 0, 'confirmed': 0, 'downgraded_confirm': 0}

    qual, promising, run_info = qualify_and_finalize_run(
        post={
            'reason_code': 'suspected_issue',
            'summary_text': 'Summary',
            'classification': 'high',
            'planned_cmd': [],
            'signal_codes': [],
            'metrics_obj': {'code': 200},
            'control_cmp': {'performed': False, 'control_delta_observed': False, 'reason': 'n/a'},
            'run_info': {'engine_status': 'ok', 'auditor_decision': 'approved', 'target': 'https://example.com/', 'objective': 'Probe'},
        },
        objective='Probe',
        target='https://example.com/',
        mode='confirm',
        run_index=2,
        decision_label='Run 2',
        owner_override=False,
        aggression=4,
        error_flag=False,
        policy_diag_logging=False,
        force_auth_like_weak_on_http_controls=False,
        repeated_consistency=False,
        host_weak_count=host_weak_count,
        quality_telemetry=quality_telemetry,
        decision_toggles=BASE_TOGGLES,
        qualification_mode='enforce',
        qualification_promising_threshold='probable',
        qualify_fn=lambda payload: {'verdict': 'confirmed', 'confidence': 'high', 'reason_code': payload['reason_code']},
        can_be_confirmed_fn=lambda qual: False,
        compute_promising_fn=lambda qual, summary_text, classification: False,
        finding_lifecycle_fn=lambda mode, qual: 'probable',
        adaptive_aggression_fn=lambda base, classification, reason_code, owner_override: base,
        normalize_pipeline_status_fn=lambda engine_status, auditor_decision, error_flag: 'done',
        log_event_fn=lambda *args, **kwargs: None,
    )
    assert qual['verdict'] == 'probable'
    assert promising is True
    assert run_info['finding_lifecycle'] == 'probable'
    assert 'next_aggression_hint' not in run_info
    assert run_info['runtime_decision']['verdict'] == 'probable'
    assert run_info['signal_contract']['workflow_promotion']['status'] == 'confirmable'
    assert quality_telemetry['downgraded_confirm'] == 1
    assert quality_telemetry['probable'] == 1


def test_finalize_uses_runtime_toggles_for_intent_flags() -> None:
    host_weak_count = {}
    quality_telemetry = {'probable': 0, 'confirmed': 0, 'downgraded_confirm': 0}
    toggles = dict(BASE_TOGGLES)
    toggles['enable_confirm_jobs'] = False

    _qual, _promising, run_info = qualify_and_finalize_run(
        post={
            'reason_code': 'interesting_signal',
            'summary_text': 'Summary',
            'classification': 'mid',
            'planned_cmd': [],
            'signal_codes': ['interesting_signal'],
            'metrics_obj': {'code': 200},
            'control_cmp': {'performed': True, 'control_delta_observed': True, 'reason': 'delta'},
            'run_info': {'engine_status': 'ok', 'auditor_decision': 'approved', 'target': 'https://example.com/', 'objective': 'Probe', 'success_criteria_eval': 'partial'},
        },
        objective='Probe',
        target='https://example.com/',
        mode='followup',
        run_index=3,
        decision_label='Run 3',
        owner_override=False,
        aggression=4,
        error_flag=False,
        policy_diag_logging=False,
        force_auth_like_weak_on_http_controls=False,
        repeated_consistency=False,
        host_weak_count=host_weak_count,
        quality_telemetry=quality_telemetry,
        decision_toggles=toggles,
        qualification_mode='enforce',
        qualification_promising_threshold='probable',
        qualify_fn=lambda payload: {'verdict': 'probable', 'confidence': 'high', 'reason_code': payload['reason_code']},
        can_be_confirmed_fn=lambda qual: True,
        compute_promising_fn=lambda qual, summary_text, classification: True,
        finding_lifecycle_fn=lambda mode, qual: 'probable',
        adaptive_aggression_fn=lambda base, classification, reason_code, owner_override: base,
        normalize_pipeline_status_fn=lambda engine_status, auditor_decision, error_flag: 'done',
        log_event_fn=lambda *args, **kwargs: None,
    )
    assert run_info['decision_intent_flags'] == {'retry': False, 'confirm': False, 'followup': False, 'precision': True}
    assert run_info['runtime_decision']['intent_flags']['precision'] is True


def test_finalize_shadow_bridge_makes_partial_heuristic_signal_followup_promotable() -> None:
    host_weak_count = {}
    quality_telemetry = {'probable': 0, 'confirmed': 0, 'downgraded_confirm': 0}

    _qual, _promising, run_info = qualify_and_finalize_run(
        post={
            'reason_code': 'engine_success',
            'summary_text': 'Potential XSS finding surfaced with redirect behavior',
            'classification': 'low',
            'planned_cmd': [],
            'signal_codes': [],
            'metrics_obj': {'code': 307},
            'control_cmp': {'performed': False, 'control_delta_observed': False, 'reason': 'baseline'},
            'run_info': {
                'engine_status': 'success',
                'auditor_decision': 'approve',
                'target': 'https://example.com/',
                'objective': 'Recon',
                'success_criteria_eval': 'partial',
            },
        },
        objective='Recon',
        target='https://example.com/',
        mode='fast',
        run_index=4,
        decision_label='Run 4',
        owner_override=False,
        aggression=2,
        error_flag=False,
        policy_diag_logging=False,
        force_auth_like_weak_on_http_controls=False,
        repeated_consistency=False,
        host_weak_count=host_weak_count,
        quality_telemetry=quality_telemetry,
        decision_toggles=BASE_TOGGLES,
        qualification_mode='shadow',
        qualification_promising_threshold='probable',
        qualify_fn=lambda payload: {'verdict': 'none', 'confidence': 0.0, 'reason_code': payload['reason_code'], 'false_positive_guards_passed': True},
        can_be_confirmed_fn=lambda qual: False,
        compute_promising_fn=lambda qual, summary_text, classification: False,
        finding_lifecycle_fn=lambda mode, qual: 'signal',
        adaptive_aggression_fn=lambda base, classification, reason_code, owner_override: base,
        normalize_pipeline_status_fn=lambda engine_status, auditor_decision, error_flag: 'done',
        log_event_fn=lambda *args, **kwargs: None,
    )
    assert run_info['signal_assessment']['shadow_bridge_active'] is True
    assert run_info['signal_contract']['workflow_promotion']['status'] == 'promotable'
    assert run_info['runtime_decision']['selected_primary_action'] == 'followup'
    assert run_info['runtime_decision']['selection_reason'] == 'followup_threshold_met'
    assert run_info['runtime_decision']['followup']['reason_code'] == 'followup_threshold_met'
