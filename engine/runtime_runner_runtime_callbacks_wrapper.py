from __future__ import annotations

from typing import Callable


def build_main_runtime_callbacks(*, build_main_runtime_callbacks_fn: Callable[..., dict], campaign_validation: dict, run_started, max_runs: int, time_budget_min: int, retry_policy: str, runs: list[dict], followup_queue: list[dict], precision_queue: list[dict], precheck_skip_count_ref: list[int], dns_skip_count: dict[str, int], host_cooldown_skip_count: dict[str, int], execution_gate_skip_count: dict[str, int], quality_telemetry: dict, host_state: dict, queue_coordinator, persist_main_runtime_snapshot_fn: Callable[..., None], refresh_main_runtime_overrides_fn: Callable[..., tuple]) -> dict:
    return build_main_runtime_callbacks_fn(
        campaign_validation=campaign_validation,
        run_started=run_started,
        max_runs=max_runs,
        time_budget_min=time_budget_min,
        retry_policy=retry_policy,
        runs=runs,
        followup_queue=followup_queue,
        precision_queue=precision_queue,
        precheck_skip_count_ref=precheck_skip_count_ref,
        dns_skip_count=dns_skip_count,
        host_cooldown_skip_count=host_cooldown_skip_count,
        execution_gate_skip_count=execution_gate_skip_count,
        quality_telemetry=quality_telemetry,
        host_state=host_state,
        queue_coordinator=queue_coordinator,
        persist_main_runtime_snapshot_fn=persist_main_runtime_snapshot_fn,
        refresh_main_runtime_overrides_fn=refresh_main_runtime_overrides_fn,
    )
