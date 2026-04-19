from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_runner_bundle_builders as rrbb  # type: ignore


def test_build_queue_coordinator_wraps_queue_coordinator_construction() -> None:
    captured = {}

    class FakeQueueCoordinator:
        def __init__(self, **kwargs):
            captured.update(kwargs)
            self.__dict__.update(kwargs)

    out = rrbb.build_queue_coordinator(
        queue_coordinator_cls=FakeQueueCoordinator,
        followup_queue=[],
        precision_queue=[],
        host_rr={},
        host_success_count={},
        host_fail_count={},
    )
    assert isinstance(out, FakeQueueCoordinator)
    assert captured['followup_queue'] == []


def test_build_runtime_precheck_context_inputs_assembles_precheck_bundle() -> None:
    captured = {}

    class FakeRuntimePrecheckContext:
        def __init__(self, **kwargs):
            captured.update(kwargs)
            self.__dict__.update(kwargs)

    out = rrbb.build_runtime_precheck_context_inputs(
        runtime_precheck_context_cls=FakeRuntimePrecheckContext,
        unresolved_hosts=set(),
        dns_skip_count={},
        host_dns_cache={},
        host_cooldown_until={},
        host_cooldown_skip_count={},
        autodiscover_deep_skip=True,
        executed_keys=set(),
        precheck_skip_examples=[],
        host_precheck_burst={},
        host_state={},
        deep_budget={},
        host_fail_streak={},
        host_success_count={},
        host_fail_count={},
        gate_skip_count={},
        gate_skip_examples={},
        increment_precheck_skip_fn=lambda: None,
        on_executed_key_fn=lambda: None,
        dedup_key_fn=lambda *args, **kwargs: 'dedup:1',
        family_allowed_for_host_stage_fn=lambda *args, **kwargs: True,
        log_skip_fn=lambda *args, **kwargs: None,
    )
    assert isinstance(out, FakeRuntimePrecheckContext)
    assert captured['autodiscover_deep_skip'] is True
    assert callable(captured['dedup_key_fn'])


def test_build_runtime_execution_deps_assembles_execution_services() -> None:
    captured = {}

    class FakeRuntimeExecutionDeps:
        def __init__(self, **kwargs):
            captured.update(kwargs)
            self.__dict__.update(kwargs)

    out = rrbb.build_runtime_execution_deps(
        runtime_execution_deps_cls=FakeRuntimeExecutionDeps,
        summarize_result_fn=lambda *args, **kwargs: None,
        post_result_common_fn=lambda *args, **kwargs: None,
        qualify_and_finalize_run_fn=lambda *args, **kwargs: None,
        inspect_json_signal_from_command_fn=lambda *args, **kwargs: None,
        parse_rc_metrics_fn=lambda *args, **kwargs: None,
        run_control_comparison_fn=lambda *args, **kwargs: None,
        attack_family_fn=lambda *args, **kwargs: 'authz',
        repeated_consistency_ok_fn=lambda *args, **kwargs: True,
        qualify_fn=lambda *args, **kwargs: {},
        can_be_confirmed_fn=lambda *args, **kwargs: False,
        compute_promising_fn=lambda *args, **kwargs: False,
        finding_lifecycle_fn=lambda *args, **kwargs: {},
        adaptive_aggression_fn=lambda *args, **kwargs: 3,
        normalize_pipeline_status_fn=lambda status: status,
        log_event_fn=lambda *args, **kwargs: None,
        run_pipeline_fn=lambda *args, **kwargs: {},
    )
    assert isinstance(out, FakeRuntimeExecutionDeps)
    assert callable(captured['run_pipeline_fn'])


def test_build_runtime_runner_deps_assembles_runner_services() -> None:
    captured = {}

    class FakeRuntimeRunnerDeps:
        def __init__(self, **kwargs):
            captured.update(kwargs)
            self.__dict__.update(kwargs)

    out = rrbb.build_runtime_runner_deps(
        runtime_runner_deps_cls=FakeRuntimeRunnerDeps,
        apply_post_run_actions_fn=lambda **kwargs: (0, {}),
        project_runtime_decision_to_run_info_fn=lambda **kwargs: {},
        maybe_reconsult_planner_fn=lambda **kwargs: None,
        refresh_planner_hints_and_reprioritize_fn=lambda **kwargs: None,
        prepare_task_precheck_fn=lambda **kwargs: {},
        prepare_curated_task_fn=lambda *args, **kwargs: None,
        prepare_runtime_task_fn=lambda *args, **kwargs: None,
        reprioritize_queues_fn=lambda: None,
        persist_recorded_run_fn=lambda **kwargs: 0.0,
        apply_runtime_adaptation_fn=lambda run_info: None,
    )
    assert isinstance(out, FakeRuntimeRunnerDeps)
    assert callable(captured['persist_recorded_run_fn'])


def test_build_runtime_session_bundle_inputs_assembles_bundle_call() -> None:
    class FakeRuntimeExecutionDeps:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class FakeRuntimeRunnerDeps:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    execution_deps, runner_deps, payload = rrbb.build_runtime_session_bundle_inputs(
        runtime_runner_deps_cls=FakeRuntimeRunnerDeps,
        runtime_execution_deps_cls=FakeRuntimeExecutionDeps,
        apply_post_run_actions_fn=lambda **kwargs: (0, {}),
        project_runtime_decision_to_run_info_fn=lambda **kwargs: {},
        maybe_reconsult_planner_fn=lambda **kwargs: None,
        refresh_planner_hints_and_reprioritize_fn=lambda **kwargs: None,
        prepare_task_precheck_fn=lambda **kwargs: {},
        prepare_curated_task_fn=lambda *args, **kwargs: None,
        prepare_runtime_task_fn=lambda *args, **kwargs: None,
        build_execute_runtime_request_fn=lambda *args, **kwargs: {},
        reprioritize_queues_fn=lambda: None,
        persist_recorded_run_fn=lambda **kwargs: 0.0,
        apply_runtime_adaptation_fn=lambda run_info: None,
        qualification_mode='shadow',
        qualification_promising_threshold='probable',
        summarize_result_fn=lambda *args, **kwargs: None,
        post_result_common_fn=lambda *args, **kwargs: None,
        qualify_and_finalize_run_fn=lambda *args, **kwargs: None,
        inspect_json_signal_from_command_fn=lambda *args, **kwargs: None,
        parse_rc_metrics_fn=lambda *args, **kwargs: None,
        run_control_comparison_fn=lambda *args, **kwargs: None,
        attack_family_fn=lambda *args, **kwargs: 'authz',
        repeated_consistency_ok_fn=lambda *args, **kwargs: True,
        qualify_fn=lambda *args, **kwargs: {},
        can_be_confirmed_fn=lambda *args, **kwargs: False,
        compute_promising_fn=lambda *args, **kwargs: False,
        finding_lifecycle_fn=lambda *args, **kwargs: {},
        adaptive_aggression_fn=lambda *args, **kwargs: 3,
        normalize_pipeline_status_fn=lambda status: status,
        log_event_fn=lambda *args, **kwargs: None,
        run_pipeline_fn=lambda *args, **kwargs: {},
    )
    assert execution_deps is not None
    assert runner_deps is not None
    assert payload['prepare_task_precheck_fn'] is not None
    assert callable(payload['run_pipeline_fn'])
