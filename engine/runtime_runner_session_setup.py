from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from runtime_runner_controls import MainRuntimeControls, build_main_runtime_controls  # type: ignore
from runtime_session_state import RuntimeSessionState  # type: ignore


@dataclass
class MainSessionBaseFields:
    runs: list[dict]
    host_state: dict
    executed_keys: set
    curated_plan_ref: list[list[dict]]
    active_plan_revision_ref: list[int]
    active_plan_hash_ref: list[str]
    host_dns_cache: dict
    toggles: dict
    planner_hints_cache_ref: list[dict]
    last_regen_run_index_ref: list[int]


@dataclass
class MainSessionAliasFields:
    followup_queue: list[dict]
    followup_counts: dict
    confirm_counts: dict
    confirm_recent: dict
    confirm_class_counts: dict
    confirm_total: int
    quality_telemetry: dict
    scheduled_keys: set
    retry_counts: dict
    precheck_skip_count_ref: list[int]
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
    queue_coordinator: object
    host_weak_count: dict[str, int]
    host_family_owner_gate: dict
    host_code000_streak: dict[str, int]
    host_code000_total: dict[str, int]
    host_403_streak: dict[str, int]
    host_precheck_burst: dict[str, int]
    last_persist_ts_ref: list[float]


@dataclass
class MainSessionSetup:
    runs: list[dict]
    host_state: dict
    executed_keys: set
    curated_plan_ref: list[list[dict]]
    active_plan_revision_ref: list[int]
    active_plan_hash_ref: list[str]
    host_dns_cache: dict
    toggles: dict
    planner_hints_cache_ref: list[dict]
    last_regen_run_index_ref: list[int]
    code000_streak_threshold: int
    code000_session_cap: int
    code000_cooldown_sec: int
    autodiscover_deep_skip: bool
    max_followups_per_target: int
    qualification_mode: str
    qualification_promising_threshold: str
    max_confirm_jobs_per_target: int
    confirm_job_cooldown_sec: int
    max_confirm_jobs_total: int
    max_confirm_jobs_per_class: int
    followup_queue: list[dict]
    followup_counts: dict
    confirm_counts: dict
    confirm_recent: dict
    confirm_class_counts: dict
    confirm_total: int
    quality_telemetry: dict
    scheduled_keys: set
    retry_counts: dict
    precheck_skip_count_ref: list[int]
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
    queue_coordinator: object
    host_weak_count: dict[str, int]
    host_family_owner_gate: dict
    host_code000_streak: dict[str, int]
    host_code000_total: dict[str, int]
    host_403_streak: dict[str, int]
    host_precheck_burst: dict[str, int]
    last_persist_ts_ref: list[float]


def build_main_session_base_fields(state: RuntimeSessionState) -> MainSessionBaseFields:
    return MainSessionBaseFields(
        runs=state.runs,
        host_state=state.host_state,
        executed_keys=state.executed_keys,
        curated_plan_ref=[state.curated_plan],
        active_plan_revision_ref=[state.active_plan_revision],
        active_plan_hash_ref=[state.active_plan_hash],
        host_dns_cache=state.host_dns_cache,
        toggles=state.toggles,
        planner_hints_cache_ref=[state.planner_hints_cache],
        last_regen_run_index_ref=[state.last_regen_run_index],
    )


def build_main_session_alias_fields(*, state_aliases, queue_coordinator: object) -> MainSessionAliasFields:
    return MainSessionAliasFields(
        followup_queue=state_aliases.followup_queue,
        followup_counts=state_aliases.followup_counts,
        confirm_counts=state_aliases.confirm_counts,
        confirm_recent=state_aliases.confirm_recent,
        confirm_class_counts=state_aliases.confirm_class_counts,
        confirm_total=state_aliases.confirm_total,
        quality_telemetry=state_aliases.quality_telemetry,
        scheduled_keys=state_aliases.scheduled_keys,
        retry_counts=state_aliases.retry_counts,
        precheck_skip_count_ref=[state_aliases.precheck_skip_count],
        followup_recent=state_aliases.followup_recent,
        precheck_skip_examples=state_aliases.precheck_skip_examples,
        unresolved_hosts=state_aliases.unresolved_hosts,
        dns_skip_count=state_aliases.dns_skip_count,
        execution_gate_skip_count=state_aliases.execution_gate_skip_count,
        execution_gate_skip_examples=state_aliases.execution_gate_skip_examples,
        host_cooldown_until=state_aliases.host_cooldown_until,
        host_cooldown_skip_count=state_aliases.host_cooldown_skip_count,
        precision_queue=state_aliases.precision_queue,
        deep_budget=state_aliases.deep_budget,
        host_fail_streak=state_aliases.host_fail_streak,
        host_success_count=state_aliases.host_success_count,
        host_fail_count=state_aliases.host_fail_count,
        queue_coordinator=queue_coordinator,
        host_weak_count=state_aliases.host_weak_count,
        host_family_owner_gate=state_aliases.host_family_owner_gate,
        host_code000_streak=state_aliases.host_code000_streak,
        host_code000_total=state_aliases.host_code000_total,
        host_403_streak=state_aliases.host_403_streak,
        host_precheck_burst=state_aliases.host_precheck_burst,
        last_persist_ts_ref=[state_aliases.last_persist_ts],
    )


def build_main_session_setup(*, state: RuntimeSessionState, build_main_runtime_controls_fn: Callable[[dict], MainRuntimeControls] = build_main_runtime_controls, build_main_state_aliases_fn: Callable[..., object], build_queue_coordinator_fn: Callable[..., object], build_main_session_alias_fields_fn: Callable[..., MainSessionAliasFields] = build_main_session_alias_fields) -> MainSessionSetup:
    base_fields = build_main_session_base_fields(state)
    runtime_controls = build_main_runtime_controls_fn(base_fields.toggles)
    state_aliases = build_main_state_aliases_fn(state)
    queue_coordinator = build_queue_coordinator_fn(
        followup_queue=state_aliases.followup_queue,
        precision_queue=state_aliases.precision_queue,
        host_rr=state_aliases.host_rr,
        host_success_count=state_aliases.host_success_count,
        host_fail_count=state_aliases.host_fail_count,
    )
    alias_fields = build_main_session_alias_fields_fn(state_aliases=state_aliases, queue_coordinator=queue_coordinator)
    return MainSessionSetup(
        **vars(base_fields),
        code000_streak_threshold=runtime_controls.code000_streak_threshold,
        code000_session_cap=runtime_controls.code000_session_cap,
        code000_cooldown_sec=runtime_controls.code000_cooldown_sec,
        autodiscover_deep_skip=runtime_controls.autodiscover_deep_skip,
        max_followups_per_target=runtime_controls.max_followups_per_target,
        qualification_mode=runtime_controls.qualification_mode,
        qualification_promising_threshold=runtime_controls.qualification_promising_threshold,
        max_confirm_jobs_per_target=runtime_controls.max_confirm_jobs_per_target,
        confirm_job_cooldown_sec=runtime_controls.confirm_job_cooldown_sec,
        max_confirm_jobs_total=runtime_controls.max_confirm_jobs_total,
        max_confirm_jobs_per_class=runtime_controls.max_confirm_jobs_per_class,
        **vars(alias_fields),
    )
