from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from runtime_execution_deps import RuntimeExecutionDeps  # type: ignore


def test_runtime_execution_deps_holds_callable_bundle() -> None:
    deps = RuntimeExecutionDeps(
        summarize_result_fn=lambda result: ('medium', 'approve', 'ok', 'summary', False),
        post_result_common_fn=lambda **kwargs: {},
        qualify_and_finalize_run_fn=lambda **kwargs: ({}, False, {}),
        inspect_json_signal_from_command_fn=lambda *args, **kwargs: None,
        parse_rc_metrics_fn=lambda *args, **kwargs: {},
        run_control_comparison_fn=lambda *args, **kwargs: {},
        attack_family_fn=lambda *args, **kwargs: 'recon',
        repeated_consistency_ok_fn=lambda runs, target, objective: True,
        qualify_fn=lambda payload: payload,
        can_be_confirmed_fn=lambda qual: True,
        compute_promising_fn=lambda qual, summary_text, classification: True,
        finding_lifecycle_fn=lambda mode, qual: 'probable',
        adaptive_aggression_fn=lambda aggression, classification, reason_code, owner_override: aggression,
        normalize_pipeline_status_fn=lambda engine_status, auditor_decision, error_flag: engine_status,
        log_event_fn=lambda *args, **kwargs: None,
        run_pipeline_fn=lambda *args, **kwargs: {'ok': True},
    )
    assert deps.attack_family_fn('Recon', 'https://a.example.com/') == 'recon'
    assert deps.run_pipeline_fn('Recon', 'https://a.example.com/') == {'ok': True}
