from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from runtime_decision_engine import build_runtime_decision  # type: ignore


def _toggles() -> dict:
    return {
        'enable_confirm_jobs': True,
        'enable_followups': True,
        'qualification_followup_threshold': 'probable',
        'candidate_partial_followup_bridge': True,
    }


def test_runtime_decision_retry_on_engine_failure() -> None:
    rec = build_runtime_decision(
        qual={'verdict': 'probable', 'confidence': 0.8},
        auditor='approve',
        engine_status='failed',
        success_eval_status='partial',
        toggles=_toggles(),
        mode='fast',
    )
    assert rec.action_flags() == {'retry': True, 'confirm': False, 'followup': False, 'precision': False}
    assert 'engine_status_failed' in rec.explain['why']


def test_runtime_decision_confirm_precedes_followup() -> None:
    rec = build_runtime_decision(
        qual={'verdict': 'probable', 'confidence': 0.71},
        auditor='approve',
        engine_status='ok',
        success_eval_status='partial',
        toggles=_toggles(),
        mode='fast',
    )
    assert rec.confirm.allowed is True
    assert rec.followup.allowed is False
    assert rec.action_flags() == {'retry': False, 'confirm': True, 'followup': False, 'precision': False}


def test_runtime_decision_precision_for_followup_mode_when_confirm_disabled() -> None:
    toggles = _toggles()
    toggles['enable_confirm_jobs'] = False
    rec = build_runtime_decision(
        qual={'verdict': 'probable', 'confidence': 0.61},
        auditor='approve',
        engine_status='ok',
        success_eval_status='partial',
        toggles=toggles,
        mode='followup',
    )
    assert rec.precision.allowed is True
    assert rec.action_flags() == {'retry': False, 'confirm': False, 'followup': False, 'precision': True}


def test_runtime_decision_blocked_auditor_blocks_downstream_actions() -> None:
    rec = build_runtime_decision(
        qual={'verdict': 'probable', 'confidence': 0.71},
        auditor='owner_approval_required',
        engine_status='ok',
        success_eval_status='partial',
        toggles=_toggles(),
        mode='fast',
    )
    assert rec.blocked is True
    assert rec.action_flags() == {'retry': False, 'confirm': False, 'followup': False, 'precision': False}


def test_runtime_decision_uses_confirmable_workflow_from_signal_contract() -> None:
    rec = build_runtime_decision(
        qual={'verdict': 'probable', 'confidence': 0.71},
        auditor='approve',
        engine_status='ok',
        success_eval_status='partial',
        toggles=_toggles(),
        mode='fast',
        signal_contract={'workflow_promotion': {'status': 'confirmable'}, 'success_outcome': {'status': 'partial'}},
    )
    assert rec.confirm.allowed is True
    assert rec.confirm.reason_code == 'workflow_confirmable'
    assert rec.action_flags() == {'retry': False, 'confirm': True, 'followup': False, 'precision': False}


def test_runtime_decision_uses_candidate_partial_bridge_for_actionable_signal() -> None:
    toggles = _toggles()
    toggles['enable_confirm_jobs'] = False
    rec = build_runtime_decision(
        qual={'verdict': 'weak_signal', 'confidence': 0.55},
        auditor='approve',
        engine_status='ok',
        success_eval_status='partial',
        toggles=toggles,
        mode='fast',
        signal_contract={
            'workflow_promotion': {'status': 'candidate'},
            'success_outcome': {'status': 'partial'},
            'finding_signal': {'status': 'weak'},
        },
    )
    assert rec.followup.allowed is True
    assert rec.followup.reason_code == 'candidate_partial_followup_bridge'
    assert rec.selection_reason == 'candidate_partial_followup_bridge'
    assert rec.action_flags() == {'retry': False, 'confirm': False, 'followup': True, 'precision': False}


def test_runtime_decision_can_disable_candidate_partial_bridge() -> None:
    toggles = _toggles()
    toggles['enable_confirm_jobs'] = False
    toggles['candidate_partial_followup_bridge'] = False
    rec = build_runtime_decision(
        qual={'verdict': 'weak_signal', 'confidence': 0.55},
        auditor='approve',
        engine_status='ok',
        success_eval_status='partial',
        toggles=toggles,
        mode='fast',
        signal_contract={
            'workflow_promotion': {'status': 'candidate'},
            'success_outcome': {'status': 'partial'},
            'finding_signal': {'status': 'weak'},
        },
    )
    assert rec.followup.allowed is False
    assert 'workflow_not_promotable:candidate' in rec.followup.blockers
    assert 'candidate_requires_promotion' in rec.followup.blockers
    assert rec.action_flags() == {'retry': False, 'confirm': False, 'followup': False, 'precision': False}


def test_runtime_decision_uses_evidence_bearing_followup_bridge_for_promotable_nonpartial_signal() -> None:
    toggles = _toggles()
    toggles['enable_confirm_jobs'] = False
    rec = build_runtime_decision(
        qual={'verdict': 'weak_signal', 'confidence': 0.58, 'false_positive_guards_passed': True},
        auditor='approve',
        engine_status='ok',
        success_eval_status='not_met',
        toggles=toggles,
        mode='fast',
        signal_contract={
            'workflow_promotion': {'status': 'promotable'},
            'success_outcome': {'status': 'not_met'},
            'finding_signal': {'status': 'weak', 'evidence_bearing': True},
        },
    )
    assert rec.followup.allowed is True
    assert rec.followup.reason_code == 'evidence_bearing_followup_bridge'
    assert rec.selection_reason == 'evidence_bearing_followup_bridge'
    assert rec.action_flags() == {'retry': False, 'confirm': False, 'followup': True, 'precision': False}


def test_runtime_decision_prefers_early_precision_for_high_leverage_candidate_family() -> None:
    toggles = _toggles()
    toggles['enable_confirm_jobs'] = False
    rec = build_runtime_decision(
        qual={'verdict': 'weak_signal', 'confidence': 0.57, 'false_positive_guards_passed': True},
        auditor='approve',
        engine_status='ok',
        success_eval_status='partial',
        toggles=toggles,
        mode='fast',
        signal_contract={
            'workflow_promotion': {'status': 'candidate'},
            'success_outcome': {'status': 'partial'},
            'finding_signal': {'status': 'weak', 'evidence_bearing': True},
        },
        task_family='authz',
    )
    assert rec.precision.allowed is True
    assert rec.precision.reason_code == 'high_leverage_candidate_precision'
    assert rec.followup.allowed is False
    assert rec.action_flags() == {'retry': False, 'confirm': False, 'followup': False, 'precision': True}


def test_runtime_decision_selects_safe_secondary_followup_for_confirm() -> None:
    toggles = _toggles()
    rec = build_runtime_decision(
        qual={'verdict': 'probable', 'confidence': 0.74, 'false_positive_guards_passed': True},
        auditor='approve',
        engine_status='ok',
        success_eval_status='partial',
        toggles=toggles,
        mode='fast',
        signal_contract={
            'workflow_promotion': {'status': 'confirmable'},
            'success_outcome': {'status': 'partial'},
            'finding_signal': {'status': 'moderate', 'evidence_bearing': True},
        },
        task_family='authz',
    )
    assert rec.selected_primary_action == 'confirm'
    assert rec.selected_secondary_action == 'followup'
    assert rec.secondary_selection_reason == 'dual_action_confirm_followup'



def test_runtime_decision_selects_safe_secondary_precision_for_followup() -> None:
    toggles = _toggles()
    toggles['enable_confirm_jobs'] = False
    rec = build_runtime_decision(
        qual={'verdict': 'weak_signal', 'confidence': 0.66, 'false_positive_guards_passed': True},
        auditor='approve',
        engine_status='ok',
        success_eval_status='partial',
        toggles=toggles,
        mode='fast',
        signal_contract={
            'workflow_promotion': {'status': 'promotable'},
            'success_outcome': {'status': 'partial'},
            'finding_signal': {'status': 'moderate', 'evidence_bearing': True},
        },
        task_family='workflow',
    )
    assert rec.selected_primary_action == 'followup'
    assert rec.selected_secondary_action == 'precision'
    assert rec.secondary_selection_reason == 'dual_action_followup_precision'


def test_runtime_decision_prefers_precision_for_artifact_capture_signal() -> None:
    toggles = _toggles()
    toggles['enable_confirm_jobs'] = False
    rec = build_runtime_decision(
        qual={'verdict': 'probable', 'confidence': 0.72, 'false_positive_guards_passed': True},
        auditor='approve',
        engine_status='ok',
        success_eval_status='partial',
        toggles=toggles,
        mode='fast',
        task_family='tls_assessment',
        signal_contract={
            'workflow_promotion': {'status': 'promotable'},
            'success_outcome': {'status': 'partial'},
            'finding_signal': {'status': 'moderate', 'evidence_bearing': True},
        },
        runtime_task={
            'planning_ladder': {
                'current_stage': 'report_artifact_capture',
                'next_stage': 'report_artifact_capture',
                'proof_strategy': 'reportable_artifact_capture',
            },
            'exploit_ladder': {'stage': 'report_artifact_capture'},
            'promotion_policy': {'confirm_preferred': False, 'followup_allowed': True},
        },
    )
    assert rec.precision.allowed is True
    assert rec.precision.reason_code == 'artifact_capture_precision_bias'
    assert rec.followup.allowed is False
    assert rec.action_flags() == {'retry': False, 'confirm': False, 'followup': False, 'precision': True}


def test_runtime_decision_artifact_capture_precision_respects_actor_state_blocking() -> None:
    toggles = _toggles()
    toggles['enable_confirm_jobs'] = False
    rec = build_runtime_decision(
        qual={'verdict': 'probable', 'confidence': 0.72, 'false_positive_guards_passed': True},
        auditor='approve',
        engine_status='ok',
        success_eval_status='partial',
        toggles=toggles,
        mode='fast',
        task_family='authz',
        signal_contract={
            'workflow_promotion': {'status': 'promotable'},
            'success_outcome': {'status': 'partial'},
            'finding_signal': {'status': 'strong', 'evidence_bearing': True},
        },
        runtime_task={
            'planning_ladder': {
                'current_stage': 'report_artifact_capture',
                'next_stage': 'report_artifact_capture',
                'proof_strategy': 'reportable_artifact_capture',
            },
            'exploit_ladder': {'stage': 'report_artifact_capture'},
            'promotion_policy': {'confirm_preferred': False, 'followup_allowed': True},
            'actor_requirements': {'required': True, 'differential': True},
            'session_requirements': {'auth_context': True},
            'open_questions': ['actor comparison not mapped yet'],
        },
    )
    assert rec.precision.allowed is False
    assert rec.followup.allowed is True
    assert rec.explain['actor_state_blocking'] is True



def test_runtime_decision_respects_followup_policy_disable_from_runtime_task() -> None:
    record = build_runtime_decision(
        qual={'verdict': 'candidate', 'vuln_class': 'authz', 'confidence': 0.71, 'structured_signal': True},
        auditor='approve',
        engine_status='ok',
        success_eval_status='partial',
        toggles=_toggles(),
        task_family='authz',
        signal_contract={
            'workflow_promotion': {'status': 'promotable'},
            'finding_signal': {'status': 'strong'},
            'success_outcome': {'status': 'partial'},
        },
        runtime_task={'promotion_policy': {'followup_allowed': False, 'confirm_preferred': False}},
    )
    out = record.as_dict()
    assert out['selected_primary_action'] == 'confirm'
    assert 'followup_policy_disabled' in (out['intent_explain']['blockers'] or [])


def test_runtime_decision_prefers_followup_over_confirm_when_policy_requests_it() -> None:
    record = build_runtime_decision(
        qual={'verdict': 'probable', 'vuln_class': 'authz', 'confidence': 0.77, 'structured_signal': True},
        auditor='approve',
        engine_status='ok',
        success_eval_status='partial',
        toggles=_toggles(),
        task_family='authz',
        signal_contract={
            'workflow_promotion': {'status': 'confirmable'},
            'finding_signal': {'status': 'strong'},
            'success_outcome': {'status': 'partial'},
        },
        runtime_task={'promotion_policy': {'followup_allowed': True, 'confirm_preferred': False}},
    )
    out = record.as_dict()
    assert out['selected_primary_action'] == 'followup'
    assert out['intent_explain']['promotion_policy']['confirm_preferred'] is False


def test_runtime_decision_prefers_followup_for_stateful_precondition_gaps() -> None:
    record = build_runtime_decision(
        qual={'verdict': 'candidate', 'vuln_class': 'workflow', 'confidence': 0.68, 'structured_signal': True},
        auditor='approve',
        engine_status='ok',
        success_eval_status='partial',
        toggles=_toggles(),
        task_family='workflow',
        signal_contract={
            'workflow_promotion': {'status': 'confirmable'},
            'finding_signal': {'status': 'strong'},
            'success_outcome': {'status': 'partial'},
        },
        runtime_task={
            'evidence_goal': 'state_transition_artifact',
            'exploit_ladder': {'stage': 'state_transition_confirmation'},
            'session_requirements': {'stateful': True, 'prerequisites': ['capture workflow state markers']},
            'open_questions': ['capture workflow state markers'],
            'promotion_policy': {'followup_allowed': True, 'confirm_preferred': True},
        },
    )
    out = record.as_dict()
    assert out['selected_primary_action'] == 'followup'
    assert 'capture workflow state markers' in out['intent_explain']['precondition_gaps']



def test_runtime_decision_uses_planning_ladder_and_target_surface_rationale_in_explain() -> None:
    record = build_runtime_decision(
        qual={'verdict': 'candidate', 'vuln_class': 'tls_assessment', 'confidence': 0.72, 'structured_signal': True},
        auditor='approve',
        engine_status='ok',
        success_eval_status='partial',
        toggles=_toggles(),
        task_family='tls_assessment',
        signal_contract={
            'workflow_promotion': {'status': 'promotable'},
            'finding_signal': {'status': 'moderate'},
            'success_outcome': {'status': 'partial'},
        },
        runtime_task={
            'promotion_policy': {'followup_allowed': True, 'confirm_preferred': True},
            'planning_ladder': {'current_stage': 'discovery', 'next_stage': 'report_artifact_capture', 'proof_strategy': 'reportable_artifact_capture'},
            'planner_rationale': {
                'recommended_progression': ['artifact_capture', 'report_artifact_capture'],
                'target_profile_summary': {'target_type': 'static'},
                'planner_preferences': {'surface_keywords': ['cdn', 'assets']},
            },
        },
    )
    out = record.as_dict()
    assert out['selected_primary_action'] == 'followup'
    assert out['intent_explain']['planning_ladder']['next_stage'] == 'report_artifact_capture'
    assert out['intent_explain']['artifact_capture_bias'] is True
    assert out['intent_explain']['target_surface_rationale'][0] == 'artifact_capture'



def test_runtime_decision_prefers_confirm_from_ladder_stage_even_without_family_bias() -> None:
    record = build_runtime_decision(
        qual={'verdict': 'probable', 'vuln_class': 'generic', 'confidence': 0.84, 'structured_signal': True},
        auditor='approve',
        engine_status='ok',
        success_eval_status='partial',
        toggles=_toggles(),
        task_family='generic',
        signal_contract={
            'workflow_promotion': {'status': 'confirmable'},
            'finding_signal': {'status': 'moderate'},
            'success_outcome': {'status': 'partial'},
        },
        runtime_task={
            'promotion_policy': {'followup_allowed': True},
            'planning_ladder': {'current_stage': 'control_boundary_confirmation', 'next_stage': 'bounded_exploit_proof'},
            'planner_rationale': {'recommended_progression': ['control_boundary_confirmation', 'bounded_exploit_proof']},
        },
    )
    out = record.as_dict()
    assert out['selected_primary_action'] == 'confirm'
    assert out['intent_explain']['planning_ladder']['current_stage'] == 'control_boundary_confirmation'



def test_runtime_decision_suppresses_confirm_for_discovery_only_goals() -> None:
    record = build_runtime_decision(
        qual={'verdict': 'probable', 'vuln_class': 'recon', 'confidence': 0.81, 'structured_signal': True},
        auditor='approve',
        engine_status='ok',
        success_eval_status='partial',
        toggles=_toggles(),
        task_family='recon',
        signal_contract={
            'workflow_promotion': {'status': 'confirmable'},
            'finding_signal': {'status': 'strong'},
            'success_outcome': {'status': 'partial'},
        },
        runtime_task={'evidence_goal': 'surface_expansion', 'promotion_policy': {'followup_allowed': True, 'confirm_preferred': True}},
    )
    out = record.as_dict()
    assert out['selected_primary_action'] != 'confirm'
    assert out['intent_explain']['family_promotion_profile']['discovery_only'] is True
    assert out['intent_explain']['family_promotion_profile']['exploit_readiness'] == 'discovery_only'
