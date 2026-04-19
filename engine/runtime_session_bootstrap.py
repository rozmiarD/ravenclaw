from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from runtime_execution_deps import RuntimeExecutionDeps  # type: ignore
from runtime_prepare_deps import RuntimePrepareDeps  # type: ignore
from runtime_runner_deps import RuntimeRunnerDeps  # type: ignore


@dataclass
class RuntimeSessionBundles:
    runner_deps: RuntimeRunnerDeps
    execution_deps: RuntimeExecutionDeps
    prepare_deps: RuntimePrepareDeps


def build_runtime_session_bundles(
    *,
    apply_post_run_actions_fn,
    project_runtime_decision_to_run_info_fn,
    maybe_reconsult_planner_fn,
    refresh_planner_hints_and_reprioritize_fn,
    prepare_task_precheck_fn,
    prepare_curated_task_fn,
    prepare_runtime_task_fn,
    build_execute_runtime_request_fn=None,
    reprioritize_queues_fn,
    persist_recorded_run_fn,
    apply_runtime_adaptation_fn,
    summarize_result_fn,
    post_result_common_fn,
    qualify_and_finalize_run_fn,
    inspect_json_signal_from_command_fn,
    parse_rc_metrics_fn,
    run_control_comparison_fn,
    attack_family_fn,
    repeated_consistency_ok_fn,
    qualify_fn,
    can_be_confirmed_fn,
    compute_promising_fn,
    finding_lifecycle_fn,
    adaptive_aggression_fn,
    normalize_pipeline_status_fn,
    log_event_fn,
    run_pipeline_fn,
) -> RuntimeSessionBundles:
    runner_deps = RuntimeRunnerDeps(
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
    execution_deps = RuntimeExecutionDeps(
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
    prepare_deps = RuntimePrepareDeps(
        precheck_and_prepare_task_fn=prepare_task_precheck_fn,
        prepare_curated_task_fn=prepare_curated_task_fn,
        prepare_runtime_task_fn=prepare_runtime_task_fn,
        build_execute_runtime_request_fn=build_execute_runtime_request_fn,
    )
    return RuntimeSessionBundles(runner_deps=runner_deps, execution_deps=execution_deps, prepare_deps=prepare_deps)
