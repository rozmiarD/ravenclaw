from __future__ import annotations

import copy
import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from evaluation_bundle import build_replay_bundle  # type: ignore
from evaluation_replay import replay_dataset, replay_decision_bundle  # type: ignore


def _base_run() -> dict:
    return {
        'index': 1,
        'objective': 'Probe authz branch',
        'target': 'https://api.example.com/v1/users',
        'task_family': 'authz',
        'auditor_decision': 'approve',
        'engine_status': 'ok',
        'signal_contract': {
            'execution_anomaly': {'status': 'none'},
            'workflow_promotion': {'status': 'confirmable', 'verdict': 'confirmed'},
            'finding_signal': {'status': 'strong'},
            'success_outcome': {'status': 'partial'},
            'adaptation_feedback': {'status': 'positive'},
        },
        'decision_selected_action': 'confirm',
        'decision_effective_action': 'confirm',
        'decision_effective_status': 'applied',
        'decision_intent_flags': {'confirm': True},
        'decision_flags': {'confirm': True},
        'runtime_task': {
            'action_type': 'differential_probe',
            'capability': 'http_probe',
            'actor_requirements': {'requires_auth': True},
        },
        'planner_rationale': {'target_surface_rationale': ['actor_asymmetry']},
        'planning_ladder': {'current_stage': 'bounded_exploit_proof', 'next_stage': 'report_artifact_capture'},
        'analysis_contract': {'semantic_loss_class': 'none'},
    }


def test_replay_decision_bundle_marks_exploit_proof_and_actor_asymmetry_success() -> None:
    result = replay_decision_bundle(build_replay_bundle(_base_run()))
    assert result['status'] == 'ok'
    assert result['requested_action'] == 'confirm'
    assert result['effective_action'] == 'confirm'
    assert result['confirmed'] is True
    assert result['exploit_proof'] is True
    assert result['actor_asymmetry_success'] is True


def test_replay_decision_bundle_marks_policy_block_and_exclusion() -> None:
    run = copy.deepcopy(_base_run())
    run['auditor_decision'] = 'owner_approval_required'
    run['engine_status'] = 'blocked'
    run['signal_contract']['execution_anomaly'] = {'status': 'policy_block'}
    run['signal_contract']['finding_signal']['evidence_class'] = 'blocked_evidence'
    result = replay_decision_bundle(build_replay_bundle(run))
    assert result['policy_blocked'] is True
    assert result['owner_gate_pending'] is True
    assert result['evidence_class'] == 'blocked_evidence'
    assert result['semantic_outcome_class'] == 'blocked_evidence'
    assert 'policy_blocked' in result['metric_exclusion_reasons']
    assert 'owner_gate_pending' in result['metric_exclusion_reasons']


def test_replay_decision_bundle_projects_branch_and_recon_intelligence_fields() -> None:
    run = copy.deepcopy(_base_run())
    run['task_family'] = 'recon'
    run['decision_selected_action'] = 'followup'
    run['decision_effective_action'] = 'followup'
    run['decision_intent_flags'] = {'followup': True}
    run['decision_flags'] = {'followup': True}
    run['planning_ladder'] = {'current_stage': 'bounded_exploit_proof', 'next_stage': 'report_artifact_capture'}
    run['runtime_task']['task_family'] = 'recon'
    run['runtime_task']['planning_ladder'] = {'current_stage': 'bounded_exploit_proof', 'next_stage': 'report_artifact_capture'}
    run['runtime_task']['branch_state'] = 'branch_candidate'
    run['runtime_task']['branch_action'] = 'deepen'
    run['runtime_task']['branch_reason'] = 'recon_to_exploit_synthesis'
    run['runtime_task']['branch_evidence_score'] = 0.42
    run['planner_rationale'] = {'target_surface_rationale': ['authenticated_or_boundary_mapping']}
    result = replay_decision_bundle(build_replay_bundle(run))
    assert result['branch_candidate'] is True
    assert result['branch_quality_positive'] is True
    assert result['recon_like'] is True
    assert result['recon_to_exploit_candidate'] is True
    assert result['recon_to_exploit_success'] is True
    assert result['signal_bearing'] is True
    assert result['confirmation_reached'] is True
    assert result['branch_action'] == 'deepen'
    assert result['branch_lifecycle_status'] == 'productive'
    assert result['branch_lifecycle_reason']
    assert result['branch_lifecycle_confidence'] > 0.0
    assert result['branch_thread_key'] == 'recon::report_artifact_capture::deepen::recon_to_exploit_synthesis'
    assert result['branch_thread_label'] == 'recon:report_artifact_capture:deepen'
    assert result['synthesis_recommended_action'] in {'confirm', 'deepen', 'pivot', 'abandon'}
    assert result['synthesis_reason']
    assert result['synthesis_alignment'] is True
    assert result['synthesis_positive'] is True


def test_replay_decision_bundle_marks_divergence_on_action_mismatch() -> None:
    run = copy.deepcopy(_base_run())
    run['decision_selected_action'] = 'followup'
    result = replay_decision_bundle(build_replay_bundle(run))
    assert result['status'] == 'divergent'
    assert any('requested_action_mismatch' in item for item in result['divergence_reasons'])


def test_replay_dataset_counts_statuses() -> None:
    ok_bundle = build_replay_bundle(_base_run())
    div_run = copy.deepcopy(_base_run())
    div_run['decision_selected_action'] = 'followup'
    div_bundle = build_replay_bundle(div_run)
    output = replay_dataset({'dataset_id': 'd1', 'run_id': 'r1', 'campaign_key': 'c1', 'variant': {'variant_id': 'baseline'}, 'bundles': [ok_bundle, div_bundle]})
    assert output['bundle_count'] == 2
    assert output['status_counts']['ok'] == 1
    assert output['status_counts']['divergent'] == 1
