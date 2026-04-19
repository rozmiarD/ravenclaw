from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_runner_execution_stage_passthrough_wrapper as rrespw  # type: ignore


def test_run_main_execution_stage_delegates() -> None:
    captured = {}

    def fake_resolve_run_main_execution_stage(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)

    rrespw.run_main_execution_stage(
        resolve_run_main_execution_stage_fn=fake_resolve_run_main_execution_stage,
        state=object(),
        campaign_validation={'ok': True},
        run_started='started',
        max_runs=5,
        target_load_limit=9,
        time_budget_min=10,
        retry_policy='balanced',
        toggles={},
        queue_coordinator=object(),
        prepare_deps=object(),
        quality_telemetry={},
        execute_runtime_task_fn=lambda *args, **kwargs: (0.0, 0),
        maybe_trigger_plan_regeneration_fn=lambda *args, **kwargs: None,
        reconcile_active_plan_if_needed_fn=lambda *args, **kwargs: None,
        persist_live_summary_fn=lambda: None,
        flush_precheck_summary_fn=lambda *args, **kwargs: None,
        flush_dns_skip_summary_fn=lambda *args, **kwargs: None,
        flush_host_cooldown_summary_fn=lambda *args, **kwargs: None,
        flush_execution_gate_summary_fn=lambda *args, **kwargs: None,
        log_operation_fn=lambda *args, **kwargs: None,
        build_execute_runner_session_inputs_fn=lambda **kwargs: object(),
        current_scope_targets_fn=lambda: [],
        execute_runner_session_fn=lambda **kwargs: None,
        build_finalize_runner_exception_inputs_fn=lambda **kwargs: object(),
        finalize_runner_exception_fn=lambda **kwargs: None,
        globals_dict={},
    )
    assert captured['max_runs'] == 5
