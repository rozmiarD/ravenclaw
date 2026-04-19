from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_runner_runtime_callbacks_wrapper as rrrcw  # type: ignore


def test_build_main_runtime_callbacks_delegates() -> None:
    captured = {}

    def fake_build_main_runtime_callbacks(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return {'persist_live_summary': lambda: None}

    out = rrrcw.build_main_runtime_callbacks(
        build_main_runtime_callbacks_fn=fake_build_main_runtime_callbacks,
        campaign_validation={'ok': True},
        run_started='started',
        max_runs=5,
        time_budget_min=10,
        retry_policy='balanced',
        runs=[],
        followup_queue=[],
        precision_queue=[],
        precheck_skip_count_ref=[0],
        dns_skip_count={},
        host_cooldown_skip_count={},
        execution_gate_skip_count={},
        quality_telemetry={},
        host_state={},
        queue_coordinator=object(),
        persist_main_runtime_snapshot_fn=lambda **kwargs: None,
        refresh_main_runtime_overrides_fn=lambda *args, **kwargs: (False, False, None, None),
    )
    assert 'persist_live_summary' in out
    assert captured['max_runs'] == 5
