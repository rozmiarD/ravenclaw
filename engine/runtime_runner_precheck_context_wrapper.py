from __future__ import annotations

from typing import Callable


def build_runtime_precheck_context_inputs(*, build_runtime_precheck_context_inputs_fn: Callable[..., object], runtime_precheck_context_cls: Callable[..., object], unresolved_hosts: set, dns_skip_count: dict, host_dns_cache: dict, host_cooldown_until: dict, host_cooldown_skip_count: dict, autodiscover_deep_skip: bool, executed_keys: set, precheck_skip_examples: list, host_precheck_burst: dict, host_state: dict, deep_budget: dict, host_fail_streak: dict, host_success_count: dict, host_fail_count: dict, gate_skip_count: dict, gate_skip_examples: dict, increment_precheck_skip_fn: Callable[[], None], on_executed_key_fn: Callable[[], None], dedup_key_fn: Callable[..., str], family_allowed_for_host_stage_fn: Callable[..., bool], log_skip_fn: Callable[..., None], host_health_cooldown_sec: int, deep_budget_cap_per_host_family: int, precheck_burst_cooldown_threshold: int, precheck_burst_cooldown_sec: int, host_fail_streak_backoff_step_sec: float, host_fail_streak_backoff_cap_sec: float) -> object:
    return build_runtime_precheck_context_inputs_fn(
        runtime_precheck_context_cls=runtime_precheck_context_cls,
        unresolved_hosts=unresolved_hosts,
        dns_skip_count=dns_skip_count,
        host_dns_cache=host_dns_cache,
        host_cooldown_until=host_cooldown_until,
        host_cooldown_skip_count=host_cooldown_skip_count,
        autodiscover_deep_skip=autodiscover_deep_skip,
        executed_keys=executed_keys,
        precheck_skip_examples=precheck_skip_examples,
        host_precheck_burst=host_precheck_burst,
        host_state=host_state,
        deep_budget=deep_budget,
        host_fail_streak=host_fail_streak,
        host_success_count=host_success_count,
        host_fail_count=host_fail_count,
        gate_skip_count=gate_skip_count,
        gate_skip_examples=gate_skip_examples,
        increment_precheck_skip_fn=increment_precheck_skip_fn,
        on_executed_key_fn=on_executed_key_fn,
        dedup_key_fn=dedup_key_fn,
        family_allowed_for_host_stage_fn=family_allowed_for_host_stage_fn,
        log_skip_fn=log_skip_fn,
        host_health_cooldown_sec=host_health_cooldown_sec,
        deep_budget_cap_per_host_family=deep_budget_cap_per_host_family,
        precheck_burst_cooldown_threshold=precheck_burst_cooldown_threshold,
        precheck_burst_cooldown_sec=precheck_burst_cooldown_sec,
        host_fail_streak_backoff_step_sec=host_fail_streak_backoff_step_sec,
        host_fail_streak_backoff_cap_sec=host_fail_streak_backoff_cap_sec,
    )
