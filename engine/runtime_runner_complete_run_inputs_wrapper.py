from __future__ import annotations

from typing import Callable


def build_complete_runtime_run_inputs(*, build_complete_runtime_run_inputs_fn: Callable[..., object], task_ctx: dict, result: dict, qual: dict, classification: str, auditor: str, engine_status: str, success_eval_status: str, summary_text: str, reason_code: str, target: str, objective: str, aggression: int, owner_auth: bool, owner_override: bool, mode: str, confirm_total: int, promising: bool, run_info: dict, runner_deps, record_and_persist_run_fn: Callable[[dict], None], toggles: dict, state) -> object:
    return build_complete_runtime_run_inputs_fn(
        task_ctx=task_ctx,
        result=result,
        qual=qual,
        classification=classification,
        auditor=auditor,
        engine_status=engine_status,
        success_eval_status=success_eval_status,
        summary_text=summary_text,
        reason_code=reason_code,
        target=target,
        objective=objective,
        aggression=aggression,
        owner_auth=owner_auth,
        owner_override=owner_override,
        mode=mode,
        confirm_total=confirm_total,
        promising=promising,
        run_info=run_info,
        runner_deps=runner_deps,
        record_and_persist_run_fn=record_and_persist_run_fn,
        toggles=toggles,
        state=state,
    )
