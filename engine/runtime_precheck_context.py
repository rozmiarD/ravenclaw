from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class RuntimePrecheckContext:
    unresolved_hosts: set
    dns_skip_count: dict
    host_dns_cache: dict
    host_cooldown_until: dict
    host_cooldown_skip_count: dict
    autodiscover_deep_skip: bool
    executed_keys: set
    precheck_skip_examples: list
    host_precheck_burst: dict
    host_state: dict
    deep_budget: dict
    host_fail_streak: dict
    host_success_count: dict
    host_fail_count: dict
    dedup_key_fn: Callable[..., tuple]
    family_allowed_for_host_stage_fn: Callable[..., bool]
    log_skip_fn: Callable[..., None]
    increment_precheck_skip_fn: Callable[[], None]
    on_executed_key_fn: Callable[[], None]
    gate_skip_count: dict
    gate_skip_examples: dict
    host_health_cooldown_sec: int = 900
    deep_budget_cap_per_host_family: int = 2
    precheck_burst_cooldown_threshold: int = 10
    precheck_burst_cooldown_sec: int = 300
    host_fail_streak_backoff_step_sec: float = 0.4
    host_fail_streak_backoff_cap_sec: float = 2.0

    def prepare_task_precheck(self, *, objective: str, target: str, mode: str, task_family: str, dedup_mode_suffix: bool, runtime_task: dict[str, Any] | None = None):
        from auto_campaign_precheck import precheck_and_prepare_task  # type: ignore

        return precheck_and_prepare_task(
            objective=str(objective),
            target=str(target),
            mode=str(mode),
            task_family=str(task_family or ''),
            dedup_mode_suffix=dedup_mode_suffix,
            runtime_task=(runtime_task if isinstance(runtime_task, dict) else {}),
            unresolved_hosts=self.unresolved_hosts,
            dns_skip_count=self.dns_skip_count,
            host_dns_cache=self.host_dns_cache,
            host_cooldown_until=self.host_cooldown_until,
            host_cooldown_skip_count=self.host_cooldown_skip_count,
            autodiscover_deep_skip=self.autodiscover_deep_skip,
            executed_keys=self.executed_keys,
            precheck_skip_examples=self.precheck_skip_examples,
            host_precheck_burst=self.host_precheck_burst,
            host_state=self.host_state,
            deep_budget=self.deep_budget,
            host_fail_streak=self.host_fail_streak,
            host_success_count=self.host_success_count,
            host_fail_count=self.host_fail_count,
            dedup_key_fn=self.dedup_key_fn,
            family_allowed_fn=self.family_allowed_for_host_stage_fn,
            log_skip=self.log_skip_fn,
            increment_precheck_skip=self.increment_precheck_skip_fn,
            on_executed_key=self.on_executed_key_fn,
            gate_skip_count=self.gate_skip_count,
            gate_skip_examples=self.gate_skip_examples,
            host_health_cooldown_sec=self.host_health_cooldown_sec,
            deep_budget_cap_per_host_family=self.deep_budget_cap_per_host_family,
            precheck_burst_cooldown_threshold=self.precheck_burst_cooldown_threshold,
            precheck_burst_cooldown_sec=self.precheck_burst_cooldown_sec,
            host_fail_streak_backoff_step_sec=self.host_fail_streak_backoff_step_sec,
            host_fail_streak_backoff_cap_sec=self.host_fail_streak_backoff_cap_sec,
        )
