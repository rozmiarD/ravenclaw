from __future__ import annotations

from typing import Callable


def build_main_prepare_callbacks(*, build_main_prepare_callbacks_fn: Callable[..., dict], precheck_ctx, scheduled_keys: set, toggles: dict, state, planner_hints_cache_ref: list[dict], attack_family_fn: Callable[..., str], prepare_curated_task_fn: Callable[..., dict | None], prepare_runtime_task_fn: Callable[..., dict | None], capped_aggression_fn: Callable[..., int], family_allowed_for_host_stage_fn: Callable[..., bool], planner_vector_weight_fn: Callable[..., float], host_from_target_fn: Callable[[str], str], apply_queue_reprioritization_fn: Callable[..., None]) -> dict:
    return build_main_prepare_callbacks_fn(
        precheck_ctx=precheck_ctx,
        scheduled_keys=scheduled_keys,
        toggles=toggles,
        state=state,
        planner_hints_cache_ref=planner_hints_cache_ref,
        attack_family_fn=attack_family_fn,
        prepare_curated_task_fn=prepare_curated_task_fn,
        prepare_runtime_task_fn=prepare_runtime_task_fn,
        capped_aggression_fn=capped_aggression_fn,
        family_allowed_for_host_stage_fn=family_allowed_for_host_stage_fn,
        planner_vector_weight_fn=planner_vector_weight_fn,
        host_from_target_fn=host_from_target_fn,
        apply_queue_reprioritization_fn=apply_queue_reprioritization_fn,
    )
