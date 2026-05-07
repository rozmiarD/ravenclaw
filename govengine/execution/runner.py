from __future__ import annotations

from typing import Any, Dict, List, Mapping


def approved_spec_compiled_action(approved_execution_spec: Mapping[str, Any]) -> Dict[str, Any]:
    """Build the compact compiled-action summary for approved-spec execution."""

    compiler = approved_execution_spec.get('compiler') if isinstance(approved_execution_spec.get('compiler'), dict) else {}
    return {
        'action_type': str(approved_execution_spec.get('action_type') or ''),
        'capability': str(approved_execution_spec.get('capability') or ''),
        'compiler_tool_choice': str(approved_execution_spec.get('resolved_tool') or ''),
        'compiler_tool_choice_source': 'approved_execution_spec',
        'execution_mode': str(approved_execution_spec.get('execution_mode') or ''),
        'semantic_loss_policy': dict(compiler.get('semantic_loss_policy') or {}),
    }


def dry_run_result(
    *,
    compiled_action: Mapping[str, Any],
    planned_commands: List[List[str]],
    execution_source: str,
    execution_ticket_gate: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Assemble the standard dry-run execution result without running commands."""

    result: Dict[str, Any] = {
        'status': 'dry-run',
        'returncode': 0,
        'stdout': '',
        'stderr': '',
        'reason': 'dry_run_requested',
        'compiled_action': dict(compiled_action),
        'planned_commands': planned_commands,
        'execution_source': str(execution_source or ''),
    }
    if execution_ticket_gate is not None:
        result['execution_ticket_gate'] = dict(execution_ticket_gate)
    return result


def approved_spec_dry_run_result(
    *,
    approved_execution_spec: Mapping[str, Any],
    planned_commands: List[List[str]],
    execution_ticket_gate: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Assemble a dry-run result for approved execution specs."""

    return dry_run_result(
        compiled_action=approved_spec_compiled_action(approved_execution_spec),
        planned_commands=planned_commands,
        execution_source='approved_execution_spec',
        execution_ticket_gate=execution_ticket_gate or {'status': 'not_required'},
    )


def legacy_action_spec_dry_run_result(*, compiled_action: Mapping[str, Any], planned_commands: List[List[str]]) -> Dict[str, Any]:
    """Assemble a dry-run result for legacy direct action specs."""

    return dry_run_result(
        compiled_action=compiled_action,
        planned_commands=planned_commands,
        execution_source='legacy_direct_action_spec',
    )
