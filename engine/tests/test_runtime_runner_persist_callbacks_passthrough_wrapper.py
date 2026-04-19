from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_runner_persist_callbacks_passthrough_wrapper as rrpcpw  # type: ignore


def test_build_main_persist_callbacks_delegates() -> None:
    captured = {}

    def fake_build_main_persist_callbacks(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return {'record_and_persist_run': lambda run_info: None}

    out = rrpcpw.build_main_persist_callbacks(
        build_main_persist_callbacks_fn=fake_build_main_persist_callbacks,
        persist_services=object(),
        state=object(),
        last_persist_ts_ref=[0.0],
        persist_live_summary_fn=lambda: None,
        run_record_and_persist_stage_fn=lambda **kwargs: 0.0,
        apply_runtime_adaptation_fn=lambda run_info: None,
    )
    assert 'record_and_persist_run' in out
    assert callable(captured['persist_live_summary_fn'])
