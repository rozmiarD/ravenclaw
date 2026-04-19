from __future__ import annotations

import copy
import hashlib
import json
from typing import Any


_RUNTIME_FIELDS = [
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
]


def _clean(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _clean(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0])) if v not in (None, '', [], {})}
    if isinstance(value, list):
        return [_clean(v) for v in value if v not in (None, '', [], {})]
    return value



def _sha256_json(value: Any) -> str:
    payload = json.dumps(_clean(value), ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()



def summarize_semantic_lineage(lineage: dict[str, Any] | None) -> dict[str, Any]:
    lineage = dict(lineage or {}) if isinstance(lineage, dict) else {}
    planner_contract = lineage.get('planner_contract') if isinstance(lineage.get('planner_contract'), dict) else {}
    runtime_contract = lineage.get('runtime_contract') if isinstance(lineage.get('runtime_contract'), dict) else {}
    artifact_boundaries = lineage.get('artifact_boundaries') if isinstance(lineage.get('artifact_boundaries'), dict) else {}
    planning_ladder = planner_contract.get('planning_ladder') if isinstance(planner_contract.get('planning_ladder'), dict) else {}
    return {
        'lineage_sha256': str(artifact_boundaries.get('lineage_sha256') or ''),
        'planner_contract_sha256': str(artifact_boundaries.get('planner_contract_sha256') or ''),
        'runtime_contract_sha256': str(artifact_boundaries.get('runtime_contract_sha256') or ''),
        'task_family': str(lineage.get('task_family') or ''),
        'target': str(lineage.get('target') or ''),
        'planner_input_source': str(planner_contract.get('planner_input_source') or ''),
        'experiment_intent_id': str(planner_contract.get('experiment_intent_id') or ''),
        'current_stage': str(planning_ladder.get('current_stage') or ''),
        'next_stage': str(planning_ladder.get('next_stage') or ''),
        'recommended_progression': list(planner_contract.get('recommended_progression') or []),
        'target_surface_rationale': list(planner_contract.get('target_surface_rationale') or []),
        'action_type': str(runtime_contract.get('action_type') or ''),
        'capability': str(runtime_contract.get('capability') or ''),
        'evidence_goal': str(runtime_contract.get('evidence_goal') or ''),
    }



def ensure_semantic_lineage(*, lineage: dict[str, Any] | None = None, task: dict[str, Any] | None = None, runtime_task: dict[str, Any] | None = None, source: str = '') -> dict[str, Any]:
    lineage = dict(lineage or {}) if isinstance(lineage, dict) else {}
    if lineage and str(((lineage.get('artifact_boundaries') or {}).get('lineage_sha256') or '')).strip():
        if not isinstance(lineage.get('summary'), dict):
            lineage['summary'] = summarize_semantic_lineage(lineage)
        return lineage
    return build_semantic_lineage(task=task, runtime_task=runtime_task, source=source)



def ensure_semantic_lineage_summary(*, summary: dict[str, Any] | None = None, lineage: dict[str, Any] | None = None, task: dict[str, Any] | None = None, runtime_task: dict[str, Any] | None = None, source: str = '') -> dict[str, Any]:
    summary = dict(summary or {}) if isinstance(summary, dict) else {}
    if summary and str(summary.get('lineage_sha256') or '').strip():
        return summary
    ensured = ensure_semantic_lineage(lineage=lineage, task=task, runtime_task=runtime_task, source=source)
    return summarize_semantic_lineage(ensured)



def build_semantic_lineage(*, task: dict[str, Any] | None = None, runtime_task: dict[str, Any] | None = None, source: str = '') -> dict[str, Any]:
    task = dict(task or {}) if isinstance(task, dict) else {}
    runtime_task = dict(runtime_task or {}) if isinstance(runtime_task, dict) else {}
    planner_rationale = dict(task.get('planner_rationale') or runtime_task.get('planner_rationale') or {})
    planning_ladder = dict(task.get('planning_ladder') or runtime_task.get('planning_ladder') or planner_rationale.get('planning_ladder') or {})
    recommended_progression = [str(x).strip().lower() for x in (task.get('recommended_progression') or planner_rationale.get('recommended_progression') or []) if str(x).strip()]
    target_surface_rationale = [str(x).strip().lower() for x in (task.get('target_surface_rationale') or planner_rationale.get('target_surface_rationale') or []) if str(x).strip()]
    planner_contract = {
        'experiment_intent_id': str(task.get('experiment_intent_id') or runtime_task.get('experiment_intent_id') or planner_rationale.get('experiment_intent_id') or ''),
        'planner_input_source': str(task.get('planner_input_source') or runtime_task.get('planner_input_source') or planner_rationale.get('planner_input_source') or ''),
        'planner_field_ownership': copy.deepcopy(task.get('planner_field_ownership') or runtime_task.get('planner_field_ownership') or {}),
        'target_profile_summary': copy.deepcopy(planner_rationale.get('target_profile_summary') or {}),
        'target_surface_rationale': list(target_surface_rationale),
        'recommended_progression': list(recommended_progression),
        'planning_ladder': copy.deepcopy(planning_ladder),
    }
    runtime_contract = {field: copy.deepcopy(runtime_task.get(field) if field in runtime_task else task.get(field)) for field in _RUNTIME_FIELDS}
    runtime_contract = {k: v for k, v in runtime_contract.items() if v not in (None, '', [], {})}
    planner_hash = _sha256_json(planner_contract)
    runtime_hash = _sha256_json(runtime_contract)
    lineage_core = {
        'lineage_version': 1,
        'source': str(source or ''),
        'target': str(task.get('target') or runtime_task.get('target') or ''),
        'objective': str(task.get('objective') or runtime_task.get('objective') or ''),
        'task_family': str(task.get('task_family') or runtime_task.get('task_family') or ''),
        'planner_contract': planner_contract,
        'runtime_contract': runtime_contract,
        'artifact_boundaries': {
            'planner_contract_sha256': planner_hash,
            'runtime_contract_sha256': runtime_hash,
            'planner_contract_locked': bool(planner_contract.get('experiment_intent_id') or planner_contract.get('planner_input_source')),
            'runtime_contract_locked': bool(runtime_contract),
        },
    }
    lineage_hash = _sha256_json(lineage_core)
    lineage_core['artifact_boundaries']['lineage_sha256'] = lineage_hash
    lineage_core['summary'] = summarize_semantic_lineage(lineage_core)
    return lineage_core
