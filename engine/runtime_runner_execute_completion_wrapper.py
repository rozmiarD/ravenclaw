from __future__ import annotations

from typing import Callable


def complete_execute_runtime_pipeline_result(*, complete_execute_runtime_pipeline_result_fn: Callable[..., int], task_ctx: dict, target: str, objective: str, aggression: int, owner_auth: bool, owner_override: bool, mode: str, confirm_total: int, pipeline_result: tuple, runner_deps, record_and_persist_run_fn: Callable[[dict], None], toggles: dict, state, build_complete_runtime_run_inputs_fn: Callable[..., object], complete_runtime_run_fn: Callable[..., tuple[int, dict, object]]) -> int:
    return complete_execute_runtime_pipeline_result_fn(
        task_ctx=task_ctx,
        target=target,
        objective=objective,
        aggression=aggression,
        owner_auth=owner_auth,
        owner_override=owner_override,
        mode=mode,
        confirm_total=confirm_total,
        pipeline_result=pipeline_result,
        runner_deps=runner_deps,
        record_and_persist_run_fn=record_and_persist_run_fn,
        toggles=toggles,
        state=state,
        build_complete_runtime_run_inputs_fn=build_complete_runtime_run_inputs_fn,
        complete_runtime_run_fn=complete_runtime_run_fn,
    )
