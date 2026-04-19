from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Any
from datetime import datetime


@dataclass
class ExecuteRunnerSessionInputs:
    state: Any
    max_runs: int
    target_load_limit: int
    time_budget_min: int
    retry_policy: str
    run_started: datetime
    scope_targets: list[str]
    preempt_in_curated: bool
    queue_coordinator: Any
    log_event_fn: Callable[..., None]
    read_runtime_control_state_fn: Callable[..., dict]
    read_runtime_owner_override_fn: Callable[..., bool]
    read_runtime_aggression_override_fn: Callable[..., int | None]
    apply_runtime_overrides_fn: Callable[..., tuple[bool, bool, int | None, int | None]]
    handle_post_run_actions_fn: Callable[..., tuple[int, dict]]
    prepare_curated_task_fn: Callable[..., Any]
    prepare_runtime_task_fn: Callable[..., Any]
    reprioritize_queues_fn: Callable[[], None]
    persist_recorded_run_fn: Callable[..., float]
    maybe_trigger_plan_regeneration_fn: Callable[..., None]
    execute_runtime_task_fn: Callable[..., tuple[float, int]]
    resolve_main_loop_candidate_fn: Callable[..., Any]
    record_run_fn: Callable[..., None]
    persist_live_summary_fn: Callable[[], None]
    normalize_runtime_task_fn: Callable[..., dict]
    reconcile_active_plan_if_needed_fn: Callable[..., None]
    maybe_preempt_curated_entry_fn: Callable[..., Any]
    dedup_key_fn: Callable[..., str]
    build_deduped_target_plan_fn: Callable[..., list[dict]]
    prepare_deps: Any
    propose_next_vector_fn: Callable[..., Any]
    unpack_queued_task_fn: Callable[..., tuple]
    clamp_aggression_fn: Callable[[int], int]
    capped_aggression_fn: Callable[[str, str, int], int]
    run_curated_loop_fn: Callable[..., Any]
    run_main_loop_fn: Callable[..., Any]
    out_path: str
    reports_dir: Path
    archive_root: Path
    campaign_validation: dict
    quality_telemetry: dict
    finalize_outputs_fn: Callable[..., dict]
    flush_precheck_summary_fn: Callable[..., None]
    flush_dns_skip_summary_fn: Callable[..., None]
    flush_host_cooldown_summary_fn: Callable[..., None]
    flush_execution_gate_summary_fn: Callable[..., None]
    log_operation_fn: Callable[..., None]


@dataclass
class FinalizeRunnerExceptionInputs:
    state: Any
    campaign_validation: dict
    run_started: datetime
    max_runs: int
    time_budget_min: int
    retry_policy: str
    out_path: str
    reports_dir: Path
    archive_root: Path
    quality_telemetry: dict
    finalize_outputs_fn: Callable[..., dict]
    flush_precheck_summary_fn: Callable[..., None]
    flush_dns_skip_summary_fn: Callable[..., None]
    flush_host_cooldown_summary_fn: Callable[..., None]
    flush_execution_gate_summary_fn: Callable[..., None]
    log_operation_fn: Callable[..., None]
    error: Exception


def build_execute_runner_session_inputs(*, state: Any, max_runs: int, target_load_limit: int, time_budget_min: int, retry_policy: str, run_started: datetime, scope_targets: list[str], toggles: dict, queue_coordinator: Any, prepare_deps: Any, quality_telemetry: dict, campaign_validation: dict, execute_runtime_task_fn: Callable[..., tuple[float, int]], maybe_trigger_plan_regeneration_fn: Callable[..., None], reconcile_active_plan_if_needed_fn: Callable[..., None], persist_live_summary_fn: Callable[[], None], flush_precheck_summary_fn: Callable[..., None], flush_dns_skip_summary_fn: Callable[..., None], flush_host_cooldown_summary_fn: Callable[..., None], flush_execution_gate_summary_fn: Callable[..., None], log_operation_fn: Callable[..., None], log_event_fn: Callable[..., None], read_runtime_control_state_fn: Callable[..., dict], read_runtime_owner_override_fn: Callable[..., bool], read_runtime_aggression_override_fn: Callable[..., int | None], apply_runtime_overrides_fn: Callable[..., tuple[bool, bool, int | None, int | None]], handle_post_run_actions_fn: Callable[..., tuple[int, dict]], prepare_curated_task_fn: Callable[..., Any], prepare_runtime_task_fn: Callable[..., Any], reprioritize_queues_fn: Callable[[], None], persist_recorded_run_fn: Callable[..., float], resolve_main_loop_candidate_fn: Callable[..., Any], record_run_fn: Callable[..., None], normalize_runtime_task_fn: Callable[..., dict], maybe_preempt_curated_entry_fn: Callable[..., Any], dedup_key_fn: Callable[..., str], build_deduped_target_plan_fn: Callable[..., list[dict]], propose_next_vector_fn: Callable[..., Any], unpack_queued_task_fn: Callable[..., tuple], clamp_aggression_fn: Callable[[int], int], capped_aggression_fn: Callable[[str, str, int], int], run_curated_loop_fn: Callable[..., Any], run_main_loop_fn: Callable[..., Any], out_path: str, reports_dir: Path, archive_root: Path, finalize_outputs_fn: Callable[..., dict]) -> ExecuteRunnerSessionInputs:
    return ExecuteRunnerSessionInputs(
        state=state,
        max_runs=int(max_runs),
        target_load_limit=int(target_load_limit),
        time_budget_min=int(time_budget_min),
        retry_policy=str(retry_policy),
        run_started=run_started,
        scope_targets=scope_targets,
        preempt_in_curated=bool(toggles.get('queue_preemption_in_curated_loop', True)),
        queue_coordinator=queue_coordinator,
        log_event_fn=log_event_fn,
        read_runtime_control_state_fn=read_runtime_control_state_fn,
        read_runtime_owner_override_fn=read_runtime_owner_override_fn,
        read_runtime_aggression_override_fn=read_runtime_aggression_override_fn,
        apply_runtime_overrides_fn=apply_runtime_overrides_fn,
        handle_post_run_actions_fn=handle_post_run_actions_fn,
        prepare_curated_task_fn=prepare_curated_task_fn,
        prepare_runtime_task_fn=prepare_runtime_task_fn,
        reprioritize_queues_fn=reprioritize_queues_fn,
        persist_recorded_run_fn=persist_recorded_run_fn,
        maybe_trigger_plan_regeneration_fn=maybe_trigger_plan_regeneration_fn,
        execute_runtime_task_fn=execute_runtime_task_fn,
        resolve_main_loop_candidate_fn=resolve_main_loop_candidate_fn,
        record_run_fn=record_run_fn,
        persist_live_summary_fn=persist_live_summary_fn,
        normalize_runtime_task_fn=normalize_runtime_task_fn,
        reconcile_active_plan_if_needed_fn=reconcile_active_plan_if_needed_fn,
        maybe_preempt_curated_entry_fn=maybe_preempt_curated_entry_fn,
        dedup_key_fn=dedup_key_fn,
        build_deduped_target_plan_fn=build_deduped_target_plan_fn,
        prepare_deps=prepare_deps,
        propose_next_vector_fn=propose_next_vector_fn,
        unpack_queued_task_fn=unpack_queued_task_fn,
        clamp_aggression_fn=clamp_aggression_fn,
        capped_aggression_fn=capped_aggression_fn,
        run_curated_loop_fn=run_curated_loop_fn,
        run_main_loop_fn=run_main_loop_fn,
        out_path=out_path,
        reports_dir=reports_dir,
        archive_root=archive_root,
        campaign_validation=campaign_validation,
        quality_telemetry=quality_telemetry,
        finalize_outputs_fn=finalize_outputs_fn,
        flush_precheck_summary_fn=flush_precheck_summary_fn,
        flush_dns_skip_summary_fn=flush_dns_skip_summary_fn,
        flush_host_cooldown_summary_fn=flush_host_cooldown_summary_fn,
        flush_execution_gate_summary_fn=flush_execution_gate_summary_fn,
        log_operation_fn=log_operation_fn,
    )


def build_finalize_runner_exception_inputs(*, state: Any, campaign_validation: dict, run_started: datetime, max_runs: int, time_budget_min: int, retry_policy: str, quality_telemetry: dict, flush_precheck_summary_fn: Callable[..., None], flush_dns_skip_summary_fn: Callable[..., None], flush_host_cooldown_summary_fn: Callable[..., None], flush_execution_gate_summary_fn: Callable[..., None], log_operation_fn: Callable[..., None], error: Exception, out_path: str, reports_dir: Path, archive_root: Path, finalize_outputs_fn: Callable[..., dict]) -> FinalizeRunnerExceptionInputs:
    return FinalizeRunnerExceptionInputs(
        state=state,
        campaign_validation=campaign_validation,
        run_started=run_started,
        max_runs=int(max_runs),
        time_budget_min=int(time_budget_min),
        retry_policy=str(retry_policy),
        out_path=out_path,
        reports_dir=reports_dir,
        archive_root=archive_root,
        quality_telemetry=quality_telemetry,
        finalize_outputs_fn=finalize_outputs_fn,
        flush_precheck_summary_fn=flush_precheck_summary_fn,
        flush_dns_skip_summary_fn=flush_dns_skip_summary_fn,
        flush_host_cooldown_summary_fn=flush_host_cooldown_summary_fn,
        flush_execution_gate_summary_fn=flush_execution_gate_summary_fn,
        log_operation_fn=log_operation_fn,
        error=error,
    )
