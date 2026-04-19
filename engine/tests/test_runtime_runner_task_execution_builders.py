from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_runner_task_execution_builders as rrteb  # type: ignore


class FakePostRunActionInputs:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class FakeExecuteRuntimeTaskInputs:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def test_build_post_run_action_inputs_normalizes_and_binds_helpers() -> None:
    payload = rrteb.build_post_run_action_inputs(
        post_run_action_inputs_cls=FakePostRunActionInputs,
        task={'task_family': 'authz'},
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
        confirm_total=2,
        confirm_class_counts={},
        max_confirm_jobs_per_target=1,
        max_confirm_jobs_total=4,
        max_confirm_jobs_per_class=2,
        confirm_job_cooldown_sec=600,
        quality_telemetry={'probable': 1},
        toggles={'policy_diag_logging': True},
        promising=True,
        signal_contract={'workflow_promotion': 'promotable'},
        runtime_decision={'intent_flags': {'followup': True}},
        dedup_key_fn=lambda *args, **kwargs: 'dedup:1',
        attack_family_fn=lambda *args, **kwargs: 'authz',
        host_from_target_fn=lambda target: 'api.example.com',
        next_followup_family_fn=lambda *args, **kwargs: 'authz',
        clamp_aggression_fn=lambda level: level,
        capped_aggression_fn=lambda family, target, aggression: aggression,
        adaptive_aggression_fn=lambda *args, **kwargs: 5,
        post_run_decision_fn=lambda **kwargs: {'decision': 'queued'},
        log_event_fn=lambda *args, **kwargs: None,
    )
    assert payload.task['mode'] == 'followup'
    assert payload.signal_contract == {'workflow_promotion': 'promotable'}
    assert callable(payload.dedup_key_fn)


def test_build_execute_runtime_task_inputs_assembles_execution_bundle() -> None:
    state = SimpleNamespace(
        runs=[{'objective': 'Probe', 'target': 'https://api.example.com/'}],
        followup_queue=[{'a': 1}],
        precision_queue=[{'b': 2}],
        host_weak_count={},
        quality_telemetry={},
    )
    deps = SimpleNamespace()
    payload = rrteb.build_execute_runtime_task_inputs(
        execute_runtime_task_inputs_cls=FakeExecuteRuntimeTaskInputs,
        task_ctx={'task_family': 'authz'},
        objective='Probe',
        target='https://api.example.com/',
        mode='fast',
        aggression=4,
        owner_auth=True,
        owner_override=False,
        plan_name='Plan',
        run_index=2,
        last_heartbeat_ts=11.0,
        state=state,
        execution_deps=deps,
        host_family_owner_gate={},
        host_cooldown_until={},
        host_code000_streak={},
        host_code000_total={},
        host_403_streak={},
        host_fail_streak={},
        host_fail_count={},
        host_success_count={},
        code000_streak_threshold=3,
        code000_cooldown_sec=900,
        code000_session_cap=5,
        toggles={'policy_diag_logging': True},
        qualification_mode='shadow',
        qualification_promising_threshold='probable',
    )
    assert payload.objective == 'Probe'
    assert payload.runs_count == 1
    assert payload.followup_queue_len == 1
    assert payload.precision_queue_len == 1
    assert payload.deps == deps


def test_run_record_and_persist_stage_builds_inputs_and_calls_runtime_persist() -> None:
    state = SimpleNamespace(runs=[{'objective': 'Probe'}], history=[{'objective': 'Probe'}], host_state={'api.example.com': {'ok': True}})
    services = SimpleNamespace()
    captured = {}

    def fake_build_record_and_persist_run_inputs(**kwargs):  # type: ignore[no-untyped-def]
        return SimpleNamespace(**kwargs)

    def fake_record_and_persist_runtime_run(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return 55.5

    out = rrteb.run_record_and_persist_stage(
        build_record_and_persist_run_inputs_fn=fake_build_record_and_persist_run_inputs,
        record_and_persist_runtime_run_fn=fake_record_and_persist_runtime_run,
        services=services,
        state=state,
        run_info={'objective': 'Probe'},
        last_persist_ts=12.5,
        persist_live_summary_fn=lambda: None,
        update_learning_fn=lambda *args, **kwargs: None,
        save_host_state_fn=lambda *args, **kwargs: None,
        attack_family_fn=lambda objective, target, family: family or 'generic',
    )
    assert out == 55.5
    assert captured['services'] == services
    assert captured['state'] == state
    assert captured['last_persist_ts'] == 12.5
