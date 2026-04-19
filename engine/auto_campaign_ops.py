from __future__ import annotations

from datetime import datetime, timezone

from aggression_policy import clamp_aggression  # type: ignore


def curated_should_stop(runs: list[dict], max_runs: int, run_started, time_budget_min: int, log_event) -> bool:
    if (datetime.now(timezone.utc) - run_started).total_seconds() >= time_budget_min * 60:
        log_event("AUTO_CAMPAIGN", "time_budget_reached", "warning", f"Reached time budget: {time_budget_min} min", actor="auto_campaign", row_type="service", highlight=True)
        return True
    return len(runs) >= max_runs


def curated_before_entry(entry: dict, *, read_runtime_owner_override, owner_override_global: bool, last_override_state: bool, log_event):
    owner_override_global = read_runtime_owner_override(default=owner_override_global)
    if owner_override_global != last_override_state:
        log_event("AUTO_CAMPAIGN", "owner_override_runtime", "warning", f"owner_override_changed:{owner_override_global}", actor="auto_campaign", row_type="service")
        last_override_state = owner_override_global
    if owner_override_global:
        entry['owner_override'] = True
    return owner_override_global, last_override_state


def dynamic_should_continue(runs: list[dict], max_runs: int, run_started, time_budget_min: int, log_event) -> bool:
    if len(runs) >= max_runs:
        return False
    if (datetime.now(timezone.utc) - run_started).total_seconds() >= time_budget_min * 60:
        log_event("AUTO_CAMPAIGN", "time_budget_reached", "warning", f"Reached time budget: {time_budget_min} min", actor="auto_campaign", row_type="service", highlight=True)
        return False
    return True


def dynamic_before_iteration(*, read_runtime_owner_override, owner_override_global: bool, last_override_state: bool, log_event):
    owner_override_global = read_runtime_owner_override(default=owner_override_global)
    if owner_override_global != last_override_state:
        log_event("AUTO_CAMPAIGN", "owner_override_runtime", "warning", f"owner_override_changed:{owner_override_global}", actor="auto_campaign", row_type="service")
        last_override_state = owner_override_global
    return owner_override_global, last_override_state


def dynamic_select_task(queue_coordinator, owner_override_global: bool):
    owner_auth = False
    owner_override = owner_override_global
    aggression = clamp_aggression(6)
    mode = "fast"
    plan_name = None
    next_task = queue_coordinator.dequeue()
    if next_task is not None:
        objective = next_task.get("objective")
        target = next_task.get("target")
        aggression = clamp_aggression(int(next_task.get("aggression", 6)))
        mode = next_task.get("mode", "followup")
        owner_auth = bool(next_task.get("owner_approved_auth", False))
        owner_override = bool(next_task.get("owner_override", owner_override_global))
        plan_name = next_task.get("name")
        return {"objective": objective, "target": target, "aggression": aggression, "mode": mode, "owner_auth": owner_auth, "owner_override": owner_override, "plan_name": plan_name, "from_queue": True}
    return {"from_queue": False}
