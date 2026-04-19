from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_runner_post_run_callback as rrprc  # type: ignore


def test_build_main_post_run_actions_callback_preserves_signal_and_runtime_decision() -> None:
    captured = {}

    def fake_handle_post_run_actions(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return (5, {'decision': 'queued'})

    callback = rrprc.build_main_post_run_actions_callback(
        handle_post_run_actions_fn=fake_handle_post_run_actions,
        retry_counts={},
        retry_limit=2,
        followup_queue=[],
        followup_counts={},
        followup_recent={},
        max_followups_per_target=3,
        scheduled_keys=set(),
        host_weak_count={},
        host_family_owner_gate={},
        confirm_counts={},
        confirm_recent={},
        confirm_class_counts={},
        max_confirm_jobs_per_target=1,
        max_confirm_jobs_total=4,
        max_confirm_jobs_per_class=2,
        confirm_job_cooldown_sec=600,
        quality_telemetry={'probable': 1},
        toggles={'policy_diag_logging': True},
        enqueue_followup_task_fn=lambda task, high_priority=False: None,
    )
    out = callback(
        {'task_family': 'authz'},
        result={'ok': True},
        qual={'verdict': 'probable'},
        classification='medium',
        auditor='approve',
        engine_status='ok',
        success_eval_status='partial',
        summary_text='summary',
        reason_code='interesting',
        target='https://api.example.com/',
        objective='Probe',
        aggression=4,
        owner_auth=True,
        owner_override=False,
        mode='followup',
        confirm_total=2,
        promising=True,
        signal_contract={'workflow_promotion': 'promotable'},
        runtime_decision={'intent_flags': {'followup': True}},
    )
    assert out == (5, {'decision': 'queued'})
    assert captured['signal_contract'] == {'workflow_promotion': 'promotable'}
    assert captured['runtime_decision'] == {'intent_flags': {'followup': True}}
    assert captured['confirm_total'] == 2
