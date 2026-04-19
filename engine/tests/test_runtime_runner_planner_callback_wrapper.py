from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_runner_planner_callback_wrapper as rrpcw  # type: ignore


def test_build_main_planner_callbacks_updates_refs_and_delegates() -> None:
    captured = {}

    def fake_resolve_main_planner_callbacks(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return {'ok': True}

    out = rrpcw.build_main_planner_callbacks(
        resolve_main_planner_callbacks_fn=fake_resolve_main_planner_callbacks,
        state=object(),
        toggles={'x': True},
        runs=[{'objective': 'Probe'}],
        followup_queue=[{'kind': 'followup'}],
        precision_queue=[{'kind': 'precision'}],
        planner_hints_cache_ref=[{'hint': True}],
        last_regen_run_index_ref=[3],
        curated_plan_ref=[[{'target': 'https://api.example.com/'}]],
        active_plan_revision_ref=[4],
        active_plan_hash_ref=['abc123'],
        reprioritize_queues_fn=lambda: None,
        summarize_planner_feedback_fn=lambda *args, **kwargs: {},
        load_planner_hints_fn=lambda: {'fresh': True},
        apply_planner_hints_refresh_fn=lambda *args, **kwargs: None,
        apply_plan_regeneration_fn=lambda *args, **kwargs: None,
        regenerate_runtime_plan_fn=lambda *args, **kwargs: [],
        apply_plan_reconciliation_fn=lambda *args, **kwargs: None,
        load_runtime_plan_meta_fn=lambda: {'plan_revision': 4},
        load_curated_plan_fn=lambda: [{'target': 'https://api.example.com/'}],
        dedup_key_fn=lambda *args, **kwargs: 'dedup:1',
        log_event_fn=lambda *args, **kwargs: None,
    )
    assert out == {'ok': True}
    assert captured['active_plan_hash_ref'] == ['abc123']
    assert callable(captured['load_runtime_plan_meta_fn'])
