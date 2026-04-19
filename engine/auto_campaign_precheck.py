from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Callable

from auto_campaign_targets import host_from_target  # type: ignore
from runtime_admission_policy import planner_runtime_admission_decision  # type: ignore
from runtime_admission_reporting import admission_skip_bucket, execution_gate_log_parts, record_execution_gate_skip  # type: ignore
from runtime_execution_gate import evaluate_host_execution_gate, family_allowed_for_host_stage, host_health_blocked  # type: ignore


PrecheckLogger = Callable[[str, str, str], None]


def evaluate_runtime_task_admission(*, runtime_task: dict[str, Any] | None, host_state: dict, host: str, mode: str, planner_feedback: dict[str, Any] | None = None) -> tuple[bool, str]:
    decision = planner_runtime_admission_decision(
        runtime_task=runtime_task,
        host_state=host_state,
        host=host,
        mode=mode,
        host_success_count=None,
        planner_feedback=planner_feedback,
    )
    return decision.allowed, decision.reason_code


def _planner_synthesis_explainability(*, runtime_task: dict[str, Any] | None, host_state: dict, host: str, mode: str, host_success_count: dict[str, int], planner_feedback: dict[str, Any] | None = None) -> dict[str, Any]:
    decision = planner_runtime_admission_decision(
        runtime_task=runtime_task,
        host_state=host_state,
        host=host,
        mode=mode,
        host_success_count=host_success_count,
        planner_feedback=planner_feedback,
    )
    explainability = getattr(decision, 'explainability', None)
    return explainability if isinstance(explainability, dict) else {}


def _gate_payload(gate) -> dict[str, Any]:
    try:
        payload = gate.as_dict()
        if isinstance(payload, dict):
            return payload
    except Exception:
        pass
    return {
        'allowed': bool(getattr(gate, 'allowed', False)),
        'host': str(getattr(gate, 'host', '') or ''),
        'family': str(getattr(gate, 'family', '') or ''),
        'reason_code': str(getattr(gate, 'reason_code', '') or ''),
        'detail': str(getattr(gate, 'detail', '') or ''),
        'cooldown_until': getattr(gate, 'cooldown_until', None),
        'state_band': str(getattr(gate, 'state_band', '') or ''),
        'blockers': list(getattr(gate, 'blockers', []) or []),
    }


def _log_gate_skip(log_skip: PrecheckLogger, gate, mode: str) -> None:
    payload = _gate_payload(gate)
    reason_code, host, detail = execution_gate_log_parts(payload, mode)
    log_skip(reason_code, host, detail)


def precheck_and_prepare_task(
    *,
    objective: str,
    target: str,
    mode: str,
    task_family: str,
    dedup_mode_suffix: bool,
    unresolved_hosts: set[str],
    dns_skip_count: dict[str, int],
    host_dns_cache: dict[str, bool],
    host_cooldown_until: dict[str, float],
    host_cooldown_skip_count: dict[str, int],
    autodiscover_deep_skip: bool,
    executed_keys: set,
    precheck_skip_examples: list[str],
    host_precheck_burst: dict[str, int],
    host_state: dict,
    deep_budget: dict[tuple[str, str], int],
    host_fail_streak: dict[str, int],
    host_success_count: dict[str, int],
    host_fail_count: dict[str, int],
    dedup_key_fn: Callable[[str, str], tuple],
    family_allowed_fn: Callable[[dict, str, str], bool],
    log_skip: PrecheckLogger,
    increment_precheck_skip: Callable[[], None],
    on_executed_key: Callable[[], None],
    runtime_task: dict[str, Any] | None = None,
    planner_feedback: dict[str, Any] | None = None,
    gate_skip_count: dict[str, int] | None = None,
    gate_skip_examples: dict[str, list[str]] | None = None,
    host_health_cooldown_sec: int = 900,
    deep_budget_cap_per_host_family: int = 2,
    precheck_burst_cooldown_threshold: int = 10,
    precheck_burst_cooldown_sec: int = 300,
    host_fail_streak_backoff_step_sec: float = 0.4,
    host_fail_streak_backoff_cap_sec: float = 2.0,
) -> dict[str, Any]:
    h = host_from_target(target)
    gate_skip_count = gate_skip_count if isinstance(gate_skip_count, dict) else {}
    gate_skip_examples = gate_skip_examples if isinstance(gate_skip_examples, dict) else {}
    gate = evaluate_host_execution_gate(
        objective=objective,
        target=target,
        mode=mode,
        task_family=task_family,
        unresolved_hosts=unresolved_hosts,
        host_dns_cache=host_dns_cache,
        host_cooldown_until=host_cooldown_until,
        autodiscover_deep_skip=autodiscover_deep_skip,
        host_state=host_state,
        deep_budget=deep_budget,
        host_success_count=host_success_count,
        host_fail_count=host_fail_count,
        family_allowed_fn=family_allowed_fn,
        runtime_task=runtime_task,
        planner_feedback=planner_feedback,
        host_health_cooldown_sec=host_health_cooldown_sec,
        deep_budget_cap_per_host_family=deep_budget_cap_per_host_family,
    )
    gate_payload = _gate_payload(gate)
    if gate_payload.get('reason_code') == 'planner_synthesis_skip':
        gate_payload.update(
            _planner_synthesis_explainability(
                runtime_task=runtime_task,
                host_state=host_state,
                host=h,
                mode=mode,
                host_success_count=host_success_count,
                planner_feedback=planner_feedback,
            )
        )
    if not gate.allowed:
        reason_code = str(gate_payload.get('reason_code') or gate.reason_code or '').strip()
        bucket = admission_skip_bucket(reason_code)
        if bucket == 'dns':
            dns_skip_count[h] = dns_skip_count.get(h, 0) + 1
        elif bucket == 'cooldown':
            host_cooldown_skip_count[h] = host_cooldown_skip_count.get(h, 0) + 1
        elif bucket == 'execution_gate':
            record_execution_gate_skip(reason_code, target, gate_payload, gate_skip_count, gate_skip_examples)
            _log_gate_skip(log_skip, gate, mode)
        return {
            'allowed': False,
            'host': h,
            'fam': gate.family,
            'key': None,
            'reason_code': reason_code,
            'gate': gate_payload,
        }
    key = dedup_key_fn(objective, target)
    if dedup_mode_suffix and str(mode).startswith('retry_'):
        key = (key[0], key[1], f"{key[2]}:{mode}")
    precheck_burst_cooldown_threshold = max(2, int(precheck_burst_cooldown_threshold or 10))
    precheck_burst_cooldown_sec = max(60, int(precheck_burst_cooldown_sec or 300))
    host_fail_streak_backoff_step_sec = max(0.0, float(host_fail_streak_backoff_step_sec if host_fail_streak_backoff_step_sec is not None else 0.4))
    host_fail_streak_backoff_cap_sec = max(host_fail_streak_backoff_step_sec, float(host_fail_streak_backoff_cap_sec if host_fail_streak_backoff_cap_sec is not None else 2.0))
    if key in executed_keys:
        increment_precheck_skip()
        if len(precheck_skip_examples) < 3:
            precheck_skip_examples.append(f'{mode}:{target}')
        if h:
            host_precheck_burst[h] = host_precheck_burst.get(h, 0) + 1
            if host_precheck_burst[h] >= precheck_burst_cooldown_threshold:
                host_cooldown_until[h] = datetime.now(timezone.utc).timestamp() + precheck_burst_cooldown_sec
        return {
            'allowed': False,
            'host': h,
            'fam': gate.family,
            'key': key,
            'reason_code': 'dedup_skip',
            'gate': gate_payload,
        }
    executed_keys.add(key)
    on_executed_key()
    fam = gate.family
    if str(mode).lower() in {'deep', 'followup'}:
        kfb = (h, fam)
        deep_budget[kfb] = deep_budget.get(kfb, 0) + 1
    if host_fail_streak.get(h, 0) > 1 and host_fail_streak_backoff_cap_sec > 0:
        time.sleep(min(host_fail_streak_backoff_cap_sec, host_fail_streak_backoff_step_sec * host_fail_streak.get(h, 0)))
    if h in host_precheck_burst and host_precheck_burst.get(h, 0) > 0:
        host_precheck_burst[h] = max(0, host_precheck_burst.get(h, 0) - 1)
    return {
        'allowed': True,
        'host': h,
        'fam': fam,
        'key': key,
        'reason_code': 'allowed',
        'gate': gate_payload,
    }
