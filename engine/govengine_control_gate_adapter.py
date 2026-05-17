from __future__ import annotations

from typing import Any, Dict, List, Mapping

from govengine.core import ArtifactState
from govengine.execution.gate import ExecutionGate, ExecutionGateInput, RunnerProfile
from govengine.sclite_contracts import descriptor_from_artifact
from govengine.signing import DemoDigestVerifier, SigningPolicy, TrustPolicy, signature_envelope_from_artifact, signature_transition_decision
from govengine.state_index import ArtifactStateIndex


def _dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list(value: Any) -> List[Any]:
    return list(value) if isinstance(value, list) else []


def _not_required() -> Dict[str, Any]:
    return {
        'status': 'not_required',
        'reason_code': 'execution_ticket_not_required',
        'available': False,
    }


def evaluate_govengine_control_gate(
    *,
    dry_run: bool,
    require_execution_ticket: bool,
    execution_ticket_gate: Mapping[str, Any] | None,
    execution_ticket: Mapping[str, Any] | None,
    execution_contract: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    """Evaluate optional GovEngine artifact-governance execution gates.

    This is a Ravenclaw host adapter seam. It consumes published GovEngine
    artifact-governance gate objects while Ravenclaw supplies host artifacts,
    runner-profile selection, and dry-run/live context.
    """

    if not require_execution_ticket:
        return _not_required()

    ticket_gate = _dict(execution_ticket_gate)
    ticket = _dict(execution_ticket)
    contract = _dict(execution_contract)
    artifact_states: List[ArtifactState] = []

    if contract:
        contract_descriptor = descriptor_from_artifact(contract, role='execution_contract')
        artifact_states.append(ArtifactState(
            descriptor=contract_descriptor,
            lifecycle_state='prepared',
            chain_status='not_checked',
            signature_status='not_required',
            policy_status='passed' if ticket_gate.get('status') == 'passed' else 'unknown',
        ))
    if ticket:
        ticket_descriptor = descriptor_from_artifact(ticket, role='execution_ticket')
        signature = signature_envelope_from_artifact(ticket)
        verification = None
        require_signature = False
        allowed_modes = ('not_signed_integrity_only', 'detached_signature', 'detached_demo_digest')
        if signature.mode == 'detached_demo_digest':
            contract_descriptor = descriptor_from_artifact(contract, role='execution_contract') if contract else ticket_descriptor
            verification = DemoDigestVerifier(
                verifier_id=str(((ticket.get('trust_decision') or {}) if isinstance(ticket.get('trust_decision'), dict) else {}).get('verifier_id') or 'ravenclaw-demo-verifier'),
                allowed_signer_ids=(str(signature.signer_id),) if signature.signer_id else (),
            ).verify(contract_descriptor, signature)
            require_signature = True
            ticket_descriptor = contract_descriptor
        signature_decision = signature_transition_decision(
            ticket_descriptor,
            signature=signature,
            verification=verification,
            signing_policy=SigningPolicy(require_signature=require_signature, allowed_modes=allowed_modes),
            trust_policy=TrustPolicy(allowed_trust_statuses=('trusted',)) if require_signature else None,
        )
        artifact_states.append(ArtifactState(
            descriptor=ticket_descriptor,
            lifecycle_state='approved',
            chain_status='not_checked',
            signature_status=str(signature.mode or 'not_required'),
            policy_status='passed' if ticket_gate.get('status') == 'passed' else 'unknown',
            blocked_reasons=tuple(signature_decision.blockers),
            next_actions=tuple(signature_decision.next_actions),
        ))
    else:
        signature_decision = None

    state_index = ArtifactStateIndex.from_states(artifact_states)
    profile_name = 'dry-run' if dry_run else 'ravenclaw-host'
    gate_decision = ExecutionGate().evaluate(
        ExecutionGateInput(
            has_prepared_execution_contract=bool(contract),
            policy_decision_status='passed' if ticket_gate.get('status') == 'passed' else 'missing',
            execution_ticket_status=str(ticket_gate.get('status') or 'missing'),
            trust_decision_status='passed' if signature_decision is None or signature_decision.allowed else 'missing',
            runner_profile=RunnerProfile(
                name=profile_name,
                allowed=True,
                live_backend_enabled=not dry_run,
                metadata={'host': 'ravenclaw'},
            ),
        ),
        live=not dry_run,
    )

    return {
        'status': gate_decision.status,
        'available': True,
        'allowed': gate_decision.allowed,
        'reason_code': gate_decision.reason_code,
        'runner_profile': profile_name,
        'blockers': list(gate_decision.blockers),
        'next_actions': list(gate_decision.next_actions),
        'signature_gate': signature_decision.as_dict() if signature_decision is not None else {'status': 'not_required'},
        'state_index': state_index.summary(required_roles=('execution_contract', 'execution_ticket')),
    }
