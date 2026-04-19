from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime, timezone

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_runner_execution_stage_runner as rresr  # type: ignore


def test_run_main_execution_stage_executes_and_prints_summary(capsys) -> None:
    captured = {}

    class Inputs:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    def fake_build_execute_runner_session_inputs(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return Inputs(state=kwargs['state'], prepare_deps=kwargs['prepare_deps'])

    def fake_execute_runner_session(**kwargs):  # type: ignore[no-untyped-def]
        return {'ok': True, 'runs': 1}

    rresr.run_main_execution_stage(
        state=object(),
        campaign_validation={'ok': True},
        run_started=datetime.now(timezone.utc),
        max_runs=5,
        target_load_limit=9,
        time_budget_min=10,
        retry_policy='balanced',
        toggles={'queue_preemption_in_curated_loop': False},
        queue_coordinator=object(),
        prepare_deps=object(),
        quality_telemetry={},
        execute_runtime_task_fn=lambda *args, **kwargs: (0.0, 0),
        maybe_trigger_plan_regeneration_fn=lambda reason, force=False: None,
        reconcile_active_plan_if_needed_fn=lambda reason: None,
        persist_live_summary_fn=lambda: None,
        flush_precheck_summary_fn=lambda force=False: None,
        flush_dns_skip_summary_fn=lambda force=False: None,
        flush_host_cooldown_summary_fn=lambda force=False: None,
        flush_execution_gate_summary_fn=lambda force=False: None,
        log_operation_fn=lambda *args, **kwargs: None,
        build_execute_runner_session_inputs_fn=fake_build_execute_runner_session_inputs,
        current_scope_targets_fn=lambda: ['a.example.com'],
        execute_runner_session_fn=fake_execute_runner_session,
        build_finalize_runner_exception_inputs_fn=lambda **kwargs: Inputs(**kwargs),
        finalize_runner_exception_fn=lambda **kwargs: None,
        globals_dict={'parse_rc_metrics': lambda *args, **kwargs: {}, 'summarize_result': lambda *args, **kwargs: {}, 'run_pipeline': lambda *args, **kwargs: {}},
    )
    out = capsys.readouterr().out
    assert '"ok": true' in out
    assert captured['scope_targets'] == ['a.example.com']


def test_run_main_execution_stage_finalizes_and_reraises() -> None:
    finalized = {}

    class Inputs:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    def fake_execute_runner_session(**kwargs):  # type: ignore[no-untyped-def]
        raise RuntimeError('boom')

    def fake_finalize_runner_exception(**kwargs):  # type: ignore[no-untyped-def]
        finalized.update(kwargs)

    try:
        rresr.run_main_execution_stage(
            state=object(),
            campaign_validation={'ok': True},
            run_started=datetime.now(timezone.utc),
            max_runs=5,
            target_load_limit=9,
            time_budget_min=10,
            retry_policy='balanced',
            toggles={},
            queue_coordinator=object(),
            prepare_deps=object(),
            quality_telemetry={},
            execute_runtime_task_fn=lambda *args, **kwargs: (0.0, 0),
            maybe_trigger_plan_regeneration_fn=lambda reason, force=False: None,
            reconcile_active_plan_if_needed_fn=lambda reason: None,
            persist_live_summary_fn=lambda: None,
            flush_precheck_summary_fn=lambda force=False: None,
            flush_dns_skip_summary_fn=lambda force=False: None,
            flush_host_cooldown_summary_fn=lambda force=False: None,
            flush_execution_gate_summary_fn=lambda force=False: None,
            log_operation_fn=lambda *args, **kwargs: None,
            build_execute_runner_session_inputs_fn=lambda **kwargs: Inputs(**kwargs),
            current_scope_targets_fn=lambda: [],
            execute_runner_session_fn=fake_execute_runner_session,
            build_finalize_runner_exception_inputs_fn=lambda **kwargs: Inputs(**kwargs),
            finalize_runner_exception_fn=fake_finalize_runner_exception,
            globals_dict={'parse_rc_metrics': lambda *args, **kwargs: {}, 'summarize_result': lambda *args, **kwargs: {}, 'run_pipeline': lambda *args, **kwargs: {}},
        )
    except RuntimeError as exc:
        assert str(exc) == 'boom'
    else:
        raise AssertionError('expected RuntimeError')

    assert finalized['retry_policy'] == 'balanced'
