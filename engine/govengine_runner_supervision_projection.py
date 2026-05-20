from __future__ import annotations

from typing import Any, Mapping

from govengine.execution.runner_protocol import dry_run_runner_receipt, runner_request_from_approved_spec
from govengine.execution.supervision import (
    runner_lease_from_request,
    supervision_plan_from_runner_request,
    validate_runner_receipt_for_request,
    validate_supervised_runner_request,
)


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def build_gov_runner_supervision_projection(
    approved_execution_spec: Mapping[str, Any],
    *,
    request_id: str = 'ravenclaw-approved-spec-request',
    execution_ticket_gate: Mapping[str, Any] | None = None,
    dry_run: bool = True,
    timeout_seconds: int = 30,
) -> dict[str, Any]:
    """Project a Ravenclaw approved-spec runner boundary into GovEngine 0.6."""

    request = runner_request_from_approved_spec(
        approved_execution_spec,
        request_id=request_id,
        execution_ticket_gate=_mapping(execution_ticket_gate) or {'status': 'not_required'},
        dry_run=dry_run,
    )
    plan = supervision_plan_from_runner_request(
        request,
        runner_profile='dry-run' if dry_run else 'ravenclaw-host',
        live_backend_enabled=False,
        timeout_seconds=timeout_seconds,
        cwd_policy='none',
        env_policy='empty',
        stdin_policy='bounded',
        metadata={'source': 'ravenclaw_runner_supervision_projection'},
    )
    validate_supervised_runner_request(request, plan)
    lease = runner_lease_from_request(
        request,
        runner_profile=plan.runner_profile,
        metadata={'source': 'ravenclaw_runner_supervision_projection'},
    )
    receipt = dry_run_runner_receipt(request)
    validate_runner_receipt_for_request(request, receipt)
    return {
        'artifact_type': 'ravenclaw_govengine_runner_supervision_projection',
        'profile': 'ravenclaw-security',
        'runner_request': request.as_dict(),
        'supervision_plan': plan.as_dict(),
        'runner_lease': lease.as_dict(),
        'runner_receipt': receipt.as_dict(),
        'non_claims': [
            'ravenclaw_owns_concrete_tool_adapters',
            'does_not_execute_from_raw_intent',
            'does_not_enable_live_backend_by_default',
        ],
    }


def validate_existing_runner_receipt_projection(
    approved_execution_spec: Mapping[str, Any],
    runner_receipt: Mapping[str, Any],
    *,
    request_id: str = 'ravenclaw-approved-spec-request',
    execution_ticket_gate: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    request = runner_request_from_approved_spec(
        approved_execution_spec,
        request_id=request_id,
        execution_ticket_gate=_mapping(execution_ticket_gate) or {'status': 'not_required'},
        dry_run=True,
    )
    receipt = validate_runner_receipt_for_request(request, runner_receipt)
    return receipt.as_dict()
