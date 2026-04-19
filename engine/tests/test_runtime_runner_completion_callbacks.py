from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_runner_completion_callbacks as rrcb  # type: ignore


def test_build_complete_runtime_run_inputs_assembles_completion_bundle() -> None:
    from runtime_session_state import RuntimeSessionState  # type: ignore

    state = RuntimeSessionState(runs=[], history=[], host_state={'api.example.com': {'ok': True}}, curated_plan=[], runtime_plan_meta={}, host_dns_cache={}, toggles={}, planner_hints_cache={}, promising_hits_ref=[1])
    runner_deps = SimpleNamespace(
        apply_post_run_actions_fn=lambda **kwargs: (0, {}),
        project_runtime_decision_to_run_info_fn=lambda **kwargs: {},
        maybe_reconsult_planner_fn=lambda **kwargs: None,
        refresh_planner_hints_and_reprioritize_fn=lambda **kwargs: None,
        precheck_and_prepare_task_fn=lambda **kwargs: {},
        prepare_curated_task_fn=lambda *args, **kwargs: None,
        prepare_runtime_task_fn=lambda *args, **kwargs: None,
        reprioritize_queues_fn=lambda: None,
        persist_recorded_run_fn=lambda **kwargs: 0.0,
        apply_runtime_adaptation_fn=lambda run_info: None,
    )

    payload = rrcb.build_complete_runtime_run_inputs(
        task_ctx={'task_family': 'authz'},
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
        mode='fast',
        confirm_total=3,
        promising=True,
        run_info={'runtime_decision': {'intent_flags': {'followup': True}}},
        runner_deps=runner_deps,
        record_and_persist_run_fn=lambda run_info: None,
        toggles={'policy_diag_logging': True},
        state=state,
    )

    assert payload.target == 'https://api.example.com/'
    assert payload.confirm_total == 3
    assert payload.promising is True
    assert payload.deps == runner_deps
    assert payload.promising_hits_ref == [1]


def test_complete_execute_runtime_pipeline_result_builds_and_completes(monkeypatch) -> None:
    captured = {}

    def fake_build_complete_runtime_run_inputs(**kwargs):  # type: ignore[no-untyped-def]
        captured['build'] = kwargs
        return SimpleNamespace(**kwargs)

    def fake_complete_runtime_run(**kwargs):  # type: ignore[no-untyped-def]
        captured['complete'] = kwargs
        return (9, {'runtime_decision': {}}, None)

    out = rrcb.complete_execute_runtime_pipeline_result(
        task_ctx={'task_family': 'authz'},
        target='https://api.example.com/',
        objective='Probe',
        aggression=4,
        owner_auth=True,
        owner_override=False,
        mode='fast',
        confirm_total=3,
        pipeline_result=(
            {'ok': True},
            'old-classification',
            'approve',
            'ok',
            'old-summary',
            False,
            {
                'reason_code': 'interesting',
                'success_eval_status': 'partial',
                'summary_text': 'new-summary',
                'classification': 'medium',
            },
            {'verdict': 'probable'},
            True,
            {'runtime_decision': {'intent_flags': {'followup': True}}},
        ),
        runner_deps=SimpleNamespace(),
        record_and_persist_run_fn=lambda run_info: None,
        toggles={'policy_diag_logging': True},
        state=SimpleNamespace(runs=[], promising_hits_ref=[1], host_state={}),
        build_complete_runtime_run_inputs_fn=fake_build_complete_runtime_run_inputs,
        complete_runtime_run_fn=fake_complete_runtime_run,
    )

    assert out == 9
    assert captured['build']['classification'] == 'medium'
    assert captured['build']['summary_text'] == 'new-summary'
    assert captured['build']['reason_code'] == 'interesting'
    assert captured['build']['success_eval_status'] == 'partial'
    assert captured['complete']['classification'] == 'medium'


def test_build_main_execute_runtime_task_callback_executes_pipeline_and_completion() -> None:
    state = SimpleNamespace(
        runs=[{'objective': 'Probe', 'target': 'https://api.example.com/'}],
        followup_queue=[{'kind': 'followup'}],
        precision_queue=[{'kind': 'precision'}],
        host_weak_count={},
        quality_telemetry={},
        host_state={'api.example.com': {'ok': True}},
        promising_hits_ref=[1],
    )
    execution_deps = SimpleNamespace()
    runner_deps = SimpleNamespace()
    pipeline_calls = {}
    complete_calls = {}

    def fake_build_execute_runtime_task_inputs(**kwargs):  # type: ignore[no-untyped-def]
        return SimpleNamespace(**kwargs)

    def fake_execute_runtime_task_pipeline(**kwargs):  # type: ignore[no-untyped-def]
        pipeline_calls.update(kwargs)
        return (
            77.0,
            (
                {'ok': True},
                'old-classification',
                'approve',
                'ok',
                'old-summary',
                False,
                {
                    'reason_code': 'interesting',
                    'success_eval_status': 'partial',
                    'summary_text': 'new-summary',
                    'classification': 'medium',
                },
                {'verdict': 'probable'},
                True,
                {'runtime_decision': {'intent_flags': {'followup': True}}},
            ),
        )

    def fake_complete_execute_runtime_pipeline_result(**kwargs):  # type: ignore[no-untyped-def]
        complete_calls.update(kwargs)
        return 9

    callback = rrcb.build_main_execute_runtime_task_callback(
        state=state,
        execution_deps=execution_deps,
        runner_deps=runner_deps,
        record_and_persist_run_fn=lambda run_info: None,
        toggles={'policy_diag_logging': True},
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
        qualification_mode='shadow',
        qualification_promising_threshold='probable',
        build_execute_runtime_task_inputs_fn=fake_build_execute_runtime_task_inputs,
        execute_runtime_task_pipeline_fn=fake_execute_runtime_task_pipeline,
        complete_execute_runtime_pipeline_result_fn=fake_complete_execute_runtime_pipeline_result,
    )

    out = callback(
        {'task_family': 'authz'},
        objective='Probe',
        target='https://api.example.com/',
        mode='fast',
        aggression=4,
        owner_auth=True,
        owner_override=False,
        plan_name='Plan',
        run_index=2,
        last_heartbeat_ts=11.0,
        confirm_total=3,
    )

    assert out == (77.0, 9)
    assert pipeline_calls['objective'] == 'Probe'
    assert pipeline_calls['execution_deps'] == execution_deps
    assert pipeline_calls['qualification_mode'] == 'shadow'
    assert complete_calls['target'] == 'https://api.example.com/'
    assert complete_calls['runner_deps'] == runner_deps
    assert callable(complete_calls['record_and_persist_run_fn'])
