from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_runner_post_run_flow as rrprf  # type: ignore


class FakeInputs:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def test_run_post_run_actions_applies_hint_then_delegates() -> None:
    captured = {}

    def fake_build(**kwargs):
        captured['build'] = kwargs
        return FakeInputs(**kwargs)

    def fake_apply(**kwargs):
        captured['apply'] = kwargs
        return (3, {'effective_status': 'applied'})

    out = rrprf.run_post_run_actions(
        task={'task_family': 'authz'},
        result={'planner_feedback': {'dead_end_pressure_recent': 0.8}},
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
        confirm_total=1,
        confirm_class_counts={},
        max_confirm_jobs_per_target=2,
        max_confirm_jobs_total=4,
        max_confirm_jobs_per_class=2,
        confirm_job_cooldown_sec=600,
        quality_telemetry={},
        toggles={'policy_diag_logging': True},
        promising=True,
        signal_contract={'workflow_promotion': 'promotable'},
        runtime_decision={'intent_flags': {'followup': True, 'confirm': False}},
        enqueue_followup_task_fn=lambda task, high_priority=False: None,
        quality_aware_followup_admission_hint_fn=lambda task, result, decision: {'suppress_followup': True, 'force_high_priority': False, 'reason': 'dead_end_pressure'},
        apply_post_run_admission_hint_fn=lambda decision, hint: {'intent_flags': {'followup': False, 'confirm': False}},
        build_post_run_action_inputs_fn=fake_build,
        apply_effective_decision_fn=fake_apply,
    )
    assert out == (3, {'effective_status': 'applied'})
    assert captured['build']['runtime_decision']['intent_flags']['followup'] is False
    assert captured['apply']['runtime_decision']['intent_flags']['followup'] is False
