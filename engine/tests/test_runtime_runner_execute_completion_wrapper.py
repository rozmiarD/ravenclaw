from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_runner_execute_completion_wrapper as rrecw  # type: ignore


def test_complete_execute_runtime_pipeline_result_delegates() -> None:
    captured = {}

    def fake_complete_execute_runtime_pipeline_result(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return 9

    out = rrecw.complete_execute_runtime_pipeline_result(
        complete_execute_runtime_pipeline_result_fn=fake_complete_execute_runtime_pipeline_result,
        task_ctx={'task_family': 'authz'},
        target='https://api.example.com/',
        objective='Probe',
        aggression=4,
        owner_auth=True,
        owner_override=False,
        mode='fast',
        confirm_total=3,
        pipeline_result=({'ok': True},),
        runner_deps=object(),
        record_and_persist_run_fn=lambda run_info: None,
        toggles={'policy_diag_logging': True},
        state=object(),
        build_complete_runtime_run_inputs_fn=lambda **kwargs: object(),
        complete_runtime_run_fn=lambda **kwargs: (9, {}, None),
    )
    assert out == 9
    assert captured['objective'] == 'Probe'
    assert callable(captured['build_complete_runtime_run_inputs_fn'])
