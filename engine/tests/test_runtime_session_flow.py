from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from runtime_session_flow import run_runtime_session  # type: ignore
from runtime_prepare_deps import RuntimePrepareDeps  # type: ignore
from runtime_session_state import RuntimeSessionState  # type: ignore


class DummyRunnerCtx:
    def refresh_runtime_overrides(self, *args, **kwargs):
        return (False, False, None, None)

    def dequeue_next_task(self):
        return None

    def requeue_task(self, *args, **kwargs):
        return None

    def read_runtime_owner_override_fn(self, default=False):
        return False

    def read_runtime_aggression_override_fn(self):
        return None


def test_run_runtime_session_threads_state_through_curated_and_main_loops() -> None:
    state = RuntimeSessionState(
        runs=[], history=[], host_state={}, curated_plan=[], runtime_plan_meta={}, host_dns_cache={}, toggles={}, planner_hints_cache={}
    )
    prepare_deps = RuntimePrepareDeps(
        precheck_and_prepare_task_fn=lambda **kwargs: {},
        prepare_curated_task_fn=lambda *args, **kwargs: None,
        prepare_runtime_task_fn=lambda *args, **kwargs: None,
    )

    seen = {}

    def curated(**kwargs):
        seen['target_load_limit'] = kwargs.get('target_load_limit')
        return (11.0, 2, 3, False)

    def main(**kwargs):
        return (12.0, 4, False)

    run_runtime_session(
        state=state,
        max_runs=5,
        target_load_limit=9,
        time_budget_min=10,
        scope_targets=['a.example.com'],
        normalize_runtime_task_fn=lambda task: task,
        reconcile_active_plan_if_needed_fn=lambda reason: None,
        runner_ctx=DummyRunnerCtx(),
        maybe_preempt_curated_entry_fn=lambda entry, **kwargs: (entry, False),
        dedup_key_fn=lambda *args: ('k',),
        build_deduped_target_plan_fn=lambda raw_plan, dedup_key_fn: raw_plan,
        prepare_deps=prepare_deps,
        execute_runtime_task_fn=lambda *args, **kwargs: (0.0, 0),
        propose_next_vector_fn=lambda history: ('Probe', 'https://a.example.com/'),
        unpack_queued_task_fn=lambda task, **kwargs: task,
        clamp_aggression_fn=lambda n: n,
        capped_aggression_fn=lambda family, target, aggression: aggression,
        run_curated_loop_fn=curated,
        run_main_loop_fn=main,
        log_event_fn=lambda *args, **kwargs: None,
        preempt_in_curated=True,
        run_started=__import__('datetime').datetime.now(__import__('datetime').timezone.utc),
    )
    assert state.last_heartbeat_ts == 12.0
    assert state.confirm_total == 4
    assert state.idx == 3
    assert seen['target_load_limit'] == 9
