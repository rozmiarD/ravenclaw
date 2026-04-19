from __future__ import annotations

from typing import Callable


def build_execute_runtime_task_inputs(*, build_execute_runtime_task_inputs_fn: Callable[..., object], execute_runtime_task_inputs_cls: Callable[..., object], task_ctx: dict, objective: str, target: str, mode: str, aggression: int, owner_auth: bool, owner_override: bool, plan_name: str | None, run_index: int, last_heartbeat_ts: float, state, execution_deps, host_family_owner_gate: dict, host_cooldown_until: dict, host_code000_streak: dict, host_code000_total: dict, host_403_streak: dict, host_fail_streak: dict, host_fail_count: dict, host_success_count: dict, code000_streak_threshold: int, code000_cooldown_sec: int, code000_session_cap: int, toggles: dict, qualification_mode: str, qualification_promising_threshold: str) -> object:
    return build_execute_runtime_task_inputs_fn(
        execute_runtime_task_inputs_cls=execute_runtime_task_inputs_cls,
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
        code000_streak_threshold=code000_streak_threshold,
        code000_cooldown_sec=code000_cooldown_sec,
        code000_session_cap=code000_session_cap,
        toggles=toggles,
        qualification_mode=qualification_mode,
        qualification_promising_threshold=qualification_promising_threshold,
    )
