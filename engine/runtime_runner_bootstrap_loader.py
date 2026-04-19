from __future__ import annotations

from datetime import datetime, timezone
import os
from typing import Callable, Any


def load_runtime_session_bootstrap(*, runtime_session_bootstrap_cls, load_existing_runs_fn: Callable[[], list[dict]], load_host_state_fn: Callable[[], dict], dedup_key_fn: Callable[..., Any], current_campaign_key_fn: Callable[[], str], campaign_settings_for_key_fn: Callable[[str], dict], load_curated_plan_fn: Callable[[], list[dict]], load_runtime_plan_meta_fn: Callable[[], dict], host_from_target_fn: Callable[[str], str], is_resolvable_host_fn: Callable[[str], bool], load_runtime_toggles_fn: Callable[..., dict], pipeline_config_path, normalize_pipeline_flags_fn: Callable[..., dict], warn_fn: Callable[[str], None], load_planner_hints_fn: Callable[[], dict], load_queue_state_fn: Callable[[], dict]):
    runs = load_existing_runs_fn()
    history = list(runs)
    host_state = load_host_state_fn()
    executed_keys = {
        dedup_key_fn(str(run.get('objective')), str(run.get('target')))
        for run in history
        if run.get('objective') and run.get('target')
    }
    run_started = datetime.now(timezone.utc)
    selected_key = current_campaign_key_fn()
    cfg = campaign_settings_for_key_fn(selected_key)
    max_runs = int(os.getenv('AUTO_MAX_RUNS', str(cfg.get('max_runs', 300))))
    target_load_limit = int(os.getenv('AUTO_TARGET_LOAD_LIMIT', str(cfg.get('target_load_limit', max_runs * 2))))
    time_budget_min = max(5, int(os.getenv('AUTO_TIME_BUDGET_MIN', str(cfg.get('time_budget_min', 60)))))
    retry_policy = str(os.getenv('AUTO_RETRY_POLICY', str(cfg.get('retry_policy', 'balanced')))).strip().lower()
    retry_policy = retry_policy if retry_policy in {'strict', 'balanced', 'aggressive'} else 'balanced'
    retry_limit = {'strict': 0, 'balanced': 1, 'aggressive': 2}[retry_policy]
    curated_plan = load_curated_plan_fn()
    runtime_plan_meta = load_runtime_plan_meta_fn()
    host_dns_cache: dict[str, bool] = {}
    for entry in curated_plan:
        if isinstance(entry, dict):
            host = host_from_target_fn(str(entry.get('target') or ''))
            if host and host not in host_dns_cache:
                host_dns_cache[host] = is_resolvable_host_fn(host)
    try:
        toggles = load_runtime_toggles_fn(
            pipeline_config_path=pipeline_config_path,
            normalize_pipeline_flags_fn=normalize_pipeline_flags_fn,
            warn_fn=warn_fn,
        )
    except TypeError:
        toggles = load_runtime_toggles_fn()
    planner_hints_cache: dict = load_planner_hints_fn()
    qstate = load_queue_state_fn()
    followup_queue = [x for x in qstate.get('followup_queue', []) if isinstance(x, dict)] if isinstance(qstate.get('followup_queue'), list) else []
    precision_queue = [x for x in qstate.get('precision_queue', []) if isinstance(x, dict)] if isinstance(qstate.get('precision_queue'), list) else []
    return runtime_session_bootstrap_cls(
        runs=runs,
        history=history,
        host_state=host_state,
        executed_keys=executed_keys,
        run_started=run_started,
        max_runs=max_runs,
        target_load_limit=target_load_limit,
        time_budget_min=time_budget_min,
        retry_policy=retry_policy,
        retry_limit=retry_limit,
        curated_plan=curated_plan,
        runtime_plan_meta=runtime_plan_meta,
        host_dns_cache=host_dns_cache,
        toggles=toggles,
        planner_hints_cache=planner_hints_cache,
        followup_queue=followup_queue,
        precision_queue=precision_queue,
    )
