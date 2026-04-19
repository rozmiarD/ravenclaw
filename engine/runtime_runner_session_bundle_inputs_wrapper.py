from __future__ import annotations

from typing import Callable


def build_runtime_session_bundle_inputs(*, build_runtime_session_bundle_inputs_fn: Callable[..., tuple[object, object, dict]], runtime_session_bundle_inputs_cls: Callable[..., object], runtime_runner_deps_cls: Callable[..., object], runtime_execution_deps_cls: Callable[..., object], apply_post_run_actions_fn: Callable[..., tuple[int, dict]], project_runtime_decision_to_run_info_fn: Callable[..., dict], maybe_reconsult_planner_fn: Callable[..., None], refresh_planner_hints_and_reprioritize_fn: Callable[..., None], prepare_task_precheck_fn: Callable[..., dict], prepare_curated_task_fn: Callable[..., dict | None], prepare_runtime_task_fn: Callable[..., dict | None], build_execute_runtime_request_fn: Callable[..., dict], reprioritize_queues_fn: Callable[[], None], persist_recorded_run_fn: Callable[..., float], apply_runtime_adaptation_fn: Callable[[dict], None], qualification_mode: str, qualification_promising_threshold: str, summarize_result_fn: Callable[..., dict], post_result_common_fn: Callable[..., dict], qualify_and_finalize_run_fn: Callable[..., dict], inspect_json_signal_from_command_fn: Callable[..., dict], parse_rc_metrics_fn: Callable[[str], dict], run_control_comparison_fn: Callable[..., dict], attack_family_fn: Callable[[str, str, str], str], repeated_consistency_ok_fn: Callable[[list[dict], str, str], bool], qualify_fn: Callable[[dict], dict], can_be_confirmed_fn: Callable[[dict], bool], compute_promising_fn: Callable[[dict, str, str], bool], finding_lifecycle_fn: Callable[..., dict], adaptive_aggression_fn: Callable[..., int], normalize_pipeline_status_fn: Callable[[str], str], log_event_fn: Callable[..., None], run_pipeline_fn: Callable[..., dict]) -> object:
    _execution_deps, _runner_deps, payload = build_runtime_session_bundle_inputs_fn(
        runtime_runner_deps_cls=runtime_runner_deps_cls,
        runtime_execution_deps_cls=runtime_execution_deps_cls,
        apply_post_run_actions_fn=apply_post_run_actions_fn,
        project_runtime_decision_to_run_info_fn=project_runtime_decision_to_run_info_fn,
        maybe_reconsult_planner_fn=maybe_reconsult_planner_fn,
        refresh_planner_hints_and_reprioritize_fn=refresh_planner_hints_and_reprioritize_fn,
        prepare_task_precheck_fn=prepare_task_precheck_fn,
        prepare_curated_task_fn=prepare_curated_task_fn,
        prepare_runtime_task_fn=prepare_runtime_task_fn,
        build_execute_runtime_request_fn=build_execute_runtime_request_fn,
        reprioritize_queues_fn=reprioritize_queues_fn,
        persist_recorded_run_fn=persist_recorded_run_fn,
        apply_runtime_adaptation_fn=apply_runtime_adaptation_fn,
        qualification_mode=qualification_mode,
        qualification_promising_threshold=qualification_promising_threshold,
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
    return runtime_session_bundle_inputs_cls(**payload)
