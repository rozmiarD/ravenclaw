from __future__ import annotations

from typing import Callable


def persist_main_runtime_snapshot(*, persist_main_runtime_snapshot_fn: Callable[..., None], campaign_validation: dict, run_started, max_runs: int, time_budget_min: int, retry_policy: str, runs: list[dict], followup_queue: list[dict], precision_queue: list[dict], precheck_skip_count_ref: list[int], dns_skip_count: dict[str, int], host_cooldown_skip_count: dict[str, int], execution_gate_skip_count: dict[str, int], quality_telemetry: dict, host_state: dict, out_path: str, save_queue_state_fn: Callable[..., None], current_campaign_key_fn: Callable[[], str], runtime_snapshot_path: str, load_runtime_plan_meta_fn: Callable[..., dict], persist_live_snapshot_fn: Callable[..., None], warn_fn: Callable[..., None]) -> None:
    return persist_main_runtime_snapshot_fn(
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
        out_path=out_path,
        save_queue_state_fn=save_queue_state_fn,
        current_campaign_key_fn=current_campaign_key_fn,
        runtime_snapshot_path=runtime_snapshot_path,
        load_runtime_plan_meta_fn=load_runtime_plan_meta_fn,
        persist_live_snapshot_fn=persist_live_snapshot_fn,
        warn_fn=warn_fn,
    )
