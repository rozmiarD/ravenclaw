from __future__ import annotations

from typing import Callable


def build_main_planner_callbacks(*, resolve_main_planner_callbacks_fn: Callable[..., dict], state, toggles: dict, runs: list[dict], followup_queue: list[dict], precision_queue: list[dict], planner_hints_cache_ref: list[dict], last_regen_run_index_ref: list[int], curated_plan_ref: list[list[dict]], active_plan_revision_ref: list[int], active_plan_hash_ref: list[str], reprioritize_queues_fn: Callable[[], None], summarize_planner_feedback_fn: Callable[..., dict], load_planner_hints_fn: Callable[..., dict], apply_planner_hints_refresh_fn: Callable[..., None], apply_plan_regeneration_fn: Callable[..., None], regenerate_runtime_plan_fn: Callable[..., list[dict]], apply_plan_reconciliation_fn: Callable[..., None], load_runtime_plan_meta_fn: Callable[..., dict], load_curated_plan_fn: Callable[..., list[dict]], dedup_key_fn: Callable[..., str], log_event_fn: Callable[..., None]) -> dict:
    return resolve_main_planner_callbacks_fn(
        state=state,
        toggles=toggles,
        runs=runs,
        followup_queue=followup_queue,
        precision_queue=precision_queue,
        planner_hints_cache_ref=planner_hints_cache_ref,
        last_regen_run_index_ref=last_regen_run_index_ref,
        curated_plan_ref=curated_plan_ref,
        active_plan_revision_ref=active_plan_revision_ref,
        active_plan_hash_ref=active_plan_hash_ref,
        reprioritize_queues_fn=reprioritize_queues_fn,
        summarize_planner_feedback_fn=summarize_planner_feedback_fn,
        load_planner_hints_fn=load_planner_hints_fn,
        apply_planner_hints_refresh_fn=apply_planner_hints_refresh_fn,
        apply_plan_regeneration_fn=apply_plan_regeneration_fn,
        regenerate_runtime_plan_fn=regenerate_runtime_plan_fn,
        apply_plan_reconciliation_fn=apply_plan_reconciliation_fn,
        load_runtime_plan_meta_fn=load_runtime_plan_meta_fn,
        load_curated_plan_fn=load_curated_plan_fn,
        dedup_key_fn=dedup_key_fn,
        log_event_fn=log_event_fn,
    )
