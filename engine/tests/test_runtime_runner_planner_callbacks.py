from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_runner_planner_callbacks as rrpl  # type: ignore


class FakeState:
    def __init__(self) -> None:
        self.runs = [{'objective': 'Probe', 'target': 'https://api.example.com/'}]
        self.host_state = {'api.example.com': {'ok': True}}



def test_build_main_planner_callbacks_updates_refs_and_delegates() -> None:
    state = FakeState()
    planner_hints_cache_ref = [{}]
    last_regen_run_index_ref = [1]
    curated_plan_ref = [[{'target': 'https://api.example.com/'}]]
    active_plan_revision_ref = [2]
    active_plan_hash_ref = ['old']
    captured = {}

    def fake_summarize_planner_feedback(**kwargs):  # type: ignore[no-untyped-def]
        captured.setdefault('summaries', []).append(kwargs)
        return {'quality': 'ok'}

    def fake_apply_planner_hints_refresh(**kwargs):  # type: ignore[no-untyped-def]
        captured['refresh'] = kwargs
        return {'fresh': True}

    def fake_apply_plan_regeneration(**kwargs):  # type: ignore[no-untyped-def]
        captured['regen'] = kwargs
        return 9

    def fake_apply_plan_reconciliation(**kwargs):  # type: ignore[no-untyped-def]
        captured['reconcile'] = kwargs
        return ([{'target': 'https://new.example.com/'}], 7, 'new-hash', True)

    callbacks = rrpl.build_main_planner_callbacks(
        state=state,
        toggles={'planner': True},
        runs=state.runs,
        followup_queue=[{'kind': 'followup'}],
        precision_queue=[{'kind': 'precision'}],
        planner_hints_cache_ref=planner_hints_cache_ref,
        last_regen_run_index_ref=last_regen_run_index_ref,
        curated_plan_ref=curated_plan_ref,
        active_plan_revision_ref=active_plan_revision_ref,
        active_plan_hash_ref=active_plan_hash_ref,
        reprioritize_queues_fn=lambda: None,
        summarize_planner_feedback_fn=fake_summarize_planner_feedback,
        load_planner_hints_fn=lambda: {'hint': True},
        apply_planner_hints_refresh_fn=fake_apply_planner_hints_refresh,
        apply_plan_regeneration_fn=fake_apply_plan_regeneration,
        regenerate_runtime_plan_fn=lambda reason='auto_runner': {'ok': True, 'reason': reason},
        apply_plan_reconciliation_fn=fake_apply_plan_reconciliation,
        load_runtime_plan_meta_fn=lambda: {'plan_revision': 7},
        load_curated_plan_fn=lambda: [{'target': 'https://new.example.com/'}],
        dedup_key_fn=lambda objective, target: ('k', objective, target),
        log_event_fn=lambda *args, **kwargs: None,
    )

    callbacks['refresh_planner_hints_and_reprioritize']('cycle', tier='deep')
    callbacks['maybe_trigger_plan_regeneration']('regen', force=True)
    callbacks['reconcile_active_plan_if_needed']('reconcile')

    assert planner_hints_cache_ref[0] == {'fresh': True}
    assert last_regen_run_index_ref[0] == 9
    assert curated_plan_ref[0] == [{'target': 'https://new.example.com/'}]
    assert active_plan_revision_ref[0] == 7
    assert active_plan_hash_ref[0] == 'new-hash'
    assert captured['refresh']['reason'] == 'cycle'
    assert captured['refresh']['tier'] == 'deep'
    assert captured['regen']['reason'] == 'regen'
    assert captured['regen']['force'] is True
    assert captured['reconcile']['reason'] == 'reconcile'
