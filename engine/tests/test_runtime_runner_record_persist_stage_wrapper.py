from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_runner_record_persist_stage_wrapper as rrpsw  # type: ignore


def test_run_record_and_persist_stage_delegates() -> None:
    captured = {}

    def fake_run_record_and_persist_stage(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return 1.5

    out = rrpsw.run_record_and_persist_stage(
        run_record_and_persist_stage_fn=fake_run_record_and_persist_stage,
        build_record_and_persist_run_inputs_fn=lambda **kwargs: object(),
        record_and_persist_runtime_run_fn=lambda **kwargs: 1.5,
        services=object(),
        state=object(),
        run_info={},
        last_persist_ts=0.0,
        persist_live_summary_fn=lambda: None,
        update_learning_fn=lambda *args, **kwargs: None,
        save_host_state_fn=lambda *args, **kwargs: None,
        attack_family_fn=lambda *args: 'x',
    )
    assert out == 1.5
    assert callable(captured['build_record_and_persist_run_inputs_fn'])
