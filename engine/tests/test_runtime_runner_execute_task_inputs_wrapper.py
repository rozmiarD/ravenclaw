from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_runner_execute_task_inputs_wrapper as rretiw  # type: ignore


def test_build_execute_runtime_task_inputs_delegates() -> None:
    captured = {}

    def fake_build_execute_runtime_task_inputs(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return object()

    out = rretiw.build_execute_runtime_task_inputs(
        build_execute_runtime_task_inputs_fn=fake_build_execute_runtime_task_inputs,
        execute_runtime_task_inputs_cls=object,
        task_ctx={},
        objective='Probe',
        target='https://example.com',
        mode='fast',
        aggression=4,
        owner_auth=True,
        owner_override=False,
        plan_name=None,
        run_index=1,
        last_heartbeat_ts=0.0,
        state=object(),
        execution_deps=object(),
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
        toggles={},
        qualification_mode='shadow',
        qualification_promising_threshold='probable',
    )
    assert out is not None
    assert captured['objective'] == 'Probe'
