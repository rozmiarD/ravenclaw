from __future__ import annotations

from typing import Callable

from aggression_policy import clamp_aggression



def reprioritize_main_prepare_queues(*, state, toggles: dict, planner_hints_cache_ref: list[dict], attack_family_fn: Callable[[str, str, str], str], family_allowed_for_host_stage_fn: Callable[..., bool], planner_vector_weight_fn: Callable[[dict, dict], float], host_from_target_fn: Callable[[str], str], apply_queue_reprioritization_fn: Callable[..., None]) -> None:
    apply_queue_reprioritization_fn(
        followup_queue=state.followup_queue,
        precision_queue=state.precision_queue,
        runs=state.runs,
        toggles=toggles,
        planner_hints_cache=planner_hints_cache_ref[0],
        host_state=state.host_state,
        host_family_owner_gate=state.host_family_owner_gate,
        attack_family_fn=attack_family_fn,
        family_allowed_for_host_stage_fn=family_allowed_for_host_stage_fn,
        planner_vector_weight_fn=planner_vector_weight_fn,
        host_from_target_fn=host_from_target_fn,
    )



def prepare_task_precheck_from_context(precheck_ctx, *, objective: str, target: str, mode: str, task_family: str, dedup_mode_suffix: bool, runtime_task: dict | None = None):
    return precheck_ctx.prepare_task_precheck(
        objective=str(objective),
        target=str(target),
        mode=str(mode),
        task_family=str(task_family or ''),
        dedup_mode_suffix=dedup_mode_suffix,
        runtime_task=(runtime_task if isinstance(runtime_task, dict) else {}),
    )



def build_main_prepare_callbacks(*, precheck_ctx, scheduled_keys: set, toggles: dict, state, planner_hints_cache_ref: list[dict], attack_family_fn: Callable[[str, str, str], str], prepare_curated_task_fn: Callable[..., dict | None], prepare_runtime_task_fn: Callable[..., dict | None], capped_aggression_fn: Callable[[str, str, int], int], family_allowed_for_host_stage_fn: Callable[..., bool], planner_vector_weight_fn: Callable[[dict, dict], float], host_from_target_fn: Callable[[str], str], apply_queue_reprioritization_fn: Callable[..., None]) -> dict:
    def prepare_task_precheck(*, objective: str, target: str, mode: str, task_family: str, dedup_mode_suffix: bool, runtime_task: dict | None = None):
        return prepare_task_precheck_from_context(
            precheck_ctx,
            objective=objective,
            target=target,
            mode=mode,
            task_family=task_family,
            dedup_mode_suffix=dedup_mode_suffix,
            runtime_task=runtime_task,
        )

    def prepare_curated_task_cb(entry: dict, aggression_override_global: int | None) -> dict | None:
        return prepare_curated_task_fn(
            entry,
            aggression_override_global=aggression_override_global,
            prepare_task_precheck_fn=prepare_task_precheck,
            clamp_aggression_fn=clamp_aggression,
            capped_aggression_fn=capped_aggression_fn,
        )

    def prepare_runtime_task_cb(task: dict | None, objective: str, target: str, mode: str, aggression: int, owner_auth: bool, owner_override: bool, plan_name: str | None):
        return prepare_runtime_task_fn(
            task,
            objective=str(objective),
            target=str(target),
            mode=str(mode),
            aggression=int(aggression),
            owner_auth=bool(owner_auth),
            owner_override=bool(owner_override),
            plan_name=plan_name,
            prepare_task_precheck_fn=prepare_task_precheck,
            scheduled_keys=scheduled_keys,
            attack_family_fn=attack_family_fn,
        )

    def reprioritize_queues() -> None:
        reprioritize_main_prepare_queues(
            state=state,
            toggles=toggles,
            planner_hints_cache_ref=planner_hints_cache_ref,
            attack_family_fn=attack_family_fn,
            family_allowed_for_host_stage_fn=family_allowed_for_host_stage_fn,
            planner_vector_weight_fn=planner_vector_weight_fn,
            host_from_target_fn=host_from_target_fn,
            apply_queue_reprioritization_fn=apply_queue_reprioritization_fn,
        )

    return {
        'prepare_task_precheck': prepare_task_precheck,
        'prepare_curated_task': prepare_curated_task_cb,
        'prepare_runtime_task': prepare_runtime_task_cb,
        'reprioritize_queues': reprioritize_queues,
    }
