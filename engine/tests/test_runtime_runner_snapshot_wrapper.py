from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_runner_snapshot_wrapper as rrsw  # type: ignore


def test_persist_main_runtime_snapshot_delegates() -> None:
    captured = {}

    def fake_persist_main_runtime_snapshot(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)

    rrsw.persist_main_runtime_snapshot(
        persist_main_runtime_snapshot_fn=fake_persist_main_runtime_snapshot,
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
        out_path='out.json',
        save_queue_state_fn=lambda **kwargs: None,
        current_campaign_key_fn=lambda: 'key',
        runtime_snapshot_path='snap.json',
        load_runtime_plan_meta_fn=lambda *args, **kwargs: {},
        persist_live_snapshot_fn=lambda **kwargs: None,
        warn_fn=lambda *args, **kwargs: None,
    )
    assert captured['runtime_snapshot_path'] == 'snap.json'
