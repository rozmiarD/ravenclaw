from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from runtime_session_bootstrap import build_runtime_session_bundles  # type: ignore


def test_build_runtime_session_bundles_returns_all_dependency_groups() -> None:
    bundles = build_runtime_session_bundles(
        apply_post_run_actions_fn=lambda **kwargs: (0, {}),
        project_runtime_decision_to_run_info_fn=lambda **kwargs: {},
        maybe_reconsult_planner_fn=lambda *args, **kwargs: None,
        refresh_planner_hints_and_reprioritize_fn=lambda *args, **kwargs: None,
        prepare_task_precheck_fn=lambda **kwargs: {},
        prepare_curated_task_fn=lambda *args, **kwargs: None,
        prepare_runtime_task_fn=lambda *args, **kwargs: None,
        reprioritize_queues_fn=lambda: None,
        persist_recorded_run_fn=lambda **kwargs: 0.0,
        apply_runtime_adaptation_fn=lambda run_info: None,
        summarize_result_fn=lambda result: ('medium', 'approve', 'ok', 'summary', False),
        post_result_common_fn=lambda **kwargs: {},
        qualify_and_finalize_run_fn=lambda **kwargs: ({}, False, {}),
        inspect_json_signal_from_command_fn=lambda *args, **kwargs: None,
        parse_rc_metrics_fn=lambda *args, **kwargs: {},
        run_control_comparison_fn=lambda *args, **kwargs: {},
        attack_family_fn=lambda *args, **kwargs: 'recon',
        repeated_consistency_ok_fn=lambda *args, **kwargs: True,
        qualify_fn=lambda payload: payload,
        can_be_confirmed_fn=lambda qual: True,
        compute_promising_fn=lambda *args, **kwargs: True,
        finding_lifecycle_fn=lambda *args, **kwargs: 'probable',
        adaptive_aggression_fn=lambda *args, **kwargs: 3,
        normalize_pipeline_status_fn=lambda *args, **kwargs: 'ok',
        log_event_fn=lambda *args, **kwargs: None,
        run_pipeline_fn=lambda *args, **kwargs: {'ok': True},
    )
    assert bundles.runner_deps.persist_recorded_run_fn(run_info={}) == 0.0
    assert bundles.execution_deps.run_pipeline_fn('Recon', 'https://a.example.com/') == {'ok': True}
    assert bundles.prepare_deps.precheck_and_prepare_task_fn(objective='Recon') == {}
