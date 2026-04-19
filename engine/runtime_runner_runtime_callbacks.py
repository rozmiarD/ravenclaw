from __future__ import annotations

from datetime import datetime
from typing import Callable


def persist_main_runtime_snapshot(*, campaign_validation: dict, run_started: datetime, max_runs: int, time_budget_min: int, retry_policy: str, runs: list[dict], followup_queue: list[dict], precision_queue: list[dict], precheck_skip_count_ref: list[int], dns_skip_count: dict[str, int], host_cooldown_skip_count: dict[str, int], execution_gate_skip_count: dict[str, int], quality_telemetry: dict, host_state: dict, out_path: str, save_queue_state_fn: Callable[..., None], current_campaign_key_fn: Callable[[], str], runtime_snapshot_path: str, load_runtime_plan_meta_fn: Callable[[], dict], persist_live_snapshot_fn: Callable[..., None], warn_fn: Callable[[str], None]) -> None:
    try:
        persist_live_snapshot_fn(
            out_path=out_path,
            save_queue_state_fn=save_queue_state_fn,
            campaign_key=current_campaign_key_fn(),
            campaign_validation=campaign_validation,
            run_started=run_started,
            max_runs=max_runs,
            time_budget_min=time_budget_min,
            retry_policy=retry_policy,
            runs=runs,
            followup_queue=followup_queue,
            precision_queue=precision_queue,
            precheck_skip_count=precheck_skip_count_ref[0],
            dns_skip_count=dns_skip_count,
            host_cooldown_skip_count=host_cooldown_skip_count,
            execution_gate_skip_count=execution_gate_skip_count,
            quality_telemetry=quality_telemetry,
            runtime_snapshot_path=runtime_snapshot_path,
            runtime_plan_meta=load_runtime_plan_meta_fn(),
            host_state=host_state,
        )
    except Exception as exc:  # noqa: BLE001
        warn_fn(f"failed to persist live runtime snapshot to {out_path}: {exc}")


def refresh_main_runtime_overrides(owner_override_global: bool, last_override_state: bool, aggression_override_global: int | None, last_aggression_override: int | None, *, apply_runtime_overrides_fn: Callable[..., tuple[bool, bool, int | None, int | None]], read_runtime_owner_override_fn: Callable[..., bool], read_runtime_aggression_override_fn: Callable[..., int | None], log_event_fn: Callable[..., None]) -> tuple[bool, bool, int | None, int | None]:
    return apply_runtime_overrides_fn(
        owner_override_global=owner_override_global,
        last_override_state=last_override_state,
        aggression_override_global=aggression_override_global,
        last_aggression_override=last_aggression_override,
        read_runtime_owner_override_fn=read_runtime_owner_override_fn,
        read_runtime_aggression_override_fn=read_runtime_aggression_override_fn,
        log_event_fn=log_event_fn,
    )


def build_main_runtime_callbacks(*, campaign_validation: dict, run_started: datetime, max_runs: int, time_budget_min: int, retry_policy: str, runs: list[dict], followup_queue: list[dict], precision_queue: list[dict], precheck_skip_count_ref: list[int], dns_skip_count: dict[str, int], host_cooldown_skip_count: dict[str, int], execution_gate_skip_count: dict[str, int], quality_telemetry: dict, host_state: dict, queue_coordinator, persist_main_runtime_snapshot_fn: Callable[..., None], refresh_main_runtime_overrides_fn: Callable[..., tuple[bool, bool, int | None, int | None]]) -> dict:
    def persist_live_summary() -> None:
        persist_main_runtime_snapshot_fn(
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
        )

    def enqueue_followup_task(task: dict, high_priority: bool = False) -> None:
        queue_coordinator.enqueue(task, high_priority=high_priority)

    def dequeue_next_task() -> dict | None:
        return queue_coordinator.dequeue()

    def refresh_runtime_overrides(owner_override_global: bool, last_override_state: bool, aggression_override_global: int | None, last_aggression_override: int | None) -> tuple[bool, bool, int | None, int | None]:
        return refresh_main_runtime_overrides_fn(
            owner_override_global,
            last_override_state,
            aggression_override_global,
            last_aggression_override,
        )

    return {
        'persist_live_summary': persist_live_summary,
        'enqueue_followup_task': enqueue_followup_task,
        'dequeue_next_task': dequeue_next_task,
        'refresh_runtime_overrides': refresh_runtime_overrides,
    }


def build_main_precheck_hooks(*, precheck_skip_count_ref: list[int], flush_precheck_summary_fn: Callable[[], None], flush_dns_skip_summary_fn: Callable[[], None], flush_host_cooldown_summary_fn: Callable[[], None], flush_execution_gate_summary_fn: Callable[[], None]) -> dict:
    def inc_precheck_skip() -> None:
        precheck_skip_count_ref[0] += 1

    def on_executed_key() -> None:
        flush_precheck_summary_fn()
        flush_dns_skip_summary_fn()
        flush_host_cooldown_summary_fn()
        flush_execution_gate_summary_fn()

    return {
        'inc_precheck_skip': inc_precheck_skip,
        'on_executed_key': on_executed_key,
    }
