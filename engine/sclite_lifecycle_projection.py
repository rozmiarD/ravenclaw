"""Ravenclaw-owned mapping from runtime output to the current SCLite lifecycle."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Mapping

from sclite.integrity import artifact_descriptor, build_artifact_chain_manifest
from sclite.redaction import sanitize_public_artifact
from sclite.tickets import normalized_args_digest, validate_ticket_semantics, verify_ticket_use


CURRENT_LIFECYCLE_TRACE_FILES = [
    'intent_contract.json',
    'policy_decision.v0.2.json',
    'execution_contract.json',
    'execution_ticket.json',
    'execution_receipt.v0.2.json',
    'evidence_contract.json',
    'artifact_chain_manifest.json',
]


def _dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _created_at(pipeline_data: Mapping[str, Any]) -> str:
    for key in ('generated_at', 'created_at', 'timestamp'):
        raw = pipeline_data.get(key)
        if raw:
            return str(raw)
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _link(role: str, artifact: Mapping[str, Any]) -> Dict[str, Any]:
    return {'role': role, 'descriptor': artifact_descriptor(dict(artifact))}


def _prepared(pipeline_data: Mapping[str, Any]) -> Dict[str, Any]:
    return _dict(pipeline_data.get('prepared_execution_spec'))


def _approved(pipeline_data: Mapping[str, Any]) -> Dict[str, Any]:
    return _dict(pipeline_data.get('approved_execution_spec'))


def _policy_decision(pipeline_data: Dict[str, Any]) -> Dict[str, Any]:
    prepared = _prepared(pipeline_data)
    auditor = _dict(pipeline_data.get('auditor'))
    policy_gate = _dict(pipeline_data.get('policy_gate'))
    passed = bool(policy_gate.get('pass', False))
    reason = str(policy_gate.get('reason') or '').strip() or ('ok' if passed else 'unspecified')
    owner_gate = bool(auditor.get('owner_gate', False)) or reason.startswith('action_type_requires_owner_gate')
    decision = 'allow_prepare' if passed else ('owner_approval_required' if owner_gate else 'deny')
    return {
        'decision': decision,
        'reason_code': reason,
        'reason': reason,
    }


def build_intent_contract(pipeline_data: Dict[str, Any]) -> Dict[str, Any]:
    prepared = _prepared(pipeline_data)
    settings = _dict(pipeline_data.get('settings'))
    return sanitize_public_artifact({
        'artifact_type': 'intent_contract',
        'schema_version': 'v0.2',
        'schema_ref': 'schemas/intent_contract.v0.2.schema.json',
        'intent_id': str(pipeline_data.get('run_id') or pipeline_data.get('task_id') or 'ravenclaw-intent'),
        'created_at': _created_at(pipeline_data),
        'actor': {'kind': 'runtime', 'label': 'ravenclaw', 'carrier': 'ravenclaw'},
        'intent': {
            'summary': str(pipeline_data.get('intent_summary') or prepared.get('action_type') or 'ravenclaw_governed_action'),
            'category': str(prepared.get('action_type') or 'unknown'),
        },
        'requested_capability': {
            'name': str(prepared.get('resolved_tool') or prepared.get('capability') or ''),
            'mode': str(settings.get('runtime_mode') or ''),
        },
        'target': {
            'uri': str(prepared.get('target') or ''),
            'host': str(prepared.get('target_host') or ''),
        },
        'constraints': ['ravenclaw_policy_gate_required', 'execution_ticket_required'],
        'authority': {
            'intent_is_authority': False,
            'requires_policy_decision': True,
            'requires_execution_ticket': True,
        },
        'non_claims': [
            'intent_does_not_authorize_execution',
            'sclite_does_not_prove_legal_authorization',
        ],
    })


def build_policy_decision(pipeline_data: Dict[str, Any], intent_contract: Mapping[str, Any]) -> Dict[str, Any]:
    decision = _policy_decision(pipeline_data)
    prepared = _prepared(pipeline_data)
    return sanitize_public_artifact({
        'artifact_type': 'policy_decision',
        'schema_version': 'v0.2',
        'schema_ref': 'schemas/policy_decision.v0.2.schema.json',
        'decision_id': str(decision.get('decision_id') or pipeline_data.get('run_id') or 'ravenclaw-policy-decision'),
        'created_at': _created_at(pipeline_data),
        'decision': str(decision.get('decision') or 'deny'),
        'links': {'intent': _link('intent_contract', intent_contract)},
        'scope': {
            'target_in_scope': bool(prepared.get('target_in_scope', False)),
            'target_host': str(prepared.get('target_host') or ''),
            'scope_facts': _dict(prepared.get('scope_facts')),
        },
        'capability': {
            'name': str(prepared.get('resolved_tool') or ''),
            'action_type': str(prepared.get('action_type') or ''),
        },
        'risk': {'level': str(_dict(pipeline_data.get('auditor')).get('risk') or 'runtime_defined')},
        'constraints': [str(item) for item in _dict(_dict(pipeline_data.get('auditor')).get('constraints')).keys()],
        'reason_codes': [str(decision.get('reason_code') or decision.get('reason') or '')],
    })


def _execution_mode(pipeline_data: Mapping[str, Any]) -> str:
    settings = _dict(pipeline_data.get('settings'))
    engine = _dict(pipeline_data.get('engine'))
    runtime_mode = str(settings.get('runtime_mode') or '').lower()
    if (
        bool(settings.get('forced_dry_run'))
        or str(engine.get('status') or '').lower() == 'dry-run'
        or runtime_mode in {'demo', 'dry_run', 'dry-run'}
    ):
        return 'dry_run'
    return 'live'


def _approval_status(approval: Mapping[str, Any]) -> str:
    decision = str(approval.get('decision') or approval.get('status') or '').lower()
    if decision in {'approve', 'approved', 'allow', 'allowed'}:
        return 'approved_for_dry_run'
    if decision in {'owner_approval_required', 'review', 'needs_review'}:
        return 'owner_approval_required'
    if decision in {'reject', 'rejected', 'deny', 'denied'}:
        return 'rejected'
    if decision in {'expired', 'revoked'}:
        return decision
    return 'owner_approval_required'


def build_execution_contract(
    pipeline_data: Dict[str, Any],
    intent_contract: Mapping[str, Any],
    policy_decision: Mapping[str, Any],
) -> Dict[str, Any]:
    prepared = _prepared(pipeline_data)
    approved = _approved(pipeline_data)
    truth = _dict(approved.get('execution_truth'))
    plan = _list(truth.get('execution_plan') or approved.get('execution_plan') or prepared.get('execution_plan'))
    return sanitize_public_artifact({
        'artifact_type': 'execution_contract',
        'schema_version': 'v0.2',
        'schema_ref': 'schemas/execution_contract.v0.2.schema.json',
        'contract_id': str(approved.get('contract_id') or pipeline_data.get('run_id') or 'ravenclaw-execution-contract'),
        'created_at': _created_at(pipeline_data),
        'links': {
            'intent': _link('intent_contract', intent_contract),
            'policy_decision': _link('policy_decision', policy_decision),
        },
        'target_binding': {
            'target': str(approved.get('target') or prepared.get('target') or ''),
            'target_host': str(approved.get('target_host') or prepared.get('target_host') or ''),
            'target_in_scope': bool(approved.get('target_in_scope', prepared.get('target_in_scope', False))),
        },
        'execution_shape': {
            'tool': str(approved.get('resolved_tool') or prepared.get('resolved_tool') or ''),
            'normalized_args': _list(approved.get('normalized_args') or prepared.get('normalized_args')),
            'plan': plan,
        },
        'execution_bounds': {
            'mode': _execution_mode(pipeline_data),
            'dry_run': _execution_mode(pipeline_data) == 'dry_run',
            'max_commands': len(plan),
        },
        'expected_receipt': {'schema_ref': 'schemas/execution_receipt.v0.2.schema.json', 'required': True},
        'non_claims': [
            'execution_contract_is_not_runtime_execution',
            'execution_contract_requires_ticket_before_use',
        ],
    })


def build_execution_ticket(
    pipeline_data: Dict[str, Any],
    policy_decision: Mapping[str, Any],
    execution_contract: Mapping[str, Any],
) -> Dict[str, Any]:
    approved = _approved(pipeline_data)
    prepared = _prepared(pipeline_data)
    approval = _dict(approved.get('approval'))
    shape = _dict(execution_contract.get('execution_shape'))
    target_binding = _dict(execution_contract.get('target_binding'))
    mode = _execution_mode(pipeline_data)
    target_host = str(target_binding.get('target_host') or prepared.get('target_host') or '')
    runtime_name = str(pipeline_data.get('runtime_name') or 'ravenclaw')
    ticket = sanitize_public_artifact({
        'artifact_type': 'execution_ticket',
        'schema_version': 'v0.3',
        'schema_ref': 'schemas/execution_ticket.v0.3.schema.json',
        'ticket_id': str(approval.get('approval_id') or pipeline_data.get('run_id') or 'ravenclaw-scoped-ticket'),
        'created_at': _created_at(pipeline_data),
        'ticket_profile': 'scoped_execution_ticket',
        'ticket_semantics': {
            'kind': 'runtime_consumable_scoped_ticket',
            'consumable_by_runtime': True,
            'default_transferable': False,
        },
        'links': {
            'policy_decision': _link('policy_decision', policy_decision),
            'execution_contract': _link('execution_contract', execution_contract),
        },
        'approval': {
            'status': _approval_status(approval),
            'approval_id': str(approval.get('approval_id') or pipeline_data.get('run_id') or 'ravenclaw-approval'),
            'approver_kind': str(approval.get('approval_source') or 'ravenclaw_auditor'),
        },
        'validity': {
            'not_before': _created_at(pipeline_data),
            'not_after': str(approval.get('expires_at') or _created_at(pipeline_data)),
        },
        'execution_limits': {'one_shot': True, 'max_runs': 1, 'mode': mode},
        'subject_binding': {
            'issued_for_actor': 'runtime:ravenclaw',
            'usable_by_runtime': f'runtime:{runtime_name}',
            'session_ref': f"session:{str(pipeline_data.get('run_id') or 'public-safe')}",
        },
        'scope_binding': {
            'target_kind': 'host',
            'target_ref': f'host:{target_host}',
            'target_host': target_host,
            'tool': str(shape.get('tool') or prepared.get('resolved_tool') or ''),
            'mode': mode,
            'normalized_args_digest': normalized_args_digest(_list(shape.get('normalized_args'))),
        },
        'spend_limits': {
            'max_uses': 1,
            'one_shot': True,
            'network_execution_allowed': False,
            'requires_receipt': True,
            'requires_evidence_contract': True,
        },
        'integrity': {
            'ticket_binds_execution_contract_digest': artifact_descriptor(execution_contract)['digest'],
            'profile': 'sclite-v0.3-scoped-ticket-integrity',
        },
        'signature': {
            'mode': 'not_signed_integrity_only',
            'identity_signature_required': False,
            'note': 'SCLite validates scoped-ticket bounds; signer trust remains a host/profile decision.',
        },
        'non_claims': [
            'ticket_does_not_prove_real_world_identity',
            'ticket_does_not_prove_legal_authorization',
            'runtime_must_enforce_ticket_bounds',
        ],
    })
    validate_ticket_semantics(ticket, execution_contract)
    return ticket


def build_execution_receipt(
    pipeline_data: Dict[str, Any],
    execution_ticket: Mapping[str, Any],
    execution_contract: Mapping[str, Any],
) -> Dict[str, Any]:
    engine = _dict(pipeline_data.get('engine'))
    mode = _execution_mode(pipeline_data)
    runtime_name = str(pipeline_data.get('runtime_name') or 'ravenclaw')
    raw_status = str(engine.get('status') or '')
    status = 'dry_run' if mode == 'dry_run' and raw_status in {'dry-run', 'dry_run', ''} else raw_status
    return sanitize_public_artifact({
        'artifact_type': 'execution_receipt',
        'schema_version': 'v0.2',
        'schema_ref': 'schemas/execution_receipt.v0.2.schema.json',
        'receipt_id': str(pipeline_data.get('run_id') or 'ravenclaw-execution-receipt'),
        'created_at': _created_at(pipeline_data),
        'links': {
            'execution_ticket': _link('execution_ticket', execution_ticket),
            'execution_contract': _link('execution_contract', execution_contract),
        },
        'runtime': {
            'name': runtime_name,
            'runtime_ref': f'runtime:{runtime_name}',
            'mode': mode,
            'version': str(pipeline_data.get('runtime_version') or ''),
        },
        'execution': {
            'executed_command_count': len(_list(engine.get('executed_commands'))),
            'planned_command_count': len(_list(engine.get('planned_commands'))),
            'network_execution_performed': False if mode == 'dry_run' else bool(engine.get('network_execution_performed')),
            'execution_source': str(engine.get('execution_source') or ''),
        },
        'outcome': {
            'status': status,
            'returncode': int(engine.get('returncode', 0) or 0),
            'reason': str(engine.get('reason') or ''),
            'stdout_present': bool(engine.get('stdout')),
            'stderr_present': bool(engine.get('stderr')),
        },
        'ticket_use': {
            'ticket_id': str(execution_ticket.get('ticket_id') or ''),
            'consumed_by_runtime': f'runtime:{runtime_name}',
            'use_count': 1,
            'one_shot_consumed': True,
        },
        'evidence_refs': [{'kind': 'evidence_contract', 'path': 'evidence_contract.json'}],
        'non_claims': [
            'receipt_does_not_include_raw_logs',
            'receipt_does_not_prove_live_vulnerability_evidence',
        ],
    })


def build_evidence_contract(
    pipeline_data: Dict[str, Any],
    execution_receipt: Mapping[str, Any],
    execution_ticket: Mapping[str, Any],
) -> Dict[str, Any]:
    return sanitize_public_artifact({
        'artifact_type': 'evidence_contract',
        'schema_version': 'v0.2',
        'schema_ref': 'schemas/evidence_contract.v0.2.schema.json',
        'evidence_contract_id': str(pipeline_data.get('run_id') or 'ravenclaw-evidence-contract'),
        'created_at': _created_at(pipeline_data),
        'links': {
            'execution_receipt': _link('execution_receipt', execution_receipt),
            'execution_ticket': _link('execution_ticket', execution_ticket),
        },
        'claims': [{
            'id': 'ravenclaw_lifecycle_chain_present',
            'statement': 'Ravenclaw emitted a public-safe SCLite lifecycle chain for this run.',
            'status': 'met',
            'claim_type': 'receipt_bounded_dry_run',
            'bounded_by_receipt': True,
            'requires_live_execution': False,
            'source_receipt_id': str(execution_receipt.get('receipt_id') or ''),
        }],
        'non_claims': [
            'does_not_claim_live_vulnerability_evidence',
            'does_not_include_private_runtime_logs',
            'does_not_prove_legal_authorization',
        ],
        'verification': {'commands': ['sclite validate-chain artifact_chain_manifest.json']},
        'replay': {'mode': 'static_bundle_verification', 'live_execution_required': False},
    })


def build_current_lifecycle_artifacts(pipeline_data: Dict[str, Any]) -> Dict[str, Any]:
    intent = build_intent_contract(pipeline_data)
    policy = build_policy_decision(pipeline_data, intent)
    contract = build_execution_contract(pipeline_data, intent, policy)
    ticket = build_execution_ticket(pipeline_data, policy, contract)
    receipt = build_execution_receipt(pipeline_data, ticket, contract)
    evidence = build_evidence_contract(pipeline_data, receipt, ticket)
    verify_ticket_use(ticket, contract, receipt, evidence)
    artifacts = {
        'intent_contract.json': intent,
        'policy_decision.v0.2.json': policy,
        'execution_contract.json': contract,
        'execution_ticket.json': ticket,
        'execution_receipt.v0.2.json': receipt,
        'evidence_contract.json': evidence,
    }
    artifacts['artifact_chain_manifest.json'] = build_artifact_chain_manifest([
        {'role': 'intent_contract', 'path': 'intent_contract.json', 'value': intent},
        {'role': 'policy_decision', 'path': 'policy_decision.v0.2.json', 'value': policy},
        {'role': 'execution_contract', 'path': 'execution_contract.json', 'value': contract},
        {'role': 'execution_ticket', 'path': 'execution_ticket.json', 'value': ticket},
        {'role': 'execution_receipt', 'path': 'execution_receipt.v0.2.json', 'value': receipt},
        {'role': 'evidence_contract', 'path': 'evidence_contract.json', 'value': evidence},
    ], chain_id=str(pipeline_data.get('run_id') or 'ravenclaw-sclite-current-lifecycle'), created_at=_created_at(pipeline_data))
    return artifacts
