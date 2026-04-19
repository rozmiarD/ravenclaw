from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_runner_session_bundle_inputs_wrapper as rrsbiw  # type: ignore


def test_build_runtime_session_bundle_inputs_delegates() -> None:
    captured = {}

    def fake_build_runtime_session_bundle_inputs(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return object(), object(), {'prepare_task_precheck_fn': kwargs['prepare_task_precheck_fn']}

    out = rrsbiw.build_runtime_session_bundle_inputs(
        build_runtime_session_bundle_inputs_fn=fake_build_runtime_session_bundle_inputs,
        runtime_session_bundle_inputs_cls=SimpleNamespace,
        runtime_runner_deps_cls=object,
        runtime_execution_deps_cls=object,
        apply_post_run_actions_fn=lambda **kwargs: (0, {}),
        project_runtime_decision_to_run_info_fn=lambda **kwargs: {},
        maybe_reconsult_planner_fn=lambda *args, **kwargs: None,
        refresh_planner_hints_and_reprioritize_fn=lambda *args, **kwargs: None,
        prepare_task_precheck_fn=lambda **kwargs: {},
        prepare_curated_task_fn=lambda *args, **kwargs: None,
        prepare_runtime_task_fn=lambda *args, **kwargs: None,
        build_execute_runtime_request_fn=lambda **kwargs: {},
        reprioritize_queues_fn=lambda: None,
        persist_recorded_run_fn=lambda **kwargs: 0.0,
        apply_runtime_adaptation_fn=lambda run_info: None,
        qualification_mode='shadow',
        qualification_promising_threshold='probable',
        summarize_result_fn=lambda **kwargs: {},
        post_result_common_fn=lambda **kwargs: {},
        qualify_and_finalize_run_fn=lambda **kwargs: {},
        inspect_json_signal_from_command_fn=lambda **kwargs: {},
        parse_rc_metrics_fn=lambda text: {},
        run_control_comparison_fn=lambda *args, **kwargs: {},
        attack_family_fn=lambda *args: 'x',
        repeated_consistency_ok_fn=lambda *args: True,
        qualify_fn=lambda payload: {},
        can_be_confirmed_fn=lambda qual: False,
        compute_promising_fn=lambda qual, summary_text, classification: False,
        finding_lifecycle_fn=lambda **kwargs: {},
        adaptive_aggression_fn=lambda *args, **kwargs: 3,
        normalize_pipeline_status_fn=lambda status: status,
        log_event_fn=lambda *args, **kwargs: None,
        run_pipeline_fn=lambda **kwargs: {},
    )
    assert callable(out.prepare_task_precheck_fn)
    assert captured['qualification_mode'] == 'shadow'
