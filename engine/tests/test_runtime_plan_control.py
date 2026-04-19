from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from runtime_plan_control import maybe_trigger_plan_regeneration, reconcile_active_plan_if_needed, refresh_planner_hints_and_reprioritize  # type: ignore


def test_refresh_planner_hints_and_reprioritize_returns_hints_and_logs() -> None:
    events = []
    reprioritized = []
    hints = refresh_planner_hints_and_reprioritize(
        reason='high_signal_threshold',
        tier='light',
        load_planner_hints_fn=lambda: {'suggested_attack_vectors': ['a', 'b']},
        reprioritize_queues_fn=lambda: reprioritized.append(True),
        log_event_fn=lambda *args, **kwargs: events.append((args, kwargs)),
        followup_queue_len=3,
        precision_queue_len=1,
        planner_feedback={'recent_next_stage_hints': ['bounded_exploit_proof'], 'recent_target_surface_rationale': ['authenticated_or_boundary_mapping']},
    )
    assert hints['suggested_attack_vectors'] == ['a', 'b']
    assert reprioritized == [True]
    assert any(args[1] == 'contextual_reconsult_applied' for args, _kwargs in events)
    assert any('stage_hints=bounded_exploit_proof' in args[3] for args, _kwargs in events)


def test_maybe_trigger_plan_regeneration_respects_gap_and_updates_index() -> None:
    events = []
    new_idx = maybe_trigger_plan_regeneration(
        reason='promising_host_shift',
        force=False,
        toggles={'dynamic_plan_adaptation': True, 'aggressive_adaptation': False},
        runs_count=10,
        last_regen_run_index=7,
        regenerate_runtime_plan_fn=lambda reason: {'ok': True, 'plan_revision': 4, 'added_tasks': 2, 'deprecated_tasks': 1},
        log_event_fn=lambda *args, **kwargs: events.append((args, kwargs)),
        planner_feedback={'recent_next_stage_hints': ['bounded_exploit_proof'], 'recent_target_surface_rationale': ['authenticated_or_boundary_mapping']},
    )
    assert new_idx == 10
    assert any(args[1] == 'plan_regenerated' for args, _kwargs in events)


def test_reconcile_active_plan_if_needed_updates_plan_and_logs() -> None:
    events = []
    curated_plan = [{'objective': 'Recon', 'target': 'https://a.example.com/'}]
    new_plan, rev, plan_hash, changed = reconcile_active_plan_if_needed(
        reason='post_regen',
        curated_plan=curated_plan,
        active_plan_revision=1,
        active_plan_hash='old',
        load_runtime_plan_meta_fn=lambda: {'plan_revision': 2, 'plan_hash': 'new'},
        load_curated_plan_fn=lambda: [{'objective': 'Probe', 'target': 'https://b.example.com/'}],
        dedup_key_fn=lambda objective, target: (objective, target),
        reprioritize_queues_fn=lambda: None,
        log_event_fn=lambda *args, **kwargs: events.append((args, kwargs)),
        followup_queue_len=2,
        precision_queue_len=1,
    )
    assert changed is True
    assert rev == 2
    assert plan_hash == 'new'
    assert new_plan[0]['target'] == 'https://b.example.com/'
    assert any(args[1] == 'plan_reconciled' for args, _kwargs in events)
