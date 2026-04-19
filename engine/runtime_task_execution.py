from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Tuple

from campaign_utils import extract_host_from_url  # type: ignore

from runtime_execution_deps import RuntimeExecutionDeps  # type: ignore
from semantic_lineage import ensure_semantic_lineage, ensure_semantic_lineage_summary  # type: ignore


TaskExecutionResult = Tuple[dict, str, str, str, str, bool, dict, dict, bool, dict]
HOST_TOKEN_RE = re.compile(r"(https?://[^\s\"'<>]+)|\b((?:[a-z0-9-]+\.)+[a-z]{2,})\b", re.IGNORECASE)


def _extract_hosts_from_text(text: Any) -> list[str]:
    raw = str(text or '').strip()
    if not raw:
        return []
    hosts: list[str] = []
    seen: set[str] = set()
    direct = str(extract_host_from_url(raw) or '').strip().lower()
    if direct:
        seen.add(direct)
        hosts.append(direct)
    for match in HOST_TOKEN_RE.finditer(raw):
        token = str(match.group(1) or match.group(2) or '').strip().lower()
        host = str(extract_host_from_url(token) or token).strip().lower()
        if host and host not in seen:
            seen.add(host)
            hosts.append(host)
    return hosts


def _string_is_target_bound(text: Any, target: str) -> bool:
    target_host = str(extract_host_from_url(target) or '').strip().lower()
    if not target_host:
        return True
    mentioned = _extract_hosts_from_text(text)
    if not mentioned:
        return True
    return all(host == target_host for host in mentioned)


def _sanitize_text_list_for_target(items: Any, target: str) -> list[str]:
    return [str(x).strip() for x in (items or []) if str(x).strip() and _string_is_target_bound(x, target)]


def _sanitize_runtime_task_for_target(task: dict, target: str) -> dict:
    runtime_task = dict(task or {}) if isinstance(task, dict) else {}
    runtime_task['hypothesis_candidates'] = _sanitize_text_list_for_target(runtime_task.get('hypothesis_candidates') or [], target)
    runtime_task['open_questions'] = _sanitize_text_list_for_target(runtime_task.get('open_questions') or [], target)
    return runtime_task


def _build_runtime_task_execution_result(
    *,
    result: dict,
    classification: str,
    auditor: str,
    engine_status: str,
    summary_text: str,
    error_flag: bool,
    post: dict,
    qual: dict,
    promising: bool,
    run_info: dict,
) -> TaskExecutionResult:
    final_summary_text = str((post or {}).get('summary_text') or summary_text)
    final_classification = str((post or {}).get('classification') or classification)
    return (
        result,
        final_classification,
        str(auditor),
        str(engine_status),
        final_summary_text,
        bool(error_flag),
        post,
        qual,
        bool(promising),
        run_info,
    )


def _build_execute_runtime_context(
    *,
    objective: str,
    target: str,
    mode: str,
    aggression: int,
    owner_auth: bool,
    owner_override: bool,
    plan_name: str | None,
    run_index: int,
) -> dict:
    objective_s = str(objective)
    target_s = str(target)
    mode_s = str(mode)
    aggression_i = int(aggression)
    owner_auth_b = bool(owner_auth)
    owner_override_b = bool(owner_override)
    plan_name_s = str(plan_name or '')
    decision_label = plan_name_s or objective_s or f'run-{run_index}'
    return {
        'objective': objective_s,
        'target': target_s,
        'mode': mode_s,
        'aggression': aggression_i,
        'owner_auth': owner_auth_b,
        'owner_override': owner_override_b,
        'plan_name': plan_name_s,
        'decision_label': decision_label,
    }


def _build_dispatch_runtime_request(
    *,
    task_ctx: dict,
    objective: str,
    target: str,
    aggression: int,
    owner_auth: bool,
    owner_override: bool,
) -> dict:
    return {
        'objective': str(objective),
        'target': str(target),
        'aggression': int(aggression),
        'owner_auth': bool(owner_auth),
        'owner_override': bool(owner_override),
        **_build_run_pipeline_runtime_payload(task_ctx, target),
    }


def _build_run_pipeline_runtime_payload(task_ctx: dict, target: str = '') -> dict:
    task = task_ctx if isinstance(task_ctx, dict) else {}
    runtime_task = _sanitize_runtime_task_for_target(task.get('runtime_task') if isinstance(task.get('runtime_task'), dict) else {}, target)
    planner_rationale = dict(task.get('planner_rationale') or runtime_task.get('planner_rationale') or {})
    planning_ladder = dict(task.get('planning_ladder') or runtime_task.get('planning_ladder') or planner_rationale.get('planning_ladder') or {})
    target_surface_rationale = [str(x).strip().lower() for x in (task.get('target_surface_rationale') or planner_rationale.get('target_surface_rationale') or []) if str(x).strip()]
    recommended_progression = [str(x).strip().lower() for x in (task.get('recommended_progression') or planner_rationale.get('recommended_progression') or []) if str(x).strip()]
    semantic_lineage = ensure_semantic_lineage(
        lineage=(task.get('semantic_lineage') if isinstance(task.get('semantic_lineage'), dict) else (runtime_task.get('semantic_lineage') if isinstance(runtime_task.get('semantic_lineage'), dict) else {})),
        task=task,
        runtime_task=runtime_task,
        source='runtime_execution_payload',
    )
    semantic_lineage_summary = ensure_semantic_lineage_summary(lineage=semantic_lineage)
    return {
        'success_criteria': str(task.get('task_success_criteria') or ''),
        'campaign_success_criteria': str(task.get('campaign_success_criteria') or ''),
        'task_family': str(task.get('task_family') or runtime_task.get('task_family') or 'generic'),
        'acceptance_checks': ','.join(str(x) for x in (task.get('acceptance_checks') or runtime_task.get('acceptance_checks') or []) if str(x).strip()),
        'evidence_required': ','.join(str(x) for x in (task.get('evidence_required') or runtime_task.get('evidence_required') or []) if str(x).strip()),
        'success_semantics_json': json.dumps(dict(task.get('success_semantics') or runtime_task.get('success_semantics') or {}), ensure_ascii=False),
        'experiment_intent_id': str(task.get('experiment_intent_id') or runtime_task.get('experiment_intent_id') or ''),
        'capability_candidates_json': json.dumps(list(task.get('capability_candidates') or runtime_task.get('capability_candidates') or []), ensure_ascii=False),
        'recommended_action_types_json': json.dumps(list(task.get('recommended_action_types') or runtime_task.get('recommended_action_types') or []), ensure_ascii=False),
        'hypothesis_candidates_json': json.dumps(list(task.get('hypothesis_candidates') or runtime_task.get('hypothesis_candidates') or []), ensure_ascii=False),
        'planner_constraints_json': json.dumps(dict(task.get('planner_constraints') or runtime_task.get('planner_constraints') or {}), ensure_ascii=False),
        'planner_preferences_json': json.dumps(dict(task.get('planner_preferences') or runtime_task.get('planner_preferences') or {}), ensure_ascii=False),
        'planner_rationale_json': json.dumps(planner_rationale, ensure_ascii=False),
        'planning_ladder_json': json.dumps(planning_ladder, ensure_ascii=False),
        'target_surface_rationale_json': json.dumps(target_surface_rationale, ensure_ascii=False),
        'recommended_progression_json': json.dumps(recommended_progression, ensure_ascii=False),
        'semantic_lineage_json': json.dumps(semantic_lineage, ensure_ascii=False),
        'semantic_lineage_summary_json': json.dumps(semantic_lineage_summary, ensure_ascii=False),
        'open_questions_json': json.dumps(list(task.get('open_questions') or runtime_task.get('open_questions') or []), ensure_ascii=False),
    }


def _build_post_runtime_inputs(
    *,
    task_ctx: dict,
    ctx: dict,
    result: dict,
    summary_text: str,
    classification: str,
    auditor: str,
    engine_status: str,
    run_index: int,
    deps: RuntimeExecutionDeps,
    host_family_owner_gate: dict,
    host_cooldown_until: dict,
    host_code000_streak: dict,
    host_code000_total: dict,
    host_403_streak: dict,
    host_fail_streak: dict,
    host_fail_count: dict,
    host_success_count: dict,
    code000_streak_threshold: int,
    code000_cooldown_sec: int,
    code000_session_cap: int,
    toggles: dict,
) -> dict:
    return {
        'task_ctx': task_ctx,
        'result': result,
        'objective': ctx['objective'],
        'target': ctx['target'],
        'mode': ctx['mode'],
        'summary_text': str(summary_text),
        'classification': str(classification),
        'auditor': str(auditor),
        'engine_status': str(engine_status),
        'run_index': int(run_index),
        'plan_name': ctx['plan_name'],
        'owner_override': ctx['owner_override'],
        'owner_auth': ctx['owner_auth'],
        'aggression': ctx['aggression'],
        'inspect_json_signal_from_command': deps.inspect_json_signal_from_command_fn,
        'parse_rc_metrics': deps.parse_rc_metrics_fn,
        'run_control_comparison': deps.run_control_comparison_fn,
        'attack_family_fn': deps.attack_family_fn,
        'host_family_owner_gate': host_family_owner_gate,
        'host_cooldown_until': host_cooldown_until,
        'host_code000_streak': host_code000_streak,
        'host_code000_total': host_code000_total,
        'host_403_streak': host_403_streak,
        'host_fail_streak': host_fail_streak,
        'host_fail_count': host_fail_count,
        'host_success_count': host_success_count,
        'code000_streak_threshold': int(code000_streak_threshold),
        'code000_cooldown_sec': int(code000_cooldown_sec),
        'code000_session_cap': int(code000_session_cap),
        'transport_observation_cooldown_sec': int((toggles or {}).get('transport_observation_cooldown_sec', 600) or 600),
        'http_403_streak_threshold': int((toggles or {}).get('http_403_streak_threshold', 4) or 4),
        'http_403_cooldown_sec': int((toggles or {}).get('http_403_cooldown_sec', 1800) or 1800),
        'code000_session_cooldown_sec': int((toggles or {}).get('code000_session_cooldown_sec', 86400) or 86400),
    }



def _build_qualify_runtime_inputs(
    *,
    ctx: dict,
    post: dict,
    run_index: int,
    error_flag: bool,
    runs: list[dict],
    toggles: dict,
    host_weak_count: dict,
    quality_telemetry: dict,
    qualification_mode: str,
    qualification_promising_threshold: str,
    deps: RuntimeExecutionDeps,
) -> dict:
    return {
        'post': post,
        'objective': ctx['objective'],
        'target': ctx['target'],
        'mode': ctx['mode'],
        'run_index': int(run_index),
        'decision_label': ctx['decision_label'],
        'owner_override': ctx['owner_override'],
        'aggression': ctx['aggression'],
        'error_flag': bool(error_flag),
        'policy_diag_logging': bool(toggles.get('policy_diag_logging', False)),
        'force_auth_like_weak_on_http_controls': bool(toggles.get('force_auth_like_weak_on_http_controls', False)),
        'repeated_consistency': deps.repeated_consistency_ok_fn(runs, ctx['target'], ctx['objective']),
        'host_weak_count': host_weak_count,
        'quality_telemetry': quality_telemetry,
        'decision_toggles': toggles,
        'qualification_mode': qualification_mode,
        'qualification_promising_threshold': qualification_promising_threshold,
        'qualify_fn': deps.qualify_fn,
        'can_be_confirmed_fn': deps.can_be_confirmed_fn,
        'compute_promising_fn': deps.compute_promising_fn,
        'finding_lifecycle_fn': deps.finding_lifecycle_fn,
        'adaptive_aggression_fn': deps.adaptive_aggression_fn,
        'normalize_pipeline_status_fn': deps.normalize_pipeline_status_fn,
        'log_event_fn': deps.log_event_fn,
    }



def _build_runtime_result_stage_inputs(
    *,
    task_ctx: dict,
    ctx: dict,
    result: dict,
    run_index: int,
    deps: RuntimeExecutionDeps,
    host_family_owner_gate: dict,
    host_cooldown_until: dict,
    host_code000_streak: dict,
    host_code000_total: dict,
    host_403_streak: dict,
    host_fail_streak: dict,
    host_fail_count: dict,
    host_success_count: dict,
    code000_streak_threshold: int,
    code000_cooldown_sec: int,
    code000_session_cap: int,
    runs: list[dict],
    toggles: dict,
    host_weak_count: dict,
    quality_telemetry: dict,
    qualification_mode: str,
    qualification_promising_threshold: str,
) -> dict:
    return {
        'task_ctx': task_ctx,
        'ctx': ctx,
        'result': result,
        'run_index': int(run_index),
        'deps': deps,
        'host_family_owner_gate': host_family_owner_gate,
        'host_cooldown_until': host_cooldown_until,
        'host_code000_streak': host_code000_streak,
        'host_code000_total': host_code000_total,
        'host_403_streak': host_403_streak,
        'host_fail_streak': host_fail_streak,
        'host_fail_count': host_fail_count,
        'host_success_count': host_success_count,
        'code000_streak_threshold': int(code000_streak_threshold),
        'code000_cooldown_sec': int(code000_cooldown_sec),
        'code000_session_cap': int(code000_session_cap),
        'runs': runs,
        'toggles': toggles,
        'host_weak_count': host_weak_count,
        'quality_telemetry': quality_telemetry,
        'qualification_mode': qualification_mode,
        'qualification_promising_threshold': qualification_promising_threshold,
    }



def _process_runtime_task_result(
    *,
    task_ctx: dict,
    ctx: dict,
    result: dict,
    run_index: int,
    deps: RuntimeExecutionDeps,
    host_family_owner_gate: dict,
    host_cooldown_until: dict,
    host_code000_streak: dict,
    host_code000_total: dict,
    host_403_streak: dict,
    host_fail_streak: dict,
    host_fail_count: dict,
    host_success_count: dict,
    code000_streak_threshold: int,
    code000_cooldown_sec: int,
    code000_session_cap: int,
    runs: list[dict],
    toggles: dict,
    host_weak_count: dict,
    quality_telemetry: dict,
    qualification_mode: str,
    qualification_promising_threshold: str,
) -> TaskExecutionResult:
    classification, auditor, engine_status, summary_text, error_flag = deps.summarize_result_fn(result)
    post_inputs = _build_post_runtime_inputs(
        task_ctx=task_ctx,
        ctx=ctx,
        result=result,
        summary_text=summary_text,
        classification=classification,
        auditor=auditor,
        engine_status=engine_status,
        run_index=run_index,
        deps=deps,
        host_family_owner_gate=host_family_owner_gate,
        host_cooldown_until=host_cooldown_until,
        host_code000_streak=host_code000_streak,
        host_code000_total=host_code000_total,
        host_403_streak=host_403_streak,
        host_fail_streak=host_fail_streak,
        host_fail_count=host_fail_count,
        host_success_count=host_success_count,
        code000_streak_threshold=code000_streak_threshold,
        code000_cooldown_sec=code000_cooldown_sec,
        code000_session_cap=code000_session_cap,
        toggles=toggles,
    )
    post = deps.post_result_common_fn(**post_inputs)
    qualify_inputs = _build_qualify_runtime_inputs(
        ctx=ctx,
        post=post,
        run_index=run_index,
        error_flag=bool(error_flag),
        runs=runs,
        toggles=toggles,
        host_weak_count=host_weak_count,
        quality_telemetry=quality_telemetry,
        qualification_mode=qualification_mode,
        qualification_promising_threshold=qualification_promising_threshold,
        deps=deps,
    )
    qual, promising, run_info = deps.qualify_and_finalize_run_fn(**qualify_inputs)
    return _build_runtime_task_execution_result(
        result=result,
        classification=classification,
        auditor=auditor,
        engine_status=engine_status,
        summary_text=summary_text,
        error_flag=bool(error_flag),
        post=post,
        qual=qual,
        promising=promising,
        run_info=run_info,
    )



def _emit_runtime_dispatch_events(
    *,
    label: str,
    target: str,
    mode: str,
    run_index: int,
    last_heartbeat_ts: float,
    runs_count: int,
    followup_queue_len: int,
    precision_queue_len: int,
    log_event_fn: Callable[..., None],
) -> float:
    log_event_fn('AUTO_CAMPAIGN', label, 'in_progress', f'Target={target}', actor='auto_campaign')
    log_event_fn('AUTO_CAMPAIGN', 'vector_dispatch', 'in_progress', f'idx={run_index};mode={mode};target={target}', actor='auto_campaign')
    now_hb = datetime.now(timezone.utc).timestamp()
    if now_hb - last_heartbeat_ts >= 30:
        last_heartbeat_ts = now_hb
        log_event_fn('AUTO_CAMPAIGN', 'pipeline_heartbeat', 'in_progress', f'runs={runs_count};followup_q={followup_queue_len};precision_q={precision_queue_len}', actor='auto_campaign', row_type='service')
    return last_heartbeat_ts



def _invoke_runtime_dispatch_request(request: dict, *, run_pipeline_fn: Callable[..., dict]) -> dict:
    return run_pipeline_fn(
        request['objective'],
        request['target'],
        aggression=int(request['aggression']),
        owner_auth=bool(request['owner_auth']),
        owner_override=bool(request['owner_override']),
        **{k: v for k, v in request.items() if k not in {'objective', 'target', 'aggression', 'owner_auth', 'owner_override'}},
    )



def dispatch_runtime_task(
    *,
    task_ctx: dict,
    objective: str,
    target: str,
    mode: str,
    aggression: int,
    owner_auth: bool,
    owner_override: bool,
    label: str,
    run_index: int,
    last_heartbeat_ts: float,
    runs_count: int,
    followup_queue_len: int,
    precision_queue_len: int,
    log_event_fn: Callable[..., None],
    run_pipeline_fn: Callable[..., dict],
) -> tuple[dict, float]:
    last_heartbeat_ts = _emit_runtime_dispatch_events(
        label=label,
        target=target,
        mode=mode,
        run_index=run_index,
        last_heartbeat_ts=last_heartbeat_ts,
        runs_count=runs_count,
        followup_queue_len=followup_queue_len,
        precision_queue_len=precision_queue_len,
        log_event_fn=log_event_fn,
    )
    request = _build_dispatch_runtime_request(
        task_ctx=task_ctx,
        objective=objective,
        target=target,
        aggression=aggression,
        owner_auth=owner_auth,
        owner_override=owner_override,
    )
    result = _invoke_runtime_dispatch_request(request, run_pipeline_fn=run_pipeline_fn)
    return result, last_heartbeat_ts


def _build_runtime_dispatch_stage_inputs(
    *,
    task_ctx: dict,
    ctx: dict,
    run_index: int,
    last_heartbeat_ts: float,
    runs_count: int,
    followup_queue_len: int,
    precision_queue_len: int,
    deps: RuntimeExecutionDeps,
) -> dict:
    return {
        'task_ctx': task_ctx,
        'objective': ctx['objective'],
        'target': ctx['target'],
        'mode': ctx['mode'],
        'aggression': ctx['aggression'],
        'owner_auth': ctx['owner_auth'],
        'owner_override': ctx['owner_override'],
        'label': ctx['decision_label'],
        'run_index': int(run_index),
        'last_heartbeat_ts': float(last_heartbeat_ts),
        'runs_count': int(runs_count),
        'followup_queue_len': int(followup_queue_len),
        'precision_queue_len': int(precision_queue_len),
        'log_event_fn': deps.log_event_fn,
        'run_pipeline_fn': deps.run_pipeline_fn,
    }



def _run_runtime_dispatch_stage(
    *,
    task_ctx: dict,
    ctx: dict,
    run_index: int,
    last_heartbeat_ts: float,
    runs_count: int,
    followup_queue_len: int,
    precision_queue_len: int,
    deps: RuntimeExecutionDeps,
) -> tuple[dict, float]:
    dispatch_inputs = _build_runtime_dispatch_stage_inputs(
        task_ctx=task_ctx,
        ctx=ctx,
        run_index=run_index,
        last_heartbeat_ts=last_heartbeat_ts,
        runs_count=runs_count,
        followup_queue_len=followup_queue_len,
        precision_queue_len=precision_queue_len,
        deps=deps,
    )
    return dispatch_runtime_task(**dispatch_inputs)



def execute_runtime_task_pipeline(
    *,
    task_ctx: dict,
    objective: str,
    target: str,
    mode: str,
    aggression: int,
    owner_auth: bool,
    owner_override: bool,
    plan_name: str | None,
    run_index: int,
    last_heartbeat_ts: float,
    runs_count: int,
    followup_queue_len: int,
    precision_queue_len: int,
    deps: RuntimeExecutionDeps,
    host_family_owner_gate: dict,
    host_cooldown_until: dict,
    host_code000_streak: dict,
    host_code000_total: dict,
    host_403_streak: dict,
    host_fail_streak: dict,
    host_fail_count: dict,
    host_success_count: dict,
    code000_streak_threshold: int,
    code000_cooldown_sec: int,
    code000_session_cap: int,
    runs: list[dict],
    toggles: dict,
    host_weak_count: dict,
    quality_telemetry: dict,
    qualification_mode: str,
    qualification_promising_threshold: str,
) -> tuple[float, TaskExecutionResult]:
    ctx = _build_execute_runtime_context(
        objective=objective,
        target=target,
        mode=mode,
        aggression=aggression,
        owner_auth=owner_auth,
        owner_override=owner_override,
        plan_name=plan_name,
        run_index=run_index,
    )
    result, last_heartbeat_ts = _run_runtime_dispatch_stage(
        task_ctx=task_ctx,
        ctx=ctx,
        run_index=run_index,
        last_heartbeat_ts=last_heartbeat_ts,
        runs_count=runs_count,
        followup_queue_len=followup_queue_len,
        precision_queue_len=precision_queue_len,
        deps=deps,
    )
    result_stage_inputs = _build_runtime_result_stage_inputs(
        task_ctx=task_ctx,
        ctx=ctx,
        result=result,
        run_index=run_index,
        deps=deps,
        host_family_owner_gate=host_family_owner_gate,
        host_cooldown_until=host_cooldown_until,
        host_code000_streak=host_code000_streak,
        host_code000_total=host_code000_total,
        host_403_streak=host_403_streak,
        host_fail_streak=host_fail_streak,
        host_fail_count=host_fail_count,
        host_success_count=host_success_count,
        code000_streak_threshold=code000_streak_threshold,
        code000_cooldown_sec=code000_cooldown_sec,
        code000_session_cap=code000_session_cap,
        runs=runs,
        toggles=toggles,
        host_weak_count=host_weak_count,
        quality_telemetry=quality_telemetry,
        qualification_mode=qualification_mode,
        qualification_promising_threshold=qualification_promising_threshold,
    )
    return last_heartbeat_ts, _process_runtime_task_result(**result_stage_inputs)
