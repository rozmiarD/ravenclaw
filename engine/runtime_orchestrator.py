from __future__ import annotations

from typing import Any, Callable


PreparedTask = dict[str, Any]


def build_execute_runtime_request(
    prepared: PreparedTask,
    *,
    run_index: int,
    last_heartbeat_ts: float,
    confirm_total: int,
) -> dict[str, Any]:
    task_ctx = prepared.get('task_ctx') if isinstance(prepared.get('task_ctx'), dict) else {}
    return {
        'task_ctx': task_ctx,
        'objective': str(prepared.get('objective') or ''),
        'target': str(prepared.get('target') or ''),
        'mode': str(prepared.get('mode') or 'fast'),
        'aggression': int(prepared.get('aggression', 1) or 1),
        'owner_auth': bool(prepared.get('owner_auth', False)),
        'owner_override': bool(prepared.get('owner_override', False)),
        'plan_name': str(prepared.get('plan_name') or ''),
        'run_index': int(run_index),
        'last_heartbeat_ts': float(last_heartbeat_ts),
        'confirm_total': int(confirm_total),
    }


def build_deduped_target_plan(raw_plan: list[dict], dedup_key_fn: Callable[[str, str], tuple]) -> list[dict]:
    target_plan: list[dict] = []
    seen_plan_keys = set()
    for entry in raw_plan:
        if not isinstance(entry, dict):
            continue
        key = dedup_key_fn(str(entry.get('objective') or ''), str(entry.get('target') or ''))
        if key in seen_plan_keys:
            continue
        seen_plan_keys.add(key)
        target_plan.append(entry)
    return target_plan


def maybe_preempt_curated_entry(
    entry: dict,
    *,
    preempt_in_curated: bool,
    has_precision_queue: bool,
    has_followup_queue: bool,
    dequeue_task_fn: Callable[[], dict | None],
) -> tuple[dict, bool]:
    if preempt_in_curated and (has_precision_queue or has_followup_queue):
        qtask = dequeue_task_fn()
        if isinstance(qtask, dict):
            return qtask, True
    return entry, False


def prepare_curated_task(
    entry: dict,
    *,
    aggression_override_global: int | None,
    prepare_task_precheck_fn: Callable[..., dict | None],
    clamp_aggression_fn: Callable[[int], int],
    capped_aggression_fn: Callable[[str, str, int], int],
) -> PreparedTask | None:
    objective = entry.get('objective')
    target = entry.get('target')
    if not objective or not target:
        return None
    mode = entry.get('mode', 'fast')
    runtime_task = entry.get('runtime_task') if isinstance(entry.get('runtime_task'), dict) else {}
    prep = prepare_task_precheck_fn(
        objective=str(objective),
        target=str(target),
        mode=str(mode),
        task_family=str(entry.get('task_family') or ''),
        dedup_mode_suffix=False,
        runtime_task=runtime_task,
    )
    if not prep or not bool(prep.get('allowed', False)):
        return None
    planned_aggression = clamp_aggression_fn(int(entry.get('aggression', 6)))
    aggression = int(aggression_override_global) if aggression_override_global is not None else planned_aggression
    aggression = capped_aggression_fn(str(entry.get('task_family') or 'generic'), str(target), aggression)
    task_ctx = dict(entry)
    task_ctx['execution_gate'] = dict(prep.get('gate') or {})
    return {
        'task_ctx': task_ctx,
        'objective': objective,
        'target': target,
        'mode': mode,
        'aggression': aggression,
        'owner_auth': bool(entry.get('owner_approved_auth', False)),
        'owner_override': bool(entry.get('owner_override', False)),
        'plan_name': entry.get('name'),
    }


def unpack_queued_task(
    task: dict,
    *,
    aggression_override_global: int | None,
    clamp_aggression_fn: Callable[[int], int],
    capped_aggression_fn: Callable[[str, str, int], int],
    owner_override_global: bool,
) -> dict[str, Any]:
    objective = task.get('objective')
    target = task.get('target')
    queued_aggression = clamp_aggression_fn(int(task.get('aggression', 6)))
    aggression = int(aggression_override_global) if aggression_override_global is not None else queued_aggression
    aggression = capped_aggression_fn(str(task.get('task_family') or 'generic'), str(target), aggression)
    return {
        'task': task,
        'objective': objective,
        'target': target,
        'aggression': aggression,
        'mode': task.get('mode', 'followup'),
        'owner_auth': bool(task.get('owner_approved_auth', False)),
        'owner_override': bool(owner_override_global or task.get('owner_override', False)),
        'plan_name': task.get('name'),
    }


def prepare_runtime_task(
    task: dict | None,
    *,
    objective: str,
    target: str,
    mode: str,
    aggression: int,
    owner_auth: bool,
    owner_override: bool,
    plan_name: str | None,
    prepare_task_precheck_fn: Callable[..., dict | None],
    scheduled_keys: set,
    attack_family_fn: Callable[[str, str, str], str],
) -> PreparedTask | None:
    runtime_task = {}
    if isinstance(task, dict):
        runtime_task = task.get('runtime_task') if isinstance(task.get('runtime_task'), dict) else {}
    prep = prepare_task_precheck_fn(
        objective=str(objective),
        target=str(target),
        mode=str(mode),
        task_family=str((task or {}).get('task_family') or ''),
        dedup_mode_suffix=True,
        runtime_task=runtime_task,
    )
    if not prep or not bool(prep.get('allowed', False)):
        return None
    scheduled_keys.add(prep['key'])
    task_ctx = dict(task) if isinstance(task, dict) else {
        'objective': objective,
        'target': target,
        'task_family': attack_family_fn(objective, target, ''),
    }
    task_ctx['execution_gate'] = dict(prep.get('gate') or {})
    return {
        'task_ctx': task_ctx,
        'objective': objective,
        'target': target,
        'mode': mode,
        'aggression': aggression,
        'owner_auth': owner_auth,
        'owner_override': owner_override,
        'plan_name': plan_name,
    }


def resolve_main_loop_candidate(
    *,
    task: dict | None,
    history: list[dict],
    scope_targets: list[str],
    runs_count: int,
    owner_override_global: bool,
    aggression_override_global: int | None,
    normalize_runtime_task_fn: Callable[[dict], dict],
    unpack_queued_task_fn: Callable[..., dict[str, Any]],
    clamp_aggression_fn: Callable[[int], int],
    capped_aggression_fn: Callable[[str, str, int], int],
    propose_next_vector_fn: Callable[[list[dict]], tuple[str, str]],
    log_failure_fn: Callable[[str], None],
    log_fallback_fn: Callable[[str, str], None],
) -> dict[str, Any]:
    if task is not None:
        normalized_task = normalize_runtime_task_fn(task)
        queued = unpack_queued_task_fn(
            normalized_task,
            aggression_override_global=aggression_override_global,
            clamp_aggression_fn=clamp_aggression_fn,
            capped_aggression_fn=capped_aggression_fn,
            owner_override_global=owner_override_global,
        )
        queued['status'] = 'ok'
        queued['source'] = 'queue'
        return queued

    owner_auth = False
    owner_override = owner_override_global
    aggression = int(aggression_override_global) if aggression_override_global is not None else clamp_aggression_fn(6)
    mode = 'fast'
    plan_name = None

    try:
        objective, target = propose_next_vector_fn(history)
    except Exception as exc:  # noqa: BLE001
        error_msg = f'brain_proposal_failed: {exc}'
        log_failure_fn(error_msg)
        if scope_targets:
            fallback_target = str(scope_targets[runs_count % len(scope_targets)]).strip()
            if fallback_target and not fallback_target.startswith('http'):
                fallback_target = f'https://{fallback_target}/'
            objective = 'Passive recon and endpoint discovery'
            target = fallback_target or ''
            log_fallback_fn(objective, target)
            return {
                'status': 'ok',
                'source': 'fallback',
                'task': None,
                'objective': objective,
                'target': target,
                'aggression': aggression,
                'mode': mode,
                'owner_auth': owner_auth,
                'owner_override': owner_override,
                'plan_name': plan_name,
            }
        return {
            'status': 'fatal',
            'source': 'brain',
            'task': None,
            'error_msg': error_msg,
            'aggression': aggression,
            'mode': mode,
            'owner_auth': owner_auth,
            'owner_override': owner_override,
            'plan_name': plan_name,
        }

    return {
        'status': 'ok',
        'source': 'brain',
        'task': None,
        'objective': objective,
        'target': target,
        'aggression': aggression,
        'mode': mode,
        'owner_auth': owner_auth,
        'owner_override': owner_override,
        'plan_name': plan_name,
    }
