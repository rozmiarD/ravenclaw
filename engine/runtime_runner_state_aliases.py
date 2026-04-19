from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass
class MainStateAliases:
    followup_queue: list[dict]
    host_rr: dict
    followup_counts: dict
    confirm_counts: dict
    confirm_recent: dict
    confirm_class_counts: dict
    confirm_total: int
    quality_telemetry: dict
    scheduled_keys: set
    retry_counts: dict
    precheck_skip_count: int
    followup_recent: dict
    precheck_skip_examples: list[str]
    unresolved_hosts: set[str]
    dns_skip_count: dict[str, int]
    execution_gate_skip_count: dict[str, int]
    execution_gate_skip_examples: dict[str, list[str]]
    host_cooldown_until: dict[str, float]
    host_cooldown_skip_count: dict[str, int]
    precision_queue: list[dict]
    deep_budget: dict
    host_fail_streak: dict[str, int]
    host_success_count: dict[str, int]
    host_fail_count: dict[str, int]
    host_weak_count: dict[str, int]
    host_family_owner_gate: dict
    host_code000_streak: dict[str, int]
    host_code000_total: dict[str, int]
    host_403_streak: dict[str, int]
    host_precheck_burst: dict[str, int]
    last_persist_ts: float


def build_main_state_aliases(state) -> MainStateAliases:
    return MainStateAliases(
        followup_queue=state.followup_queue,
        host_rr=state.host_rr,
        followup_counts=state.followup_counts,
        confirm_counts=state.confirm_counts,
        confirm_recent=state.confirm_recent,
        confirm_class_counts=state.confirm_class_counts,
        confirm_total=int(state.confirm_total),
        quality_telemetry=state.quality_telemetry,
        scheduled_keys=state.scheduled_keys,
        retry_counts=state.retry_counts,
        precheck_skip_count=int(state.precheck_skip_count),
        followup_recent=state.followup_recent,
        precheck_skip_examples=state.precheck_skip_examples,
        unresolved_hosts=state.unresolved_hosts,
        dns_skip_count=state.dns_skip_count,
        execution_gate_skip_count=state.execution_gate_skip_count,
        execution_gate_skip_examples=state.execution_gate_skip_examples,
        host_cooldown_until=state.host_cooldown_until,
        host_cooldown_skip_count=state.host_cooldown_skip_count,
        precision_queue=state.precision_queue,
        deep_budget=state.deep_budget,
        host_fail_streak=state.host_fail_streak,
        host_success_count=state.host_success_count,
        host_fail_count=state.host_fail_count,
        host_weak_count=state.host_weak_count,
        host_family_owner_gate=state.host_family_owner_gate,
        host_code000_streak=state.host_code000_streak,
        host_code000_total=state.host_code000_total,
        host_403_streak=state.host_403_streak,
        host_precheck_burst=state.host_precheck_burst,
        last_persist_ts=float(state.last_persist_ts),
    )


def make_skip_summary_flusher(*, flush_skip_summaries_fn: Callable[..., None], log_event_fn: Callable[..., None], precheck_skip_count_ref: list[int], precheck_skip_examples_ref: list[str], dns_skip_count_ref: dict[str, int], host_cooldown_skip_count_ref: dict[str, int], execution_gate_skip_count_ref: dict[str, int], execution_gate_skip_examples_ref: dict[str, list[str]]) -> Callable[[bool], None]:
    def flush(force: bool = False) -> None:
        flush_skip_summaries_fn(
            precheck_skip_count_ref=precheck_skip_count_ref,
            precheck_skip_examples_ref=precheck_skip_examples_ref,
            dns_skip_count_ref=dns_skip_count_ref,
            host_cooldown_skip_count_ref=host_cooldown_skip_count_ref,
            execution_gate_skip_count_ref=execution_gate_skip_count_ref,
            execution_gate_skip_examples_ref=execution_gate_skip_examples_ref,
            log_event_fn=log_event_fn,
            force=force,
        )

    return flush


def build_main_skip_summary_flushers(*, make_skip_summary_flusher_fn: Callable[..., Callable[[bool], None]], precheck_skip_count_ref: list[int], precheck_skip_examples: list[str], dns_skip_count: dict[str, int], host_cooldown_skip_count: dict[str, int], execution_gate_skip_count: dict[str, int], execution_gate_skip_examples: dict[str, list[str]]) -> dict:
    return {
        'flush_precheck_summary': make_skip_summary_flusher_fn(
            precheck_skip_count_ref=precheck_skip_count_ref,
            precheck_skip_examples_ref=precheck_skip_examples,
            dns_skip_count_ref={},
            host_cooldown_skip_count_ref={},
            execution_gate_skip_count_ref={},
            execution_gate_skip_examples_ref={},
        ),
        'flush_dns_skip_summary': make_skip_summary_flusher_fn(
            precheck_skip_count_ref=[0],
            precheck_skip_examples_ref=[],
            dns_skip_count_ref=dns_skip_count,
            host_cooldown_skip_count_ref={},
            execution_gate_skip_count_ref={},
            execution_gate_skip_examples_ref={},
        ),
        'flush_host_cooldown_summary': make_skip_summary_flusher_fn(
            precheck_skip_count_ref=[0],
            precheck_skip_examples_ref=[],
            dns_skip_count_ref={},
            host_cooldown_skip_count_ref=host_cooldown_skip_count,
            execution_gate_skip_count_ref={},
            execution_gate_skip_examples_ref={},
        ),
        'flush_execution_gate_summary': make_skip_summary_flusher_fn(
            precheck_skip_count_ref=[0],
            precheck_skip_examples_ref=[],
            dns_skip_count_ref={},
            host_cooldown_skip_count_ref={},
            execution_gate_skip_count_ref=execution_gate_skip_count,
            execution_gate_skip_examples_ref=execution_gate_skip_examples,
        ),
    }
