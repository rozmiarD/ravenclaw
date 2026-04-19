from __future__ import annotations

from typing import Any

from runtime_task_schema import normalize_runtime_task_v2  # type: ignore

PLANNER_INTENT_RUNTIME_SEMANTIC_FIELDS = [
    'action_type',
    'capability',
    'experiment_shape',
    'evidence_goal',
    'priority_tier',
    'expected_depth',
    'activation_phase',
    'activation_mode',
    'conditional_gate',
    'surface_role',
    'target_cluster',
    'exploit_ladder',
    'actor_requirements',
    'session_requirements',
    'promotion_policy',
    'contamination_policy',
    'approval_sensitivity',
]

PLANNER_INTENT_REQUIRED_FIELDS = [
    'intent_id',
    'target',
    'target_host',
    'target_type',
    'task_family',
    'objective',
    'capability_candidates',
    'recommended_action_types',
    'evidence_contract',
    'success_model',
    'planner_constraints',
    'planner_preferences',
    'ambiguity_flags',
    'open_questions',
    'runtime_task_contract',
    'planning_ladder',
    *PLANNER_INTENT_RUNTIME_SEMANTIC_FIELDS,
]

PLANNER_INTENT_REQUIRED_DICT_FIELDS = [
    'evidence_contract',
    'planner_constraints',
    'planner_preferences',
    'runtime_task_contract',
    'planning_ladder',
    'exploit_ladder',
    'actor_requirements',
    'session_requirements',
    'promotion_policy',
    'contamination_policy',
    'approval_sensitivity',
]

PLANNER_INTENT_REQUIRED_STRING_FIELDS = [
    'action_type',
    'capability',
    'experiment_shape',
    'evidence_goal',
    'priority_tier',
    'expected_depth',
    'activation_mode',
    'conditional_gate',
    'surface_role',
    'target_cluster',
]

_ALLOWED_TARGET_TYPES = {'api', 'web', 'auth', 'static', 'sandbox', 'integration', 'support', 'host'}


def _text(value: Any) -> str:
    return str(value or '').strip()



def _list_text(value: Any, *, lower: bool = False, limit: int = 12) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        text = _text(item)
        if lower:
            text = text.lower()
        if text and text not in out:
            out.append(text)
        if len(out) >= limit:
            break
    return out



def _dedupe_keep_order(values: list[str]) -> list[str]:
    out: list[str] = []
    for value in values:
        text = _text(value).lower()
        if text and text not in out:
            out.append(text)
    return out



def build_planning_ladder(*, runtime_task_contract: dict[str, Any] | None, success_model: str = '', task_family: str = '', recommended_action_types: list[str] | None = None) -> dict[str, Any]:
    runtime_task_contract = dict(runtime_task_contract or {}) if isinstance(runtime_task_contract, dict) else {}
    exploit_ladder = dict(runtime_task_contract.get('exploit_ladder') or {}) if isinstance(runtime_task_contract.get('exploit_ladder'), dict) else {}
    progression = _list_text(exploit_ladder.get('progression') or [], lower=True, limit=8)
    current_stage = _text(exploit_ladder.get('stage') or (progression[0] if progression else 'validation')).lower() or 'validation'
    if not progression:
        progression = [current_stage]
    next_stage = ''
    if current_stage in progression:
        idx = progression.index(current_stage)
        if idx + 1 < len(progression):
            next_stage = progression[idx + 1]
    elif progression:
        next_stage = progression[0]
    session_requirements = dict(runtime_task_contract.get('session_requirements') or {}) if isinstance(runtime_task_contract.get('session_requirements'), dict) else {}
    actor_requirements = dict(runtime_task_contract.get('actor_requirements') or {}) if isinstance(runtime_task_contract.get('actor_requirements'), dict) else {}
    promotion_policy = dict(runtime_task_contract.get('promotion_policy') or {}) if isinstance(runtime_task_contract.get('promotion_policy'), dict) else {}
    prerequisites = _list_text(session_requirements.get('prerequisites') or [], lower=False, limit=8)
    action_candidates = _list_text(recommended_action_types or runtime_task_contract.get('recommended_action_types') or [], lower=True, limit=6)
    return {
        'planning_mode': 'laddered',
        'task_family': _text(task_family).lower() or _text(runtime_task_contract.get('task_family')).lower() or 'generic',
        'success_model': _text(success_model),
        'current_stage': current_stage,
        'next_stage': next_stage,
        'stage_progression': progression,
        'proof_strategy': _text(exploit_ladder.get('proof_strategy') or ''),
        'stateful': bool(session_requirements.get('stateful')),
        'auth_context': bool(session_requirements.get('auth_context')),
        'differential': bool(actor_requirements.get('differential')),
        'bounded_only': bool(promotion_policy.get('bounded_only', True)),
        'prerequisites': prerequisites,
        'recommended_action_types': action_candidates,
    }



def recommended_progression_from_planning_ladder(*, planning_ladder: dict[str, Any] | None, target_type: str = '', preferred_vector_families: list[str] | None = None) -> list[str]:
    ladder = dict(planning_ladder or {}) if isinstance(planning_ladder, dict) else {}
    target_type_l = _text(target_type).lower() or 'host'
    stage_progression = _list_text(ladder.get('stage_progression') or [], lower=True, limit=8)
    current_stage = _text(ladder.get('current_stage') or '').lower()
    next_stage = _text(ladder.get('next_stage') or '').lower()
    recommended_actions = _list_text(ladder.get('recommended_action_types') or [], lower=True, limit=4)
    preferred_vectors = _list_text(preferred_vector_families or [], lower=True, limit=4)
    if current_stage and current_stage in stage_progression:
        current_idx = stage_progression.index(current_stage)
        stage_window = stage_progression[current_idx:]
    else:
        stage_window = stage_progression[:]
    hints: list[str] = []
    if target_type_l in {'api', 'auth', 'integration'}:
        hints.append('authenticated_or_boundary_mapping')
    elif target_type_l in {'web'}:
        hints.append('browser_flow_mapping')
    elif target_type_l in {'static', 'support'}:
        hints.append('artifact_capture')
    if current_stage:
        hints.append(current_stage)
    if next_stage and next_stage != current_stage:
        hints.append(next_stage)
    hints.extend(stage_window)
    hints.extend(recommended_actions[:2])
    hints.extend(preferred_vectors[:2])
    return _dedupe_keep_order(hints)[:8] or ['recon', 'validation', 'deeper_family']



def validate_experiment_intent_contract(intent: dict[str, Any]) -> None:
    if not isinstance(intent, dict):
        raise ValueError('experiment_intent_item_not_dict')
    runtime_task_contract = dict(intent.get('runtime_task_contract') or {}) if isinstance(intent.get('runtime_task_contract'), dict) else {}
    if int(runtime_task_contract.get('schema_version', 0) or 0) != 2:
        raise ValueError('experiment_intent_runtime_task_contract_invalid')
    for field in PLANNER_INTENT_RUNTIME_SEMANTIC_FIELDS:
        if intent.get(field) != runtime_task_contract.get(field):
            raise ValueError(f'experiment_intent_mirror_mismatch_{field}')
    planning_ladder = dict(intent.get('planning_ladder') or {}) if isinstance(intent.get('planning_ladder'), dict) else {}
    expected_ladder = build_planning_ladder(
        runtime_task_contract=runtime_task_contract,
        success_model=_text(intent.get('success_model') or ''),
        task_family=_text(intent.get('task_family') or runtime_task_contract.get('task_family') or ''),
        recommended_action_types=list(intent.get('recommended_action_types') or runtime_task_contract.get('recommended_action_types') or []),
    )
    if planning_ladder != expected_ladder:
        raise ValueError('experiment_intent_planning_ladder_mismatch')
    target_type = _text(intent.get('target_type') or '').lower() or 'host'
    if target_type not in _ALLOWED_TARGET_TYPES:
        raise ValueError('experiment_intent_target_type_invalid')



def compose_experiment_intent_contract(*, base_intent: dict[str, Any], runtime_task_contract: dict[str, Any] | None, success_model: str = '') -> dict[str, Any]:
    out = dict(base_intent or {})
    normalized_runtime_task = normalize_runtime_task_v2(out, runtime_task_contract or {})
    planner_execution_defaults = {
        'priority_tier': 'medium',
        'expected_depth': 'medium',
        'activation_phase': 1,
        'activation_mode': 'immediate',
        'conditional_gate': 'none',
        'surface_role': 'primary',
        'target_cluster': 'general',
    }
    for key, default in planner_execution_defaults.items():
        if normalized_runtime_task.get(key) in (None, ''):
            normalized_runtime_task[key] = default
    out['runtime_task_contract'] = normalized_runtime_task
    for field in PLANNER_INTENT_RUNTIME_SEMANTIC_FIELDS:
        out[field] = normalized_runtime_task.get(field)
    out['planning_ladder'] = build_planning_ladder(
        runtime_task_contract=normalized_runtime_task,
        success_model=_text(success_model or out.get('success_model') or ''),
        task_family=_text(out.get('task_family') or normalized_runtime_task.get('task_family') or ''),
        recommended_action_types=list(out.get('recommended_action_types') or normalized_runtime_task.get('recommended_action_types') or []),
    )
    validate_experiment_intent_contract(out)
    return out
