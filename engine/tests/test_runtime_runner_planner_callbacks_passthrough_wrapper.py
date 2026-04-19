from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_runner_planner_callbacks_passthrough_wrapper as rrpcpw  # type: ignore


def test_build_main_planner_callbacks_delegates() -> None:
    captured = {}

    def fake_resolve_main_planner_callback_wrapper(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return {'maybe_trigger_plan_regeneration': lambda reason, force=False: None}

    out = rrpcpw.build_main_planner_callbacks(
        resolve_main_planner_callback_wrapper_fn=fake_resolve_main_planner_callback_wrapper,
        resolve_main_planner_callbacks_fn=lambda **kwargs: {},
        state=object(),
        toggles={},
        runs=[],
        followup_queue=[],
        precision_queue=[],
        planner_hints_cache_ref=[{}],
        last_regen_run_index_ref=[0],
        curated_plan_ref=[[]],
        active_plan_revision_ref=[0],
        active_plan_hash_ref=[''],
        reprioritize_queues_fn=lambda: None,
        summarize_planner_feedback_fn=lambda *args, **kwargs: {},
        load_planner_hints_fn=lambda *args, **kwargs: {},
        apply_planner_hints_refresh_fn=lambda *args, **kwargs: None,
        apply_plan_regeneration_fn=lambda *args, **kwargs: None,
        regenerate_runtime_plan_fn=lambda *args, **kwargs: {},
        apply_plan_reconciliation_fn=lambda *args, **kwargs: None,
        load_runtime_plan_meta_fn=lambda *args, **kwargs: {},
        load_curated_plan_fn=lambda *args, **kwargs: [],
        dedup_key_fn=lambda *args, **kwargs: 'k',
        log_event_fn=lambda *args, **kwargs: None,
    )
    assert 'maybe_trigger_plan_regeneration' in out
    assert callable(captured['resolve_main_planner_callbacks_fn'])
