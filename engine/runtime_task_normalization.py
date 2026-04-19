from __future__ import annotations

from typing import Any, Dict

from runtime_task_schema import normalize_runtime_task_v2  # type: ignore


def merge_runtime_task_contract_metadata(out: Dict[str, Any], runtime_task: Dict[str, Any]) -> Dict[str, Any]:
    for key in [
        'experiment_intent_id',
        'capability_candidates',
        'recommended_action_types',
        'hypothesis_candidates',
        'open_questions',
        'planner_constraints',
        'planner_preferences',
        'planner_field_ownership',
        'planner_input_source',
        'planning_ladder',
        'action_type',
        'capability',
        'experiment_shape',
        'evidence_goal',
        'exploit_ladder',
        'actor_requirements',
        'session_requirements',
        'promotion_policy',
        'contamination_policy',
        'approval_sensitivity',
    ]:
        if key not in out and key in runtime_task:
            out[key] = runtime_task.get(key)
    return out


def build_normalized_runtime_task_core(task: Dict[str, Any], runtime_task: Dict[str, Any]) -> Dict[str, Any]:
    normalized_runtime_task = normalize_runtime_task_v2(task, runtime_task)
    out = dict(task)
    out['objective'] = str(task.get('objective') or normalized_runtime_task.get('objective') or '')
    out['target'] = str(task.get('target') or normalized_runtime_task.get('target') or '')
    out['task_family'] = str(task.get('task_family') or normalized_runtime_task.get('task_family') or 'generic')
    out['campaign_success_criteria'] = str(task.get('campaign_success_criteria') or normalized_runtime_task.get('campaign_success_criteria') or '')
    out['task_success_criteria'] = str(task.get('task_success_criteria') or task.get('success_criteria') or normalized_runtime_task.get('task_success_criteria') or '')
    out['acceptance_checks'] = list(task.get('acceptance_checks') or normalized_runtime_task.get('acceptance_checks') or [])
    out['evidence_required'] = list(task.get('evidence_required') or normalized_runtime_task.get('evidence_required') or [])
    return out


def ensure_runtime_task_view(out: Dict[str, Any], runtime_task: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(runtime_task, dict) and runtime_task:
        return normalize_runtime_task_v2(out, runtime_task)
    return {
        'target': out['target'],
        'task_family': out['task_family'],
        'acceptance_checks': out['acceptance_checks'],
        'evidence_required': out['evidence_required'],
    }


def normalize_runtime_task(task: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(task, dict):
        return {}
    rt = task.get('runtime_task') if isinstance(task.get('runtime_task'), dict) else {}
    out = build_normalized_runtime_task_core(task, rt)
    out['runtime_task'] = ensure_runtime_task_view(out, rt)
    return merge_runtime_task_contract_metadata(out, out['runtime_task'])
