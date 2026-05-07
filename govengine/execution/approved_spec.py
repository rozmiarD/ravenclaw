from __future__ import annotations

from typing import Any, Dict, List


def validate_approved_execution_spec(approved_execution_spec: Dict[str, Any]) -> Dict[str, Any]:
    """Validate the approved-spec envelope and return execution_truth.

    This helper is pure: it does not touch tools, paths, subprocesses, or scope.
    """

    if not isinstance(approved_execution_spec, dict):
        raise ValueError('invalid_approved_execution_spec')
    spec_version = str(approved_execution_spec.get('spec_version') or '').strip()
    if spec_version != '2026-03-18.approved.v1':
        raise ValueError(f'invalid_approved_execution_spec_version:{spec_version or "missing"}')
    approval = approved_execution_spec.get('approval') if isinstance(approved_execution_spec.get('approval'), dict) else {}
    decision = str(approval.get('decision') or '').strip().lower()
    if decision != 'approve':
        raise ValueError(f'invalid_approved_execution_decision:{decision or "missing"}')
    execution_truth = approved_execution_spec.get('execution_truth') if isinstance(approved_execution_spec.get('execution_truth'), dict) else {}
    artifact_type = str(execution_truth.get('artifact_type') or '').strip()
    if artifact_type != 'approved_execution_spec':
        raise ValueError(f'invalid_approved_execution_truth_artifact:{artifact_type or "missing"}')
    return execution_truth


def approved_execution_steps(approved_execution_spec: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return normalized execution steps from an approved execution spec."""

    execution_truth = validate_approved_execution_spec(approved_execution_spec)
    execution_plan = execution_truth.get('execution_plan') if isinstance(execution_truth, dict) else approved_execution_spec.get('execution_plan')
    if not isinstance(execution_plan, list) or not execution_plan:
        raise ValueError('missing_execution_plan')
    out: List[Dict[str, Any]] = []
    for step in execution_plan:
        if not isinstance(step, dict):
            continue
        normalized_step = {'tool': str(step.get('tool') or ''), 'args': list(step.get('args') or [])}
        if step.get('stdin'):
            normalized_step['stdin'] = str(step.get('stdin') or '')
        out.append(normalized_step)
    if not out:
        raise ValueError('missing_execution_plan')
    return out
