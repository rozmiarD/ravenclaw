from __future__ import annotations

from typing import Callable, Any


def build_queue_coordinator(*, queue_coordinator_cls, followup_queue: Any, precision_queue: Any, host_rr: Any, host_success_count: Any, host_fail_count: Any):
    return queue_coordinator_cls(
        followup_queue=followup_queue,
        precision_queue=precision_queue,
        host_rr=host_rr,
        host_success_count=host_success_count,
        host_fail_count=host_fail_count,
    )


def build_runtime_precheck_context_inputs(*, runtime_precheck_context_cls, unresolved_hosts: set, dns_skip_count: dict, host_dns_cache: dict, host_cooldown_until: dict, host_cooldown_skip_count: dict, autodiscover_deep_skip: bool, executed_keys: set, precheck_skip_examples: list, host_precheck_burst: dict, host_state: dict, deep_budget: dict, host_fail_streak: dict, host_success_count: dict, host_fail_count: dict, gate_skip_count: dict, gate_skip_examples: dict, increment_precheck_skip_fn: Callable[[], None], on_executed_key_fn: Callable[[], None], dedup_key_fn: Callable[..., str], family_allowed_for_host_stage_fn: Callable[..., Any], log_skip_fn: Callable[..., None], host_health_cooldown_sec: int = 900, deep_budget_cap_per_host_family: int = 2, precheck_burst_cooldown_threshold: int = 10, precheck_burst_cooldown_sec: int = 300, host_fail_streak_backoff_step_sec: float = 0.4, host_fail_streak_backoff_cap_sec: float = 2.0):
    return runtime_precheck_context_cls(
        unresolved_hosts=unresolved_hosts,
        dns_skip_count=dns_skip_count,
        host_dns_cache=host_dns_cache,
        host_cooldown_until=host_cooldown_until,
        host_cooldown_skip_count=host_cooldown_skip_count,
        autodiscover_deep_skip=bool(autodiscover_deep_skip),
        executed_keys=executed_keys,
        precheck_skip_examples=precheck_skip_examples,
        host_precheck_burst=host_precheck_burst,
        host_state=host_state,
        deep_budget=deep_budget,
        host_fail_streak=host_fail_streak,
        host_success_count=host_success_count,
        host_fail_count=host_fail_count,
        dedup_key_fn=dedup_key_fn,
        family_allowed_for_host_stage_fn=family_allowed_for_host_stage_fn,
        log_skip_fn=log_skip_fn,
        increment_precheck_skip_fn=increment_precheck_skip_fn,
        on_executed_key_fn=on_executed_key_fn,
        gate_skip_count=gate_skip_count,
        gate_skip_examples=gate_skip_examples,
        host_health_cooldown_sec=max(60, int(host_health_cooldown_sec or 900)),
        deep_budget_cap_per_host_family=max(1, int(deep_budget_cap_per_host_family or 2)),
        precheck_burst_cooldown_threshold=max(2, int(precheck_burst_cooldown_threshold or 10)),
        precheck_burst_cooldown_sec=max(60, int(precheck_burst_cooldown_sec or 300)),
        host_fail_streak_backoff_step_sec=max(0.0, float(host_fail_streak_backoff_step_sec if host_fail_streak_backoff_step_sec is not None else 0.4)),
        host_fail_streak_backoff_cap_sec=max(0.0, float(host_fail_streak_backoff_cap_sec if host_fail_streak_backoff_cap_sec is not None else 2.0)),
    )


def build_runtime_execution_deps(*, runtime_execution_deps_cls, summarize_result_fn: Callable[..., Any], post_result_common_fn: Callable[..., Any], qualify_and_finalize_run_fn: Callable[..., Any], inspect_json_signal_from_command_fn: Callable[..., Any], parse_rc_metrics_fn: Callable[..., Any], run_control_comparison_fn: Callable[..., Any], attack_family_fn: Callable[..., Any], repeated_consistency_ok_fn: Callable[..., Any], qualify_fn: Callable[..., Any], can_be_confirmed_fn: Callable[..., Any], compute_promising_fn: Callable[..., Any], finding_lifecycle_fn: Callable[..., Any], adaptive_aggression_fn: Callable[..., Any], normalize_pipeline_status_fn: Callable[..., Any], log_event_fn: Callable[..., None], run_pipeline_fn: Callable[..., Any]):
    return runtime_execution_deps_cls(
        summarize_result_fn=summarize_result_fn,
        post_result_common_fn=post_result_common_fn,
        qualify_and_finalize_run_fn=qualify_and_finalize_run_fn,
        inspect_json_signal_from_command_fn=inspect_json_signal_from_command_fn,
        parse_rc_metrics_fn=parse_rc_metrics_fn,
        run_control_comparison_fn=run_control_comparison_fn,
        attack_family_fn=attack_family_fn,
        repeated_consistency_ok_fn=repeated_consistency_ok_fn,
        qualify_fn=qualify_fn,
        can_be_confirmed_fn=can_be_confirmed_fn,
        compute_promising_fn=compute_promising_fn,
        finding_lifecycle_fn=finding_lifecycle_fn,
        adaptive_aggression_fn=adaptive_aggression_fn,
        normalize_pipeline_status_fn=normalize_pipeline_status_fn,
        log_event_fn=log_event_fn,
        run_pipeline_fn=run_pipeline_fn,
    )


def build_runtime_runner_deps(*, runtime_runner_deps_cls, apply_post_run_actions_fn: Callable[..., tuple[int, dict]], project_runtime_decision_to_run_info_fn: Callable[..., dict], maybe_reconsult_planner_fn: Callable[..., None], refresh_planner_hints_and_reprioritize_fn: Callable[..., None], prepare_task_precheck_fn: Callable[..., dict], prepare_curated_task_fn: Callable[..., dict | None], prepare_runtime_task_fn: Callable[..., dict | None], reprioritize_queues_fn: Callable[[], None], persist_recorded_run_fn: Callable[..., float], apply_runtime_adaptation_fn: Callable[[dict], None]):
    return runtime_runner_deps_cls(
        apply_post_run_actions_fn=apply_post_run_actions_fn,
        project_runtime_decision_to_run_info_fn=project_runtime_decision_to_run_info_fn,
        maybe_reconsult_planner_fn=maybe_reconsult_planner_fn,
        refresh_planner_hints_and_reprioritize_fn=refresh_planner_hints_and_reprioritize_fn,
        precheck_and_prepare_task_fn=prepare_task_precheck_fn,
        prepare_curated_task_fn=prepare_curated_task_fn,
        prepare_runtime_task_fn=prepare_runtime_task_fn,
        reprioritize_queues_fn=reprioritize_queues_fn,
        persist_recorded_run_fn=persist_recorded_run_fn,
        apply_runtime_adaptation_fn=apply_runtime_adaptation_fn,
    )


def build_runtime_session_bundle_inputs(*, runtime_runner_deps_cls, runtime_execution_deps_cls, apply_post_run_actions_fn: Callable[..., tuple[int, dict]], project_runtime_decision_to_run_info_fn: Callable[..., dict], maybe_reconsult_planner_fn: Callable[..., None], refresh_planner_hints_and_reprioritize_fn: Callable[..., None], prepare_task_precheck_fn: Callable[..., dict], prepare_curated_task_fn: Callable[..., dict | None], prepare_runtime_task_fn: Callable[..., dict | None], build_execute_runtime_request_fn: Callable[..., dict], reprioritize_queues_fn: Callable[[], None], persist_recorded_run_fn: Callable[..., float], apply_runtime_adaptation_fn: Callable[[dict], None], qualification_mode: str, qualification_promising_threshold: str, summarize_result_fn: Callable[..., Any], post_result_common_fn: Callable[..., Any], qualify_and_finalize_run_fn: Callable[..., Any], inspect_json_signal_from_command_fn: Callable[..., Any], parse_rc_metrics_fn: Callable[..., Any], run_control_comparison_fn: Callable[..., Any], attack_family_fn: Callable[..., Any], repeated_consistency_ok_fn: Callable[..., Any], qualify_fn: Callable[..., Any], can_be_confirmed_fn: Callable[..., Any], compute_promising_fn: Callable[..., Any], finding_lifecycle_fn: Callable[..., Any], adaptive_aggression_fn: Callable[..., Any], normalize_pipeline_status_fn: Callable[..., Any], log_event_fn: Callable[..., None], run_pipeline_fn: Callable[..., Any]):
    runner_deps = build_runtime_runner_deps(
        runtime_runner_deps_cls=runtime_runner_deps_cls,
        apply_post_run_actions_fn=apply_post_run_actions_fn,
        project_runtime_decision_to_run_info_fn=project_runtime_decision_to_run_info_fn,
        maybe_reconsult_planner_fn=maybe_reconsult_planner_fn,
        refresh_planner_hints_and_reprioritize_fn=refresh_planner_hints_and_reprioritize_fn,
        prepare_task_precheck_fn=prepare_task_precheck_fn,
        prepare_curated_task_fn=prepare_curated_task_fn,
        prepare_runtime_task_fn=prepare_runtime_task_fn,
        reprioritize_queues_fn=reprioritize_queues_fn,
        persist_recorded_run_fn=persist_recorded_run_fn,
        apply_runtime_adaptation_fn=apply_runtime_adaptation_fn,
    )
    execution_deps = build_runtime_execution_deps(
        runtime_execution_deps_cls=runtime_execution_deps_cls,
        summarize_result_fn=summarize_result_fn,
        post_result_common_fn=post_result_common_fn,
        qualify_and_finalize_run_fn=qualify_and_finalize_run_fn,
        inspect_json_signal_from_command_fn=inspect_json_signal_from_command_fn,
        parse_rc_metrics_fn=parse_rc_metrics_fn,
        run_control_comparison_fn=run_control_comparison_fn,
        attack_family_fn=attack_family_fn,
        repeated_consistency_ok_fn=repeated_consistency_ok_fn,
        qualify_fn=qualify_fn,
        can_be_confirmed_fn=can_be_confirmed_fn,
        compute_promising_fn=compute_promising_fn,
        finding_lifecycle_fn=finding_lifecycle_fn,
        adaptive_aggression_fn=adaptive_aggression_fn,
        normalize_pipeline_status_fn=normalize_pipeline_status_fn,
        log_event_fn=log_event_fn,
        run_pipeline_fn=run_pipeline_fn,
    )
    return execution_deps, runner_deps, {
        'apply_post_run_actions_fn': apply_post_run_actions_fn,
        'project_runtime_decision_to_run_info_fn': project_runtime_decision_to_run_info_fn,
        'maybe_reconsult_planner_fn': maybe_reconsult_planner_fn,
        'refresh_planner_hints_and_reprioritize_fn': refresh_planner_hints_and_reprioritize_fn,
        'prepare_task_precheck_fn': prepare_task_precheck_fn,
        'prepare_curated_task_fn': prepare_curated_task_fn,
        'prepare_runtime_task_fn': prepare_runtime_task_fn,
        'build_execute_runtime_request_fn': build_execute_runtime_request_fn,
        'reprioritize_queues_fn': reprioritize_queues_fn,
        'persist_recorded_run_fn': persist_recorded_run_fn,
        'apply_runtime_adaptation_fn': apply_runtime_adaptation_fn,
        'summarize_result_fn': summarize_result_fn,
        'post_result_common_fn': post_result_common_fn,
        'qualify_and_finalize_run_fn': qualify_and_finalize_run_fn,
        'inspect_json_signal_from_command_fn': inspect_json_signal_from_command_fn,
        'parse_rc_metrics_fn': parse_rc_metrics_fn,
        'run_control_comparison_fn': run_control_comparison_fn,
        'attack_family_fn': attack_family_fn,
        'repeated_consistency_ok_fn': repeated_consistency_ok_fn,
        'qualify_fn': qualify_fn,
        'can_be_confirmed_fn': can_be_confirmed_fn,
        'compute_promising_fn': compute_promising_fn,
        'finding_lifecycle_fn': finding_lifecycle_fn,
        'adaptive_aggression_fn': adaptive_aggression_fn,
        'normalize_pipeline_status_fn': normalize_pipeline_status_fn,
        'log_event_fn': log_event_fn,
        'run_pipeline_fn': run_pipeline_fn,
    }
