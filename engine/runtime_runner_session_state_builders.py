from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable, Any


def build_runtime_session_state_from_bootstrap(*, runtime_session_state_cls, bootstrap: Any):
    runs = list(bootstrap.runs or [])
    executed_keys = set(bootstrap.executed_keys or set())
    runtime_plan_meta = bootstrap.runtime_plan_meta if isinstance(bootstrap.runtime_plan_meta, dict) else {}
    return runtime_session_state_cls(
        runs=runs,
        history=list(bootstrap.history or []),
        host_state=dict(bootstrap.host_state or {}),
        curated_plan=list(bootstrap.curated_plan or []),
        runtime_plan_meta=runtime_plan_meta,
        host_dns_cache=dict(bootstrap.host_dns_cache or {}),
        toggles=dict(bootstrap.toggles or {}),
        planner_hints_cache=dict(bootstrap.planner_hints_cache or {}),
        followup_queue=list(bootstrap.followup_queue or []),
        precision_queue=list(bootstrap.precision_queue or []),
        executed_keys=executed_keys,
        scheduled_keys=set(executed_keys),
        active_plan_revision=int(runtime_plan_meta.get('plan_revision', 0) or 0),
        active_plan_hash=str(runtime_plan_meta.get('plan_hash') or ''),
        last_regen_run_index=len(runs),
        idx=len(runs),
        promising_hits_ref=[sum(1 for r in runs if bool(r.get('promising', False)))],
    )


def build_runtime_session_state(*, reports_dir, validate_campaign_fn: Callable[[str], dict], selected_scope_path_fn: Callable[[], Any], runtime_session_state_cls, load_runtime_session_bootstrap_fn: Callable[[], Any], build_runtime_session_state_from_bootstrap_fn: Callable[..., Any]) -> tuple[dict, Any, datetime, int, int, int, str, int]:
    reports_dir.mkdir(parents=True, exist_ok=True)
    campaign_validation = validate_campaign_fn(str(selected_scope_path_fn()))
    if not campaign_validation.get('ok'):
        return campaign_validation, runtime_session_state_cls(runs=[], history=[], host_state={}, curated_plan=[], runtime_plan_meta={}, host_dns_cache={}, toggles={}, planner_hints_cache={}), datetime.now(timezone.utc), 0, 0, 0, 'balanced', 0

    bootstrap = load_runtime_session_bootstrap_fn()
    state = build_runtime_session_state_from_bootstrap_fn(bootstrap=bootstrap)
    return campaign_validation, state, bootstrap.run_started, int(bootstrap.max_runs), int(bootstrap.target_load_limit), int(bootstrap.time_budget_min), str(bootstrap.retry_policy), int(bootstrap.retry_limit)
