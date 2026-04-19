from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from runtime_run_completion import complete_runtime_run  # type: ignore
from runtime_runner_deps import RuntimeRunnerDeps  # type: ignore
from runtime_session_state import RuntimeSessionState  # type: ignore


@dataclass
class CompleteRuntimeRunInputs:
    run_info: dict
    task_ctx: dict
    result: dict
    qual: dict
    classification: str
    auditor: str
    engine_status: str
    success_eval_status: str
    summary_text: str
    reason_code: str
    target: str
    objective: str
    aggression: int
    owner_auth: bool
    owner_override: bool
    mode: str
    confirm_total: int
    promising: bool
    runtime_decision: dict
    deps: RuntimeRunnerDeps
    record_and_persist_run_fn: Callable[[dict], None]
    toggles: dict
    runs: list[dict]
    promising_hits_ref: list[int]
    host_state: dict


@dataclass
class ExecuteRuntimePipelineCompletionInputs:
    task_ctx: dict
    target: str
    objective: str
    aggression: int
    owner_auth: bool
    owner_override: bool
    mode: str
    confirm_total: int
    pipeline_result: tuple
    runner_deps: RuntimeRunnerDeps
    record_and_persist_run_fn: Callable[[dict], None]
    toggles: dict
    state: RuntimeSessionState


def build_complete_runtime_run_inputs(*, task_ctx: dict, result: dict, qual: dict, classification: str, auditor: str, engine_status: str, success_eval_status: str, summary_text: str, reason_code: str, target: str, objective: str, aggression: int, owner_auth: bool, owner_override: bool, mode: str, confirm_total: int, promising: bool, run_info: dict, runner_deps: RuntimeRunnerDeps, record_and_persist_run_fn: Callable[[dict], None], toggles: dict, state: RuntimeSessionState) -> CompleteRuntimeRunInputs:
    return CompleteRuntimeRunInputs(
        run_info=run_info,
        task_ctx=task_ctx,
        result=(result if isinstance(result, dict) else {}),
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
        mode=str(mode),
        confirm_total=int(confirm_total),
        promising=bool(promising),
        runtime_decision=(run_info.get('runtime_decision') if isinstance(run_info.get('runtime_decision'), dict) else {}),
        deps=runner_deps,
        record_and_persist_run_fn=record_and_persist_run_fn,
        toggles=toggles,
        runs=state.runs,
        promising_hits_ref=state.promising_hits_ref,
        host_state=state.host_state,
    )


def complete_execute_runtime_pipeline_result(*, task_ctx: dict, target: str, objective: str, aggression: int, owner_auth: bool, owner_override: bool, mode: str, confirm_total: int, pipeline_result: tuple, runner_deps: RuntimeRunnerDeps, record_and_persist_run_fn: Callable[[dict], None], toggles: dict, state: RuntimeSessionState, build_complete_runtime_run_inputs_fn: Callable[..., CompleteRuntimeRunInputs] = build_complete_runtime_run_inputs, complete_runtime_run_fn: Callable[..., tuple[int, dict, str | None]] = complete_runtime_run) -> int:
    result, _classification_unused, auditor, engine_status, _summary_text_unused, _error_flag, post, qual, promising, run_info = pipeline_result
    complete_inputs = build_complete_runtime_run_inputs_fn(
        task_ctx=task_ctx,
        result=result,
        qual=qual,
        classification=str(post['classification']),
        auditor=auditor,
        engine_status=engine_status,
        success_eval_status=str(post['success_eval_status']),
        summary_text=str(post['summary_text']),
        reason_code=str(post['reason_code']),
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
    confirm_total_out, _run_info_out, _tier = complete_runtime_run_fn(**vars(complete_inputs))
    return confirm_total_out


def build_main_execute_runtime_task_callback(*, state: RuntimeSessionState, execution_deps: Any, runner_deps: RuntimeRunnerDeps, record_and_persist_run_fn: Callable[[dict], None], toggles: dict, host_family_owner_gate: dict, host_cooldown_until: dict, host_code000_streak: dict, host_code000_total: dict, host_403_streak: dict, host_fail_streak: dict, host_fail_count: dict, host_success_count: dict, code000_streak_threshold: int, code000_cooldown_sec: int, code000_session_cap: int, qualification_mode: str, qualification_promising_threshold: str, build_execute_runtime_task_inputs_fn: Callable[..., Any], execute_runtime_task_pipeline_fn: Callable[..., tuple[float, tuple]], complete_execute_runtime_pipeline_result_fn: Callable[..., int] = complete_execute_runtime_pipeline_result) -> Callable[..., tuple[float, int]]:
    def execute_runtime_task_cb(task_ctx: dict, *, objective: str, target: str, mode: str, aggression: int, owner_auth: bool, owner_override: bool, plan_name: str | None, run_index: int, last_heartbeat_ts: float, confirm_total: int) -> tuple[float, int]:
        execute_inputs = build_execute_runtime_task_inputs_fn(
            task_ctx=task_ctx,
            objective=objective,
            target=target,
            mode=mode,
            aggression=aggression,
            owner_auth=owner_auth,
            owner_override=owner_override,
            plan_name=plan_name,
            run_index=run_index,
            last_heartbeat_ts=last_heartbeat_ts,
            confirm_total=confirm_total,
            state=state,
            execution_deps=execution_deps,
            host_family_owner_gate=host_family_owner_gate,
            host_cooldown_until=host_cooldown_until,
            host_code000_streak=host_code000_streak,
            host_code000_total=host_code000_total,
            host_403_streak=host_403_streak,
            host_fail_streak=host_fail_streak,
            host_fail_count=host_fail_count,
            host_success_count=host_success_count,
            code000_streak_threshold=int(code000_streak_threshold),
            code000_cooldown_sec=int(code000_cooldown_sec),
            code000_session_cap=int(code000_session_cap),
            toggles=toggles,
            qualification_mode=qualification_mode,
            qualification_promising_threshold=qualification_promising_threshold,
        )
        last_heartbeat_ts_out, pipeline_result = execute_runtime_task_pipeline_fn(**vars(execute_inputs))
        confirm_total_out = complete_execute_runtime_pipeline_result_fn(
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
        )
        return last_heartbeat_ts_out, confirm_total_out

    return execute_runtime_task_cb
