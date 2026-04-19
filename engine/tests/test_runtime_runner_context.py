from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from runtime_runner_context import RuntimeRunnerContext, resolve_main_loop_selected  # type: ignore


class DummyQueue:
    def __init__(self) -> None:
        self.items = []

    def enqueue(self, task, high_priority: bool = False) -> None:
        self.items.append((task, high_priority))

    def dequeue(self):
        return {'objective': 'Recon', 'target': 'https://a.example.com/'}


def _ctx(resolve_fn):
    return RuntimeRunnerContext(
        queue_coordinator=DummyQueue(),
        log_event_fn=lambda *args, **kwargs: None,
        read_runtime_control_state_fn=lambda: {},
        read_runtime_owner_override_fn=lambda default=False: False,
        read_runtime_aggression_override_fn=lambda: None,
        apply_runtime_overrides_fn=lambda **kwargs: (False, False, None, None),
        handle_post_run_actions_fn=lambda **kwargs: (0, {}),
        prepare_curated_task_fn=lambda *args, **kwargs: None,
        prepare_runtime_task_fn=lambda *args, **kwargs: None,
        reprioritize_queues_fn=lambda **kwargs: None,
        persist_recorded_run_fn=lambda **kwargs: 0.0,
        maybe_trigger_plan_regeneration_fn=lambda reason: None,
        execute_runtime_task_fn=lambda *args, **kwargs: (0.0, 0),
        resolve_main_loop_candidate_fn=resolve_fn,
        record_run_fn=lambda runs, row: runs.append(row),
        persist_live_summary_fn=lambda: None,
    )


def test_context_refresh_runtime_overrides_delegates() -> None:
    seen = {}
    ctx = _ctx(lambda **kwargs: {})
    ctx.apply_runtime_overrides_fn = lambda **kwargs: seen.update(kwargs) or (True, True, 4, 4)
    out = ctx.refresh_runtime_overrides(False, False, None, None)
    assert out == (True, True, 4, 4)
    assert callable(seen['read_runtime_owner_override_fn'])


def test_resolve_main_loop_selected_records_fatal_error() -> None:
    runs = []
    ctx = _ctx(lambda **kwargs: {'status': 'fatal', 'error_msg': 'brain_proposal_failed'})
    out = resolve_main_loop_selected(
        ctx=ctx,
        runs=runs,
        owner_override_global=False,
        aggression_override_global=None,
        history=[],
        scope_targets=['a.example.com'],
        normalize_runtime_task_fn=lambda task: task,
        unpack_queued_task_fn=lambda task, **kwargs: task,
        clamp_aggression_fn=lambda n: n,
        capped_aggression_fn=lambda family, target, aggression: aggression,
        propose_next_vector_fn=lambda history: ('Probe', 'https://a.example.com/'),
    )
    assert out['status'] == 'fatal'
    assert runs[0]['error'] == 'brain_proposal_failed'
