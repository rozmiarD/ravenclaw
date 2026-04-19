from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class RuntimeRunnerContext:
    queue_coordinator: Any
    log_event_fn: Callable[..., None]
    read_runtime_control_state_fn: Callable[[], dict]
    read_runtime_owner_override_fn: Callable[..., bool]
    read_runtime_aggression_override_fn: Callable[..., int | None]
    apply_runtime_overrides_fn: Callable[..., tuple[bool, bool, int | None, int | None]]
    handle_post_run_actions_fn: Callable[..., tuple[int, dict]]
    prepare_curated_task_fn: Callable[..., dict | None]
    prepare_runtime_task_fn: Callable[..., dict | None]
    reprioritize_queues_fn: Callable[..., None]
    persist_recorded_run_fn: Callable[..., float]
    maybe_trigger_plan_regeneration_fn: Callable[[str], None]
    execute_runtime_task_fn: Callable[..., tuple[float, int]]
    resolve_main_loop_candidate_fn: Callable[..., dict]
    record_run_fn: Callable[..., None]
    persist_live_summary_fn: Callable[[], None]

    def enqueue_followup_task(self, task: dict, high_priority: bool = False) -> None:
        self.queue_coordinator.enqueue(task, high_priority=high_priority)

    def dequeue_next_task(self) -> dict | None:
        return self.queue_coordinator.dequeue()

    def requeue_task(self, task: dict) -> None:
        self.queue_coordinator.requeue_front(task)

    def refresh_runtime_overrides(self, owner_override_global: bool, last_override_state: bool, aggression_override_global: int | None, last_aggression_override: int | None) -> tuple[bool, bool, int | None, int | None]:
        return self.apply_runtime_overrides_fn(
            owner_override_global=owner_override_global,
            last_override_state=last_override_state,
            aggression_override_global=aggression_override_global,
            last_aggression_override=last_aggression_override,
            read_runtime_owner_override_fn=self.read_runtime_owner_override_fn,
            read_runtime_aggression_override_fn=self.read_runtime_aggression_override_fn,
            log_event_fn=self.log_event_fn,
        )

    def read_runtime_control_state(self) -> dict:
        try:
            state = self.read_runtime_control_state_fn()
            return state if isinstance(state, dict) else {}
        except Exception:
            return {}


def resolve_main_loop_selected(
    *,
    ctx: RuntimeRunnerContext,
    runs: list[dict],
    owner_override_global: bool,
    aggression_override_global: int | None,
    history: list[dict],
    scope_targets: list[str],
    normalize_runtime_task_fn: Callable[[dict], dict],
    unpack_queued_task_fn: Callable[..., dict],
    clamp_aggression_fn: Callable[[int], int],
    capped_aggression_fn: Callable[[str, str, int], int],
    propose_next_vector_fn: Callable[[list[dict]], tuple[str, str]],
) -> dict:
    selected = ctx.resolve_main_loop_candidate_fn(
        task=ctx.dequeue_next_task(),
        history=history,
        scope_targets=scope_targets,
        runs_count=len(runs),
        owner_override_global=owner_override_global,
        aggression_override_global=aggression_override_global,
        normalize_runtime_task_fn=normalize_runtime_task_fn,
        unpack_queued_task_fn=unpack_queued_task_fn,
        clamp_aggression_fn=clamp_aggression_fn,
        capped_aggression_fn=capped_aggression_fn,
        propose_next_vector_fn=propose_next_vector_fn,
        log_failure_fn=lambda error_msg: ctx.log_event_fn('BRAIN', 'propose_next_vector', 'failed', error_msg, actor='brain'),
        log_fallback_fn=lambda objective, target: ctx.log_event_fn('BRAIN', 'propose_next_vector_fallback', 'warning', f'fallback_objective={objective};fallback_target={target}', actor='brain', row_type='service'),
    )
    if str(selected.get('status') or '') == 'fatal':
        ctx.record_run_fn(runs, {'index': len(runs) + 1, 'error': str(selected.get('error_msg') or 'brain_proposal_failed')})
        ctx.persist_live_summary_fn()
    return selected
