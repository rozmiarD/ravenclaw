from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from collections import defaultdict, deque


@dataclass
class RuntimeSessionState:
    runs: list[dict]
    history: list[dict]
    host_state: dict
    curated_plan: list[dict]
    runtime_plan_meta: dict
    host_dns_cache: dict[str, bool]
    toggles: dict
    planner_hints_cache: dict
    followup_queue: list[dict] = field(default_factory=list)
    precision_queue: list[dict] = field(default_factory=list)
    executed_keys: set = field(default_factory=set)
    scheduled_keys: set = field(default_factory=set)
    host_rr: dict[str, deque] = field(default_factory=lambda: defaultdict(deque))
    followup_counts: dict[str, int] = field(default_factory=dict)
    confirm_counts: dict[str, int] = field(default_factory=dict)
    confirm_recent: dict[str, float] = field(default_factory=dict)
    confirm_class_counts: dict[str, int] = field(default_factory=dict)
    confirm_total: int = 0
    quality_telemetry: dict = field(default_factory=lambda: {'probable': 0, 'confirmed': 0, 'downgraded_confirm': 0, 'confirm_queued': 0})
    retry_counts: dict = field(default_factory=dict)
    precheck_skip_count: int = 0
    followup_recent: dict[str, float] = field(default_factory=dict)
    precheck_skip_examples: list[str] = field(default_factory=list)
    unresolved_hosts: set[str] = field(default_factory=set)
    dns_skip_count: dict[str, int] = field(default_factory=dict)
    execution_gate_skip_count: dict[str, int] = field(default_factory=dict)
    execution_gate_skip_examples: dict[str, list[str]] = field(default_factory=dict)
    host_cooldown_until: dict[str, float] = field(default_factory=dict)
    host_cooldown_skip_count: dict[str, int] = field(default_factory=dict)
    deep_budget: dict = field(default_factory=dict)
    host_fail_streak: dict[str, int] = field(default_factory=dict)
    host_success_count: dict[str, int] = field(default_factory=dict)
    host_fail_count: dict[str, int] = field(default_factory=dict)
    host_weak_count: dict[str, int] = field(default_factory=dict)
    host_family_owner_gate: dict = field(default_factory=dict)
    host_code000_streak: dict[str, int] = field(default_factory=dict)
    host_code000_total: dict[str, int] = field(default_factory=dict)
    host_403_streak: dict[str, int] = field(default_factory=dict)
    host_precheck_burst: dict[str, int] = field(default_factory=dict)
    last_persist_ts: float = 0.0
    active_plan_revision: int = 0
    active_plan_hash: str = ''
    last_regen_run_index: int = 0
    last_heartbeat_ts: float = 0.0
    idx: int = 0
    promising_hits_ref: list[int] = field(default_factory=lambda: [0])
