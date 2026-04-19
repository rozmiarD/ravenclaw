from __future__ import annotations

import json
from typing import Callable


def run_main_execution_stage(*, state, campaign_validation: dict, run_started, max_runs: int, target_load_limit: int, time_budget_min: int, retry_policy: str, toggles: dict, queue_coordinator, prepare_deps, quality_telemetry: dict, execute_runtime_task_fn: Callable[..., tuple[float, int]], maybe_trigger_plan_regeneration_fn: Callable[..., None], reconcile_active_plan_if_needed_fn: Callable[..., None], persist_live_summary_fn: Callable[[], None], flush_precheck_summary_fn: Callable[..., None], flush_dns_skip_summary_fn: Callable[..., None], flush_host_cooldown_summary_fn: Callable[..., None], flush_execution_gate_summary_fn: Callable[..., None], log_operation_fn: Callable[..., None], build_execute_runner_session_inputs_fn: Callable[..., object], current_scope_targets_fn: Callable[[], list[str]], execute_runner_session_fn: Callable[..., dict], build_finalize_runner_exception_inputs_fn: Callable[..., object], finalize_runner_exception_fn: Callable[..., None], globals_dict: dict):
    for fn_name in ('parse_rc_metrics', 'summarize_result', 'run_pipeline'):
        if not callable(globals_dict.get(fn_name)):
            raise RuntimeError(f'startup_self_check_failed: missing {fn_name}')
    try:
        execute_inputs = build_execute_runner_session_inputs_fn(
            state=state,
            max_runs=max_runs,
            target_load_limit=target_load_limit,
            time_budget_min=time_budget_min,
            retry_policy=retry_policy,
            run_started=run_started,
            scope_targets=current_scope_targets_fn(),
            toggles=toggles,
            queue_coordinator=queue_coordinator,
            prepare_deps=prepare_deps,
            quality_telemetry=quality_telemetry,
            campaign_validation=campaign_validation,
            execute_runtime_task_fn=execute_runtime_task_fn,
            maybe_trigger_plan_regeneration_fn=maybe_trigger_plan_regeneration_fn,
            reconcile_active_plan_if_needed_fn=reconcile_active_plan_if_needed_fn,
            persist_live_summary_fn=persist_live_summary_fn,
            flush_precheck_summary_fn=flush_precheck_summary_fn,
            flush_dns_skip_summary_fn=flush_dns_skip_summary_fn,
            flush_host_cooldown_summary_fn=flush_host_cooldown_summary_fn,
            flush_execution_gate_summary_fn=flush_execution_gate_summary_fn,
            log_operation_fn=log_operation_fn,
        )
        summary = execute_runner_session_fn(**vars(execute_inputs))
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    except Exception as exc:  # noqa: BLE001
        finalize_inputs = build_finalize_runner_exception_inputs_fn(
            state=state,
            campaign_validation=campaign_validation,
            run_started=run_started,
            max_runs=max_runs,
            time_budget_min=time_budget_min,
            retry_policy=retry_policy,
            quality_telemetry=quality_telemetry,
            flush_precheck_summary_fn=flush_precheck_summary_fn,
            flush_dns_skip_summary_fn=flush_dns_skip_summary_fn,
            flush_host_cooldown_summary_fn=flush_host_cooldown_summary_fn,
            flush_execution_gate_summary_fn=flush_execution_gate_summary_fn,
            log_operation_fn=log_operation_fn,
            error=exc,
        )
        finalize_runner_exception_fn(**vars(finalize_inputs))
        raise
