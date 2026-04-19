from __future__ import annotations

from typing import Any, Dict

from action_schema import (  # type: ignore
    ACTION_TYPE_TO_CAPABILITY,
    ACTION_TYPE_TO_EXPERIMENT_SHAPE,
    DEFAULT_ACTION_TYPE,
    DEFAULT_CAPABILITY,
)

RUNTIME_TASK_SCHEMA_VERSION = 2

_ALLOWED_LADDER_STAGES = {
    'discovery',
    'validation',
    'control_boundary_confirmation',
    'state_transition_confirmation',
    'bounded_exploit_proof',
    'report_artifact_capture',
}

_ACTIVATION_PHASE_MAP = {
    'discovery': 1,
    'validation': 1,
    'control_boundary_confirmation': 2,
    'state_transition_confirmation': 2,
    'bounded_exploit_proof': 3,
    'report_artifact_capture': 3,
}


def _text(value: Any) -> str:
    return str(value or '').strip()



def _lower(value: Any) -> str:
    return _text(value).lower()



def _enum(value: Any, *, allowed: set[str], default: str) -> str:
    normalized = _lower(value) or default
    return normalized if normalized in allowed else default



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



def _dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}



def _activation_phase(value: Any) -> int:
    raw = _lower(value)
    if not raw:
        return 1
    if raw.isdigit():
        return max(1, min(3, int(raw)))
    return _ACTIVATION_PHASE_MAP.get(raw, 1)



def _default_exploit_ladder(task_family: str, action_type: str, experiment_shape: str) -> dict[str, Any]:
    fam = _lower(task_family)
    if fam in {'authz', 'idor'}:
        return {
            'stage': 'control_boundary_confirmation',
            'progression': ['discovery', 'validation', 'control_boundary_confirmation', 'bounded_exploit_proof', 'report_artifact_capture'],
            'proof_strategy': 'actor_or_object_boundary_delta',
        }
    if fam in {'logic', 'workflow', 'state_transition'} or action_type == 'state_transition_probe' or experiment_shape == 'state_transition':
        return {
            'stage': 'state_transition_confirmation',
            'progression': ['discovery', 'validation', 'state_transition_confirmation', 'bounded_exploit_proof', 'report_artifact_capture'],
            'proof_strategy': 'forbidden_transition_or_invariant_break',
        }
    if fam in {'input_tamper', 'redirect_trust', 'client_input'}:
        return {
            'stage': 'validation',
            'progression': ['discovery', 'validation', 'bounded_exploit_proof', 'report_artifact_capture'],
            'proof_strategy': 'safe_input_or_trust_boundary_validation',
        }
    if fam in {'recon', 'content_discovery', 'historical_url_mining', 'tls_assessment', 'secret_hunt'}:
        return {
            'stage': 'discovery',
            'progression': ['discovery', 'validation', 'report_artifact_capture'],
            'proof_strategy': 'surface_expansion_and_pivot_selection',
        }
    return {
        'stage': 'validation',
        'progression': ['discovery', 'validation', 'bounded_exploit_proof', 'report_artifact_capture'],
        'proof_strategy': 'bounded_validation',
    }



def _normalize_exploit_ladder(raw: Any, *, task_family: str, action_type: str, experiment_shape: str) -> dict[str, Any]:
    base = _default_exploit_ladder(task_family, action_type, experiment_shape)
    source = _dict(raw)
    stage = _lower(source.get('stage') or base.get('stage') or 'validation')
    if stage not in _ALLOWED_LADDER_STAGES:
        stage = str(base.get('stage') or 'validation')
    progression = _list_text(source.get('progression') or base.get('progression') or [], lower=True, limit=8)
    progression = [p for p in progression if p in _ALLOWED_LADDER_STAGES] or list(base.get('progression') or [])
    proof_strategy = _text(source.get('proof_strategy') or base.get('proof_strategy') or 'bounded_validation')
    return {
        'stage': stage,
        'progression': progression,
        'proof_strategy': proof_strategy,
    }



def _normalize_actor_requirements(raw: Any, task_family: str) -> dict[str, Any]:
    source = _dict(raw)
    fam = _lower(task_family)
    required = bool(source.get('required', fam in {'authz', 'idor', 'auth_flow', 'logic', 'workflow', 'state_transition'}))
    differential = bool(source.get('differential', fam in {'authz', 'idor'}))
    return {
        'required': required,
        'differential': differential,
        'preferred_roles': _list_text(source.get('preferred_roles'), lower=True, limit=6),
    }



def _normalize_session_requirements(raw: Any, task_family: str, experiment_shape: str) -> dict[str, Any]:
    source = _dict(raw)
    fam = _lower(task_family)
    stateful = bool(source.get('stateful', fam in {'auth_flow', 'logic', 'workflow', 'state_transition'} or experiment_shape == 'state_transition'))
    auth_context = bool(source.get('auth_context', fam in {'authz', 'idor', 'auth_flow', 'logic', 'workflow', 'state_transition'}))
    return {
        'stateful': stateful,
        'auth_context': auth_context,
        'prerequisites': _list_text(source.get('prerequisites'), lower=False, limit=8),
    }



def _normalize_promotion_policy(raw: Any, task_family: str) -> dict[str, Any]:
    source = _dict(raw)
    fam = _lower(task_family)
    return {
        'followup_allowed': bool(source.get('followup_allowed', True)),
        'confirm_preferred': bool(source.get('confirm_preferred', fam in {'authz', 'idor', 'logic', 'workflow', 'state_transition'})),
        'bounded_only': bool(source.get('bounded_only', True)),
    }



def _normalize_contamination_policy(raw: Any) -> dict[str, Any]:
    source = _dict(raw)
    return {
        'learning_excluded_on_cross_host_mismatch': bool(source.get('learning_excluded_on_cross_host_mismatch', True)),
        'learning_excluded_on_hygiene_violation': bool(source.get('learning_excluded_on_hygiene_violation', True)),
    }



def _normalize_approval_sensitivity(raw: Any, planner_constraints: dict[str, Any], task_family: str) -> dict[str, Any]:
    source = _dict(raw)
    fam = _lower(task_family)
    approval_required = bool(source.get('owner_approval_required', planner_constraints.get('owner_approval_required', False)))
    auth_sensitive = bool(source.get('auth_sensitive', planner_constraints.get('credentials_required', fam in {'authz', 'auth_flow', 'logic', 'workflow', 'state_transition'})))
    return {
        'owner_approval_required': approval_required,
        'auth_sensitive': auth_sensitive,
    }



def normalize_runtime_task_v2(task: dict[str, Any] | None, runtime_task: dict[str, Any] | None = None) -> dict[str, Any]:
    task_view = _dict(task)
    rt = _dict(runtime_task or task_view.get('runtime_task'))

    target = _text(task_view.get('target') or rt.get('target'))
    objective = _text(task_view.get('objective') or rt.get('objective'))
    task_family = _lower(task_view.get('task_family') or rt.get('task_family') or 'generic') or 'generic'
    capability_candidates = _list_text(task_view.get('capability_candidates') or rt.get('capability_candidates'), lower=True, limit=6)
    recommended_action_types = _list_text(task_view.get('recommended_action_types') or rt.get('recommended_action_types'), lower=True, limit=6)
    action_type = _lower(task_view.get('action_type') or rt.get('action_type') or (recommended_action_types[0] if recommended_action_types else DEFAULT_ACTION_TYPE))
    if not action_type:
        action_type = DEFAULT_ACTION_TYPE
    capability = _lower(task_view.get('capability') or rt.get('capability') or ACTION_TYPE_TO_CAPABILITY.get(action_type) or (capability_candidates[0] if capability_candidates else DEFAULT_CAPABILITY))
    if not capability:
        capability = DEFAULT_CAPABILITY
    experiment_shape = _lower(task_view.get('experiment_shape') or rt.get('experiment_shape') or ACTION_TYPE_TO_EXPERIMENT_SHAPE.get(action_type) or 'single_step')

    success_semantics = _dict(task_view.get('success_semantics') or rt.get('success_semantics'))
    evidence_goal = _text(task_view.get('evidence_goal') or rt.get('evidence_goal') or success_semantics.get('evidence_goal_type'))
    planner_constraints = _dict(task_view.get('planner_constraints') or rt.get('planner_constraints'))
    planner_preferences = _dict(task_view.get('planner_preferences') or rt.get('planner_preferences'))
    planner_rationale = _dict(task_view.get('planner_rationale') or rt.get('planner_rationale'))
    field_ownership = _dict(task_view.get('planner_field_ownership') or rt.get('planner_field_ownership'))

    normalized = {
        'schema_version': RUNTIME_TASK_SCHEMA_VERSION,
        'target': target,
        'objective': objective,
        'task_family': task_family,
        'task_success_criteria': _text(task_view.get('task_success_criteria') or task_view.get('success_criteria') or rt.get('task_success_criteria')),
        'campaign_success_criteria': _text(task_view.get('campaign_success_criteria') or rt.get('campaign_success_criteria')),
        'priority_score': float(task_view.get('priority_score') or rt.get('priority_score') or 1.0),
        'cost_band': _lower(task_view.get('cost_band') or rt.get('cost_band') or 'medium'),
        'priority_tier': _enum(task_view.get('priority_tier') or rt.get('priority_tier') or 'medium', allowed={'high', 'medium', 'low'}, default='medium'),
        'expected_depth': _enum(task_view.get('expected_depth') or rt.get('expected_depth') or 'medium', allowed={'deep', 'medium', 'light'}, default='medium'),
        'activation_phase': _activation_phase(task_view.get('activation_phase') or rt.get('activation_phase') or 1),
        'activation_mode': _enum(task_view.get('activation_mode') or rt.get('activation_mode') or 'immediate', allowed={'immediate', 'if_signal', 'if_confirmed', 'background'}, default='immediate'),
        'conditional_gate': _text(task_view.get('conditional_gate') or rt.get('conditional_gate')),
        'surface_role': _enum(task_view.get('surface_role') or rt.get('surface_role') or 'primary', allowed={'primary', 'supporting', 'background'}, default='primary'),
        'target_cluster': _lower(task_view.get('target_cluster') or rt.get('target_cluster') or 'general') or 'general',
        'acceptance_checks': _list_text(task_view.get('acceptance_checks') or rt.get('acceptance_checks'), lower=False, limit=12),
        'evidence_required': _list_text(task_view.get('evidence_required') or rt.get('evidence_required'), lower=False, limit=12),
        'success_semantics': success_semantics,
        'evidence_goal': evidence_goal,
        'capability_candidates': capability_candidates,
        'recommended_action_types': recommended_action_types,
        'hypothesis_candidates': _list_text(task_view.get('hypothesis_candidates') or rt.get('hypothesis_candidates'), lower=True, limit=8),
        'open_questions': _list_text(task_view.get('open_questions') or rt.get('open_questions'), lower=False, limit=8),
        'recommended_tools': _list_text(task_view.get('recommended_tools') or rt.get('recommended_tools'), lower=False, limit=8),
        'experiment_intent_id': _text(task_view.get('experiment_intent_id') or rt.get('experiment_intent_id')),
        'planner_constraints': planner_constraints,
        'planner_preferences': planner_preferences,
        'planner_input_source': _text(task_view.get('planner_input_source') or rt.get('planner_input_source')),
        'planner_field_ownership': field_ownership,
        'planner_rationale': planner_rationale,
        'action_type': action_type,
        'capability': capability,
        'experiment_shape': experiment_shape,
    }
    normalized['exploit_ladder'] = _normalize_exploit_ladder(task_view.get('exploit_ladder') or rt.get('exploit_ladder'), task_family=task_family, action_type=action_type, experiment_shape=experiment_shape)
    normalized['actor_requirements'] = _normalize_actor_requirements(task_view.get('actor_requirements') or rt.get('actor_requirements'), task_family)
    normalized['session_requirements'] = _normalize_session_requirements(task_view.get('session_requirements') or rt.get('session_requirements'), task_family, experiment_shape)
    normalized['promotion_policy'] = _normalize_promotion_policy(task_view.get('promotion_policy') or rt.get('promotion_policy'), task_family)
    normalized['contamination_policy'] = _normalize_contamination_policy(task_view.get('contamination_policy') or rt.get('contamination_policy'))
    normalized['approval_sensitivity'] = _normalize_approval_sensitivity(task_view.get('approval_sensitivity') or rt.get('approval_sensitivity'), planner_constraints, task_family)
    return normalized
