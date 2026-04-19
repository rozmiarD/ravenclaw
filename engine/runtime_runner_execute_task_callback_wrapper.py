from __future__ import annotations

from typing import Callable


def build_main_execute_runtime_task_callback(*, build_main_execute_runtime_task_callback_fn: Callable[..., Callable[..., tuple[float, int]]], state, execution_deps, runner_deps, record_and_persist_run_fn: Callable[[dict], None], toggles: dict, host_family_owner_gate: dict, host_cooldown_until: dict, host_code000_streak: dict, host_code000_total: dict, host_403_streak: dict, host_fail_streak: dict, host_fail_count: dict, host_success_count: dict, code000_streak_threshold: int, code000_cooldown_sec: int, code000_session_cap: int, qualification_mode: str, qualification_promising_threshold: str, build_execute_runtime_task_inputs_fn: Callable[..., object], execute_runtime_task_pipeline_fn: Callable[..., tuple[float, tuple]], complete_execute_runtime_pipeline_result_fn: Callable[..., int]) -> Callable[..., tuple[float, int]]:
    return build_main_execute_runtime_task_callback_fn(
        state=state,
        execution_deps=execution_deps,
        runner_deps=runner_deps,
        record_and_persist_run_fn=record_and_persist_run_fn,
        toggles=toggles,
        host_family_owner_gate=host_family_owner_gate,
        host_cooldown_until=host_cooldown_until,
        host_code000_streak=host_code000_streak,
        host_code000_total=host_code000_total,
        host_403_streak=host_403_streak,
        host_fail_streak=host_fail_streak,
        host_fail_count=host_fail_count,
        host_success_count=host_success_count,
        code000_streak_threshold=code000_streak_threshold,
        code000_cooldown_sec=code000_cooldown_sec,
        code000_session_cap=code000_session_cap,
        qualification_mode=qualification_mode,
        qualification_promising_threshold=qualification_promising_threshold,
        build_execute_runtime_task_inputs_fn=build_execute_runtime_task_inputs_fn,
        execute_runtime_task_pipeline_fn=execute_runtime_task_pipeline_fn,
        complete_execute_runtime_pipeline_result_fn=complete_execute_runtime_pipeline_result_fn,
    )
