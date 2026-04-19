from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from auto_campaign_persistence import record_and_persist_run  # type: ignore


def test_record_and_persist_run_updates_host_state_and_returns_timestamp() -> None:
    runs = []
    history = []
    host_state = {'hosts': {}}
    called = {'persist': 0, 'regen': [], 'reprioritize': 0, 'save': 0, 'learn': 0}

    run_info = {
        'objective': 'Recon',
        'target': 'https://example.com/',
        'task_family': 'recon',
        'classification': 'mid',
        'promising': False,
        'request_shape_hygiene': {'request_shape_hygiene_status': 'clean', 'target_host_match_status': 'exact'},
        'signal_contract': {
            'workflow_promotion': {'status': 'promotable'},
            'finding_signal': {'status': 'strong'},
            'adaptation_feedback': {'host_signal': 'positive'},
        },
        'engine_status': 'ok',
        'success_criteria_eval': 'partial',
        'runtime_task': {
            'planning_ladder': {'current_stage': 'discovery', 'next_stage': 'validation'},
            'planner_rationale': {'target_profile_summary': {'target_type': 'web'}, 'target_surface_rationale': ['browser_flow_mapping']},
        },
        'decision_flags': {'followup': False, 'confirm': True},
        'decision_explain': {'why': ['confirm_selected_for_probable_verdict'], 'blockers': []},
    }

    ts = record_and_persist_run(
        runs=runs,
        history=history,
        run_info=run_info,
        host_state=host_state,
        last_persist_ts=0.0,
        record_run_fn=lambda runs_ref, info: runs_ref.append(info),
        persist_live_summary_fn=lambda: called.__setitem__('persist', called['persist'] + 1),
        update_learning_fn=lambda *args, **kwargs: called.__setitem__('learn', called['learn'] + 1),
        save_host_state_fn=lambda state: called.__setitem__('save', called['save'] + 1),
        reprioritize_queues_fn=lambda: called.__setitem__('reprioritize', called['reprioritize'] + 1),
        attack_family_fn=lambda objective, target, family: family or 'generic',
    )
    assert ts > 0
    assert len(runs) == 1
    assert len(history) == 1
    hs = host_state['hosts']['example.com']
    assert hs['state'] == 'promising'
    assert hs['last_success_family'] == 'recon'
    assert hs['promise_score'] > 1.0
    assert hs['evidence_density'] > 0.5
    assert 'validation' in hs['preferred_stages']
    assert 'web' in hs['target_types_seen']
    assert run_info['host_state_band'] == 'promising'
    assert run_info['host_transition']['to_band'] == 'promising'
    assert isinstance(run_info['host_update'], dict)
    assert run_info['run_contamination']['status'] == 'clean'
    assert run_info['decision_economics']['contamination_status'] == 'clean'
    assert run_info['runtime_utility']['contamination_status'] == 'clean'
    assert called['persist'] == 1
    assert called['save'] == 1
    assert called['learn'] == 1
    assert called['regen'] == []


def test_record_and_persist_run_degrades_noisy_host() -> None:
    runs = []
    history = []
    host_state = {'hosts': {}}
    called = {'regen': []}

    run_info = {
        'objective': 'Authz probe',
        'target': 'https://auth.example.com/',
        'task_family': 'authz',
        'classification': 'low',
        'promising': False,
        'request_shape_hygiene': {'request_shape_hygiene_status': 'cross_host_mismatch', 'target_host_match_status': 'mixed'},
        'auditor_decision': 'owner_approval_required',
        'reason_code': 'policy_gate_block',
        'decision_economics': {'value_estimate': 0.2, 'cost_weight': 0.3, 'priority_score': -0.1},
        'engine_status': 'failed',
        'success_criteria_eval': 'failed',
        'decision_flags': {'retry': True},
        'decision_explain': {'why': ['engine_status_failed'], 'blockers': []},
    }

    record_and_persist_run(
        runs=runs,
        history=history,
        run_info=run_info,
        host_state=host_state,
        last_persist_ts=0.0,
        record_run_fn=lambda runs_ref, info: runs_ref.append(info),
        persist_live_summary_fn=lambda: None,
        update_learning_fn=lambda *args, **kwargs: None,
        save_host_state_fn=lambda state: None,
        reprioritize_queues_fn=lambda: None,
        attack_family_fn=lambda objective, target, family: family or 'generic',
    )
    hs = host_state['hosts']['auth.example.com']
    assert hs['noise_score'] < 1.0
    assert hs['state'] in {'active', 'degraded'}
    assert run_info['host_transition']['to_band'] in {'warmup', 'active', 'degraded'}
    assert isinstance(run_info['host_transition']['reasons'], list)
    assert run_info['run_contamination']['status'] == 'contaminated'
    assert run_info['run_contamination']['learning_excluded'] is True
    assert run_info['decision_economics']['priority_score'] < -0.1
    assert run_info['runtime_utility']['contamination_penalty'] > 0
