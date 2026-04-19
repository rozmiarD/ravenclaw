from __future__ import annotations

from typing import Callable



def build_main_planner_callbacks(*, state, toggles: dict, runs: list[dict], followup_queue: list[dict], precision_queue: list[dict], planner_hints_cache_ref: list[dict], last_regen_run_index_ref: list[int], curated_plan_ref: list[list[dict]], active_plan_revision_ref: list[int], active_plan_hash_ref: list[str], reprioritize_queues_fn: Callable[[], None], summarize_planner_feedback_fn: Callable[..., dict], load_planner_hints_fn: Callable[[], dict], apply_planner_hints_refresh_fn: Callable[..., dict], apply_plan_regeneration_fn: Callable[..., int], regenerate_runtime_plan_fn: Callable[..., dict], apply_plan_reconciliation_fn: Callable[..., tuple], load_runtime_plan_meta_fn: Callable[[], dict], load_curated_plan_fn: Callable[[], list[dict]], dedup_key_fn: Callable[[str, str], tuple[str, str, str]], log_event_fn: Callable[..., None]) -> dict:
    def refresh_planner_hints_and_reprioritize(reason: str, tier: str = 'light') -> None:
        planner_feedback = summarize_planner_feedback_fn(runs=state.runs, host_state=state.host_state)
        planner_hints_cache_ref[0] = apply_planner_hints_refresh_fn(
            reason=reason,
            tier=tier,
            load_planner_hints_fn=load_planner_hints_fn,
            reprioritize_queues_fn=reprioritize_queues_fn,
            log_event_fn=log_event_fn,
            followup_queue_len=len(followup_queue),
            precision_queue_len=len(precision_queue),
            planner_feedback=planner_feedback,
        )

    def maybe_trigger_plan_regeneration(reason: str, force: bool = False) -> None:
        planner_feedback = summarize_planner_feedback_fn(runs=state.runs, host_state=state.host_state)
        last_regen_run_index_ref[0] = apply_plan_regeneration_fn(
            reason=reason,
            force=bool(force),
            toggles=toggles,
            runs_count=len(runs),
            last_regen_run_index=last_regen_run_index_ref[0],
            regenerate_runtime_plan_fn=regenerate_runtime_plan_fn,
            log_event_fn=log_event_fn,
            planner_feedback=planner_feedback,
        )

    def reconcile_active_plan_if_needed(reason: str) -> None:
        curated_plan, active_plan_revision, active_plan_hash, _changed = apply_plan_reconciliation_fn(
            reason=reason,
            curated_plan=curated_plan_ref[0],
            active_plan_revision=active_plan_revision_ref[0],
            active_plan_hash=active_plan_hash_ref[0],
            load_runtime_plan_meta_fn=load_runtime_plan_meta_fn,
            load_curated_plan_fn=load_curated_plan_fn,
            dedup_key_fn=dedup_key_fn,
            reprioritize_queues_fn=reprioritize_queues_fn,
            log_event_fn=log_event_fn,
            followup_queue_len=len(followup_queue),
            precision_queue_len=len(precision_queue),
        )
        curated_plan_ref[0] = curated_plan
        active_plan_revision_ref[0] = active_plan_revision
        active_plan_hash_ref[0] = active_plan_hash

    return {
        'refresh_planner_hints_and_reprioritize': refresh_planner_hints_and_reprioritize,
        'maybe_trigger_plan_regeneration': maybe_trigger_plan_regeneration,
        'reconcile_active_plan_if_needed': reconcile_active_plan_if_needed,
    }
