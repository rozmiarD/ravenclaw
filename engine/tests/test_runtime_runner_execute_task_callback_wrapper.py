from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_runner_execute_task_callback_wrapper as rretcw  # type: ignore


def test_build_main_execute_runtime_task_callback_delegates() -> None:
    captured = {}

    def fake_build_main_execute_runtime_task_callback(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return lambda *args, **kwargs2: (0.0, 0)

    out = rretcw.build_main_execute_runtime_task_callback(
        build_main_execute_runtime_task_callback_fn=fake_build_main_execute_runtime_task_callback,
        state=object(),
        execution_deps=object(),
        runner_deps=object(),
        record_and_persist_run_fn=lambda run_info: None,
        toggles={'policy_diag_logging': True},
        host_family_owner_gate={},
        host_cooldown_until={},
        host_code000_streak={},
        host_code000_total={},
        host_403_streak={},
        host_fail_streak={},
        host_fail_count={},
        host_success_count={},
        code000_streak_threshold=3,
        code000_cooldown_sec=900,
        code000_session_cap=5,
        qualification_mode='shadow',
        qualification_promising_threshold='probable',
        build_execute_runtime_task_inputs_fn=lambda **kwargs: object(),
        execute_runtime_task_pipeline_fn=lambda **kwargs: (0.0, ({},)),
        complete_execute_runtime_pipeline_result_fn=lambda **kwargs: 0,
    )
    assert callable(out)
    assert captured['qualification_mode'] == 'shadow'
    assert callable(captured['build_execute_runtime_task_inputs_fn'])
