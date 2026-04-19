from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from auto_campaign_downstream import post_run_decision  # type: ignore


def _base_toggles() -> dict:
    return {
        'enable_confirm_jobs': True,
        'enable_followups': True,
        'qualification_followup_threshold': 'probable',
    }


def test_failed_engine_status_prefers_retry_only() -> None:
    out = post_run_decision({}, {}, {'verdict': 'probable'}, 'mid', 'approved', 'failed', 'partial', _base_toggles(), mode='fast')
    assert out == {'retry': True, 'confirm': False, 'followup': False, 'precision': False}


def test_probable_first_pass_prefers_confirm_over_followup() -> None:
    out = post_run_decision({}, {}, {'verdict': 'probable'}, 'mid', 'approved', 'ok', 'partial', _base_toggles(), mode='fast')
    assert out == {'retry': False, 'confirm': True, 'followup': False, 'precision': False}


def test_followup_mode_still_keeps_confirm_precedence_for_probable() -> None:
    out = post_run_decision({}, {}, {'verdict': 'probable'}, 'mid', 'approved', 'ok', 'partial', _base_toggles(), mode='followup')
    assert out == {'retry': False, 'confirm': True, 'followup': False, 'precision': False}


def test_followup_mode_precision_when_confirm_disabled() -> None:
    toggles = _base_toggles()
    toggles['enable_confirm_jobs'] = False
    out = post_run_decision({}, {}, {'verdict': 'probable'}, 'mid', 'approved', 'ok', 'partial', toggles, mode='followup')
    assert out == {'retry': False, 'confirm': False, 'followup': False, 'precision': True}


def test_blocked_auditor_prevents_followup_and_confirm() -> None:
    out = post_run_decision({}, {}, {'verdict': 'probable'}, 'mid', 'owner_approval_required', 'ok', 'partial', _base_toggles(), mode='fast')
    assert out == {'retry': False, 'confirm': False, 'followup': False, 'precision': False}


def test_post_run_decision_uses_signal_contract_from_result() -> None:
    toggles = _base_toggles()
    toggles['enable_confirm_jobs'] = False
    out = post_run_decision(
        {},
        {'signal_contract': {'workflow_promotion': {'status': 'promotable'}, 'success_outcome': {'status': 'partial'}}},
        {'verdict': 'weak_signal'},
        'mid',
        'approved',
        'ok',
        'partial',
        toggles,
        mode='fast',
    )
    assert out == {'retry': False, 'confirm': False, 'followup': True, 'precision': False}


def test_post_run_decision_uses_evidence_bearing_followup_bridge() -> None:
    toggles = _base_toggles()
    toggles['enable_confirm_jobs'] = False
    out = post_run_decision(
        {'task_family': 'recon'},
        {'signal_contract': {'workflow_promotion': {'status': 'promotable'}, 'success_outcome': {'status': 'not_met'}, 'finding_signal': {'status': 'weak', 'evidence_bearing': True}}},
        {'verdict': 'weak_signal', 'false_positive_guards_passed': True},
        'mid',
        'approved',
        'ok',
        'not_met',
        toggles,
        mode='fast',
    )
    assert out == {'retry': False, 'confirm': False, 'followup': True, 'precision': False}


def test_post_run_decision_prefers_early_precision_for_high_leverage_candidate_family() -> None:
    toggles = _base_toggles()
    toggles['enable_confirm_jobs'] = False
    out = post_run_decision(
        {'task_family': 'authz'},
        {'signal_contract': {'workflow_promotion': {'status': 'candidate'}, 'success_outcome': {'status': 'partial'}, 'finding_signal': {'status': 'weak', 'evidence_bearing': True}}},
        {'verdict': 'weak_signal', 'false_positive_guards_passed': True},
        'mid',
        'approved',
        'ok',
        'partial',
        toggles,
        mode='fast',
    )
    assert out == {'retry': False, 'confirm': False, 'followup': False, 'precision': True}


def test_post_run_decision_prefers_precision_for_artifact_capture_signal() -> None:
    toggles = _base_toggles()
    toggles['enable_confirm_jobs'] = False
    out = post_run_decision(
        {
            'task_family': 'tls_assessment',
            'runtime_task': {
                'planning_ladder': {
                    'current_stage': 'report_artifact_capture',
                    'next_stage': 'report_artifact_capture',
                    'proof_strategy': 'reportable_artifact_capture',
                },
                'exploit_ladder': {'stage': 'report_artifact_capture'},
                'promotion_policy': {'confirm_preferred': False, 'followup_allowed': True},
            },
        },
        {
            'signal_contract': {
                'workflow_promotion': {'status': 'promotable'},
                'success_outcome': {'status': 'partial'},
                'finding_signal': {'status': 'moderate', 'evidence_bearing': True},
            },
        },
        {'verdict': 'probable', 'confidence': 0.72, 'false_positive_guards_passed': True},
        'mid',
        'approved',
        'ok',
        'partial',
        toggles,
        mode='fast',
    )
    assert out == {'retry': False, 'confirm': False, 'followup': False, 'precision': True}
