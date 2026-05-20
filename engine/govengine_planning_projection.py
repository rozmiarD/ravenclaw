from __future__ import annotations

from hashlib import sha256
from typing import Any, Mapping

from govengine.planning import task_contract_from_host_task, validate_plan_intent_contract, validate_planner_port

from runtime_task_schema import normalize_runtime_task_v2  # type: ignore


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: Any, default: str = '') -> str:
    out = str(value if value is not None else '').strip()
    return out if out else default


def _target_ref(value: Any) -> tuple[str, bool]:
    text = _text(value)
    if not text:
        return '', False
    return 'sha256:' + sha256(text.encode('utf-8')).hexdigest()[:24], True


def build_gov_task_contract_projection(
    task: Mapping[str, Any] | None = None,
    runtime_task: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Project Ravenclaw runtime-task semantics into GovEngine 0.4 shape.

    Ravenclaw keeps the security-domain contract. GovEngine receives only a
    neutral, redacted planner-to-runtime handoff shape.
    """

    task_view = _mapping(task)
    runtime_view = _mapping(runtime_task or task_view.get('runtime_task'))
    normalized = normalize_runtime_task_v2(task_view, runtime_view)
    target_ref, redacted = _target_ref(normalized.get('target'))
    contract_id = (
        _text(normalized.get('experiment_intent_id'))
        or _text(task_view.get('intent_id'))
        or _text(task_view.get('task_id'))
        or f"{target_ref or 'ravenclaw-task'}:{_text(normalized.get('task_family'), 'generic')}"
    )
    contract = task_contract_from_host_task(
        contract_id=contract_id,
        task_family=_text(normalized.get('task_family'), 'generic'),
        objective=_text(normalized.get('objective')),
        capability=_text(normalized.get('capability')),
        action_type=_text(normalized.get('action_type')),
        target_ref=target_ref,
        target_kind=_text(task_view.get('target_type') or runtime_view.get('target_type'), 'host'),
        evidence_goal=_text(normalized.get('evidence_goal')),
        priority_tier=_text(normalized.get('priority_tier'), 'medium'),
        expected_depth=_text(normalized.get('expected_depth'), 'medium'),
        activation_phase=int(normalized.get('activation_phase') or 1),
        activation_mode=_text(normalized.get('activation_mode'), 'immediate'),
        conditional_gate=_text(normalized.get('conditional_gate')),
        surface_role=_text(normalized.get('surface_role'), 'primary'),
        constraints=_mapping(normalized.get('planner_constraints')),
        preferences=_mapping(normalized.get('planner_preferences')),
        rationale={
            'planner_rationale': _mapping(normalized.get('planner_rationale')),
            'planning_ladder': _mapping(task_view.get('planning_ladder') or runtime_view.get('planning_ladder')),
        },
        metadata={
            'source': 'ravenclaw_planning_projection',
            'target_redacted': redacted,
            'runtime_task_schema_version': normalized.get('schema_version'),
        },
    )
    return contract.as_dict()


def build_gov_plan_intent_projection(intent: Mapping[str, Any]) -> dict[str, Any]:
    source = _mapping(intent)
    task_contract = build_gov_task_contract_projection(source, _mapping(source.get('runtime_task_contract')))
    plan = validate_plan_intent_contract({
        'intent_id': _text(source.get('intent_id') or task_contract.get('contract_id'), 'ravenclaw-plan-intent'),
        'profile': 'ravenclaw-security',
        'planner_id': _text(source.get('planner_id'), 'ravenclaw-planner'),
        'goal': _text(source.get('objective')),
        'task_contracts': [task_contract],
        'non_claims': [
            'ravenclaw_owns_security_planning_semantics',
            'does_not_expose_raw_target_to_govengine',
            'does_not_grant_execution_authority',
        ],
        'metadata': {'source': 'ravenclaw_planning_projection'},
    })
    return plan.as_dict()


def ravenclaw_planner_port_projection() -> dict[str, Any]:
    return validate_planner_port({
        'name': 'ravenclaw-planner',
        'profile': 'ravenclaw-security',
        'supported_contracts': ['gov_task_contract', 'gov_plan_intent_contract'],
        'metadata': {'source': 'ravenclaw_planning_projection'},
    }).as_dict()
