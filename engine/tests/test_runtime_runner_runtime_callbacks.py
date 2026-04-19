from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_runner_runtime_callbacks as rrrc  # type: ignore


def test_build_main_runtime_callbacks_wire_persist_queue_and_override() -> None:
    events = []
    persisted = []
    queue = SimpleNamespace(
        enqueue=lambda task, high_priority=False: events.append(('enqueue', task, high_priority)),
        dequeue=lambda: {'kind': 'followup'},
    )

    callbacks = rrrc.build_main_runtime_callbacks(
        campaign_validation={'ok': True},
        run_started=datetime.now(timezone.utc),
        max_runs=5,
        time_budget_min=10,
        retry_policy='balanced',
        runs=[],
        followup_queue=[],
        precision_queue=[],
        precheck_skip_count_ref=[1],
        dns_skip_count={'api.example.com': 1},
        host_cooldown_skip_count={'api.example.com': 2},
        execution_gate_skip_count={'api.example.com': 3},
        quality_telemetry={},
        host_state={'api.example.com': {'ok': True}},
        queue_coordinator=queue,
        persist_main_runtime_snapshot_fn=lambda **kwargs: persisted.append(kwargs),
        refresh_main_runtime_overrides_fn=lambda *args: (True, False, 3, 2),
    )

    callbacks['persist_live_summary']()
    callbacks['enqueue_followup_task']({'kind': 'followup'}, high_priority=True)
    out = callbacks['dequeue_next_task']()
    override_out = callbacks['refresh_runtime_overrides'](False, True, 2, 1)

    assert persisted
    assert events == [('enqueue', {'kind': 'followup'}, True)]
    assert out == {'kind': 'followup'}
    assert override_out == (True, False, 3, 2)


def test_build_main_precheck_hooks_increment_and_flush() -> None:
    events = []
    hooks = rrrc.build_main_precheck_hooks(
        precheck_skip_count_ref=[2],
        flush_precheck_summary_fn=lambda: events.append('precheck'),
        flush_dns_skip_summary_fn=lambda: events.append('dns'),
        flush_host_cooldown_summary_fn=lambda: events.append('cooldown'),
        flush_execution_gate_summary_fn=lambda: events.append('gate'),
    )

    hooks['inc_precheck_skip']()
    hooks['on_executed_key']()

    assert events == ['precheck', 'dns', 'cooldown', 'gate']


def test_persist_main_runtime_snapshot_passes_expected_payload() -> None:
    captured = {}

    def fake_persist_live_snapshot(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)

    rrrc.persist_main_runtime_snapshot(
        campaign_validation={'ok': True},
        run_started=datetime.now(timezone.utc),
        max_runs=5,
        time_budget_min=10,
        retry_policy='balanced',
        runs=[{'objective': 'Probe'}],
        followup_queue=[{'kind': 'followup'}],
        precision_queue=[{'kind': 'precision'}],
        precheck_skip_count_ref=[4],
        dns_skip_count={'api.example.com': 1},
        host_cooldown_skip_count={'api.example.com': 2},
        execution_gate_skip_count={'api.example.com': 3},
        quality_telemetry={'branch_quality_rate_recent': 0.5},
        host_state={'api.example.com': {'ok': True}},
        out_path='reports/out.json',
        save_queue_state_fn=lambda *args, **kwargs: None,
        current_campaign_key_fn=lambda: 'campaign-key',
        runtime_snapshot_path='reports/runtime-snapshot.json',
        load_runtime_plan_meta_fn=lambda: {'revision': 3},
        persist_live_snapshot_fn=fake_persist_live_snapshot,
        warn_fn=lambda message: None,
    )

    assert captured['campaign_key'] == 'campaign-key'
    assert captured['precheck_skip_count'] == 4
    assert captured['runtime_snapshot_path'] == 'reports/runtime-snapshot.json'
    assert captured['runtime_plan_meta'] == {'revision': 3}


def test_refresh_main_runtime_overrides_delegates() -> None:
    captured = {}

    def fake_apply_runtime_overrides(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return (True, False, 3, 2)

    out = rrrc.refresh_main_runtime_overrides(
        False,
        True,
        2,
        1,
        apply_runtime_overrides_fn=fake_apply_runtime_overrides,
        read_runtime_owner_override_fn=lambda default=False: True,
        read_runtime_aggression_override_fn=lambda: 3,
        log_event_fn=lambda *args, **kwargs: None,
    )

    assert out == (True, False, 3, 2)
    assert captured['owner_override_global'] is False
    assert callable(captured['read_runtime_owner_override_fn'])
