from __future__ import annotations

from typing import Callable


def run_main_execution_stage(*, resolve_run_main_execution_stage_fn: Callable[..., None], state, campaign_validation: dict, run_started, max_runs: int, target_load_limit: int, time_budget_min: int, retry_policy: str, toggles: dict, queue_coordinator, prepare_deps, quality_telemetry: dict, execute_runtime_task_fn: Callable[..., tuple[float, int]], maybe_trigger_plan_regeneration_fn: Callable[..., None], reconcile_active_plan_if_needed_fn: Callable[..., None], persist_live_summary_fn: Callable[[], None], flush_precheck_summary_fn: Callable[..., None], flush_dns_skip_summary_fn: Callable[..., None], flush_host_cooldown_summary_fn: Callable[..., None], flush_execution_gate_summary_fn: Callable[..., None], log_operation_fn: Callable[..., None], build_execute_runner_session_inputs_fn: Callable[..., object], current_scope_targets_fn: Callable[[], list[str]], execute_runner_session_fn: Callable[..., None], build_finalize_runner_exception_inputs_fn: Callable[..., object], finalize_runner_exception_fn: Callable[..., None], globals_dict: dict) -> None:
    return resolve_run_main_execution_stage_fn(
        state=state,
        campaign_validation=campaign_validation,
        run_started=run_started,
        max_runs=max_runs,
        target_load_limit=target_load_limit,
        time_budget_min=time_budget_min,
        retry_policy=retry_policy,
        toggles=toggles,
        queue_coordinator=queue_coordinator,
        prepare_deps=prepare_deps,
        quality_telemetry=quality_telemetry,
        execute_runtime_task_fn=execute_runtime_task_fn,
        maybe_trigger_plan_regeneration_fn=maybe_trigger_plan_regeneration_fn,
        reconcile_active_plan_if_needed_fn=reconcile_active_plan_if_needed_fn,
        persist_live_summary_fn=persist_live_summary_fn,
        flush_precheck_summary_fn=flush_precheck_summary_fn,
        flush_dns_skip_summary_fn=flush_dns_skip_summary_fn,
        flush_host_cooldown_summary_fn=flush_host_cooldown_summary_fn,
        flush_execution_gate_summary_fn=flush_execution_gate_summary_fn,
        log_operation_fn=log_operation_fn,
        build_execute_runner_session_inputs_fn=build_execute_runner_session_inputs_fn,
        current_scope_targets_fn=current_scope_targets_fn,
        execute_runner_session_fn=execute_runner_session_fn,
        build_finalize_runner_exception_inputs_fn=build_finalize_runner_exception_inputs_fn,
        finalize_runner_exception_fn=finalize_runner_exception_fn,
        globals_dict=globals_dict,
    )
