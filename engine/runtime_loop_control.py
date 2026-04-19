from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Callable


def _respect_runtime_control(*, read_runtime_control_state_fn: Callable[[], dict] | None, log_event_fn: Callable[..., None], sleep_fn: Callable[[float], None], poll_sec: float = 1.0) -> bool:
    if not callable(read_runtime_control_state_fn):
        return False
    logged_pause = False
    while True:
        try:
            control = read_runtime_control_state_fn() or {}
        except Exception:
            control = {}
        if bool(control.get('stopped', False)):
            log_event_fn('AUTO_CAMPAIGN', 'runtime_stop_requested', 'warning', 'stop_requested_via_logdash_control', actor='auto_campaign', row_type='service', highlight=True)
            return True
        if not bool(control.get('paused', False)):
            if logged_pause:
                log_event_fn('AUTO_CAMPAIGN', 'runtime_resumed', 'in_progress', 'resume_detected_via_logdash_control', actor='auto_campaign', row_type='service')
            return False
        if not logged_pause:
            log_event_fn('AUTO_CAMPAIGN', 'runtime_paused', 'warning', 'pause_requested_via_logdash_control', actor='auto_campaign', row_type='service', highlight=True)
            logged_pause = True
        sleep_fn(max(0.0, float(poll_sec)))


def time_budget_reached(*, run_started, time_budget_min: int) -> bool:
    return (datetime.now(timezone.utc) - run_started).total_seconds() >= time_budget_min * 60


def run_curated_loop(
    *,
    curated_plan: list[dict],
    max_runs: int,
    run_started,
    time_budget_min: int,
    target_load_limit: int,
    runs: list[dict],
    normalize_runtime_task_fn: Callable[[dict], dict],
    reconcile_active_plan_if_needed_fn: Callable[[str], None],
    log_event_fn: Callable[..., None],
    refresh_runtime_overrides_fn: Callable[[bool, bool, int | None, int | None], tuple[bool, bool, int | None, int | None]],
    owner_override_global: bool,
    last_override_state: bool,
    aggression_override_global: int | None,
    last_aggression_override: int | None,
    preempt_in_curated: bool,
    precision_queue: list[dict],
    followup_queue: list[dict],
    maybe_preempt_curated_entry_fn: Callable[..., tuple[dict, bool]],
    dequeue_next_task_fn: Callable[[], dict | None],
    requeue_task_fn: Callable[[dict], None],
    prepare_curated_task_fn: Callable[[dict, int | None], dict | None],
    build_execute_runtime_request_fn: Callable[..., dict],
    execute_runtime_task_fn: Callable[..., tuple[float, int]],
    last_heartbeat_ts: float,
    confirm_total: int,
    idx: int,
    build_deduped_target_plan_fn: Callable[[list[dict], Callable[..., tuple]], list[dict]],
    dedup_key_fn: Callable[..., tuple],
    read_runtime_control_state_fn: Callable[[], dict] | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> tuple[float, int, int, bool]:
    if not curated_plan:
        return last_heartbeat_ts, confirm_total, idx, False
    raw_plan = curated_plan[: max(1, target_load_limit)]
    target_plan = build_deduped_target_plan_fn(raw_plan, dedup_key_fn)
    budget_hit = False
    queue_preemptions = 0
    for entry in target_plan:
        entry = normalize_runtime_task_fn(entry)
        reconcile_active_plan_if_needed_fn('safe_boundary_curated_loop')
        if time_budget_reached(run_started=run_started, time_budget_min=time_budget_min):
            log_event_fn('AUTO_CAMPAIGN', 'time_budget_reached', 'warning', f'Reached time budget: {time_budget_min} min', actor='auto_campaign', row_type='service', highlight=True)
            budget_hit = True
            break
        if _respect_runtime_control(read_runtime_control_state_fn=read_runtime_control_state_fn, log_event_fn=log_event_fn, sleep_fn=sleep_fn):
            break
        owner_override_global, last_override_state, aggression_override_global, last_aggression_override = refresh_runtime_overrides_fn(
            owner_override_global,
            last_override_state,
            aggression_override_global,
            last_aggression_override,
        )
        if owner_override_global:
            entry['owner_override'] = True
        entry, was_preempted = maybe_preempt_curated_entry_fn(
            entry,
            preempt_in_curated=preempt_in_curated and queue_preemptions == 0,
            has_precision_queue=bool(precision_queue),
            has_followup_queue=bool(followup_queue),
            dequeue_task_fn=dequeue_next_task_fn,
        )
        if was_preempted:
            queue_preemptions += 1
            log_event_fn('AUTO_CAMPAIGN', 'curated_preempted_by_queue', 'in_progress', f"preempted_target={entry.get('target')};mode={entry.get('mode','followup')};count={queue_preemptions}", actor='auto_campaign', row_type='service')
        if len(runs) >= max_runs:
            if was_preempted:
                requeue_task_fn(entry)
            break
        prepared = prepare_curated_task_fn(entry, aggression_override_global)
        if prepared is None:
            if was_preempted:
                requeue_task_fn(entry)
            continue
        idx += 1
        request = build_execute_runtime_request_fn(
            prepared,
            run_index=idx,
            last_heartbeat_ts=last_heartbeat_ts,
            confirm_total=confirm_total,
        )
        last_heartbeat_ts, confirm_total = execute_runtime_task_fn(**request)
    return last_heartbeat_ts, confirm_total, idx, budget_hit


def run_main_loop(
    *,
    max_runs: int,
    runs: list[dict],
    run_started,
    time_budget_min: int,
    reconcile_active_plan_if_needed_fn: Callable[[str], None],
    log_event_fn: Callable[..., None],
    refresh_runtime_overrides_fn: Callable[[bool, bool, int | None, int | None], tuple[bool, bool, int | None, int | None]],
    owner_override_global: bool,
    last_override_state: bool,
    aggression_override_global: int | None,
    last_aggression_override: int | None,
    dequeue_next_task_fn: Callable[[], dict | None],
    requeue_task_fn: Callable[[dict], None],
    history: list[dict],
    scope_targets: list[str],
    normalize_runtime_task_fn: Callable[[dict], dict],
    unpack_queued_task_fn: Callable[..., dict],
    clamp_aggression_fn: Callable[[int], int],
    capped_aggression_fn: Callable[[str, str, int], int],
    propose_next_vector_fn: Callable[[list[dict]], tuple[str, str]],
    prepare_runtime_task_fn: Callable[..., dict | None],
    build_execute_runtime_request_fn: Callable[..., dict],
    execute_runtime_task_fn: Callable[..., tuple[float, int]],
    last_heartbeat_ts: float,
    confirm_total: int,
    selected_error_record_fn: Callable[[str], None],
    read_runtime_control_state_fn: Callable[[], dict] | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> tuple[float, int, bool]:
    budget_hit = False
    while len(runs) < max_runs:
        reconcile_active_plan_if_needed_fn('safe_boundary_main_loop')
        if time_budget_reached(run_started=run_started, time_budget_min=time_budget_min):
            log_event_fn('AUTO_CAMPAIGN', 'time_budget_reached', 'warning', f'Reached time budget: {time_budget_min} min', actor='auto_campaign', row_type='service', highlight=True)
            budget_hit = True
            break
        if _respect_runtime_control(read_runtime_control_state_fn=read_runtime_control_state_fn, log_event_fn=log_event_fn, sleep_fn=sleep_fn):
            break
        owner_override_global, last_override_state, aggression_override_global, last_aggression_override = refresh_runtime_overrides_fn(
            owner_override_global,
            last_override_state,
            aggression_override_global,
            last_aggression_override,
        )
        selected = selected_error_record_fn(
            owner_override_global,
            aggression_override_global,
            dequeue_next_task_fn,
            history,
            scope_targets,
            normalize_runtime_task_fn,
            unpack_queued_task_fn,
            clamp_aggression_fn,
            capped_aggression_fn,
            propose_next_vector_fn,
        )
        if isinstance(selected, dict) and str(selected.get('status') or '') == 'fatal':
            break
        if not isinstance(selected, dict):
            continue
        task = selected.get('task') if isinstance(selected.get('task'), dict) else None
        selected_from_queue = str(selected.get('source') or '') == 'queue' and isinstance(task, dict)
        objective = selected.get('objective')
        target = selected.get('target')
        aggression = int(selected.get('aggression', clamp_aggression_fn(6)))
        mode = str(selected.get('mode') or 'fast')
        owner_auth = bool(selected.get('owner_auth', False))
        owner_override = bool(selected.get('owner_override', owner_override_global))
        plan_name = selected.get('plan_name')
        if not objective or not target:
            if selected_from_queue:
                requeue_task_fn(task)
            continue
        prepared = prepare_runtime_task_fn(task, objective, target, mode, aggression, owner_auth, owner_override, plan_name)
        if prepared is None:
            if selected_from_queue:
                requeue_task_fn(task)
            continue
        current_index = len(runs) + 1
        request = build_execute_runtime_request_fn(
            prepared,
            run_index=current_index,
            last_heartbeat_ts=last_heartbeat_ts,
            confirm_total=confirm_total,
        )
        last_heartbeat_ts, confirm_total = execute_runtime_task_fn(**request)
    return last_heartbeat_ts, confirm_total, budget_hit
