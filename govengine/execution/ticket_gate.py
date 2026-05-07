from __future__ import annotations

from typing import Any, Dict, List

from sclite.integrity import artifact_descriptor

APPROVED_TICKET_STATUSES = {'approve', 'approved', 'approved_for_dry_run'}


def validate_execution_ticket_gate(
    approved_execution_spec: Dict[str, Any],
    *,
    execution_ticket: Dict[str, Any] | None,
    execution_contract: Dict[str, Any] | None,
    raw_steps: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Validate that an ExecutionTicket authorizes the approved execution shape.

    The approved spec is accepted for signature compatibility with the runtime
    gate, but this pure gate currently validates the ticket, contract digest,
    and command-shape binding only.
    """

    _ = approved_execution_spec
    if not isinstance(execution_ticket, dict):
        raise ValueError('missing_execution_ticket')
    if not isinstance(execution_contract, dict):
        raise ValueError('missing_execution_contract')
    artifact_type = str(execution_ticket.get('artifact_type') or '').strip()
    schema_version = str(execution_ticket.get('schema_version') or '').strip()
    if artifact_type != 'execution_ticket' or schema_version != 'v0.2':
        raise ValueError(f'invalid_execution_ticket:{artifact_type or "missing"}:{schema_version or "missing"}')
    approval = execution_ticket.get('approval') if isinstance(execution_ticket.get('approval'), dict) else {}
    status = str(approval.get('status') or '').strip().lower()
    if status not in APPROVED_TICKET_STATUSES:
        raise ValueError(f'invalid_execution_ticket_approval:{status or "missing"}')
    limits = execution_ticket.get('execution_limits') if isinstance(execution_ticket.get('execution_limits'), dict) else {}
    try:
        max_runs = int(limits.get('max_runs', 0) or 0)
    except (TypeError, ValueError):
        max_runs = 0
    if max_runs < 1:
        raise ValueError('invalid_execution_ticket_max_runs')
    contract_digest = artifact_descriptor(execution_contract)['digest']
    integrity = execution_ticket.get('integrity') if isinstance(execution_ticket.get('integrity'), dict) else {}
    bound_digest = str(integrity.get('ticket_binds_execution_contract_digest') or '').strip()
    if bound_digest != contract_digest:
        raise ValueError('execution_ticket_contract_digest_mismatch')
    shape = execution_contract.get('execution_shape') if isinstance(execution_contract.get('execution_shape'), dict) else {}
    contract_plan = shape.get('plan') if isinstance(shape.get('plan'), list) else []
    if len(contract_plan) != len(raw_steps):
        raise ValueError('execution_ticket_plan_length_mismatch')
    for idx, (contract_step, approved_step) in enumerate(zip(contract_plan, raw_steps), 1):
        if not isinstance(contract_step, dict):
            raise ValueError(f'execution_ticket_invalid_contract_step:{idx}')
        if str(contract_step.get('tool') or '') != str(approved_step.get('tool') or ''):
            raise ValueError(f'execution_ticket_tool_mismatch:{idx}')
        if [str(item) for item in list(contract_step.get('args') or [])] != [str(item) for item in list(approved_step.get('args') or [])]:
            raise ValueError(f'execution_ticket_args_mismatch:{idx}')
    return {
        'status': 'passed',
        'ticket_id': str(execution_ticket.get('ticket_id') or ''),
        'execution_contract_digest': contract_digest,
        'profile': str(integrity.get('profile') or ''),
    }
