from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Mapping

from execution_contracts import redact_prepared_execution_spec_for_auditor  # type: ignore
from policy_gateway import normalize_policy_decision_v0  # type: ignore
from sclite.artifacts import (
    PREPARED_EXECUTION_SPEC_VERSION,
    REDACTED_PREPARED_EXECUTION_SPEC_ARTIFACT_TYPE,
    build_proof_trace_artifacts as build_scl_proof_trace_artifacts,
)
from sclite.integrity import artifact_descriptor, build_artifact_chain_manifest
from sclite.redaction import sanitize_public_artifact

LIFECYCLE_TRACE_FILES_V02 = [
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


def build_policy_decision_artifact(pipeline_data: Dict[str, Any]) -> Dict[str, Any]:
    """Map Ravenclaw pipeline policy/auditor output to an SCL PolicyDecision artifact."""
    prepared = _prepared(pipeline_data)
    auditor = _dict(pipeline_data.get('auditor'))
    return normalize_policy_decision_v0(
        _dict(pipeline_data.get('policy_gate')),
        target=str(prepared.get('target') or ''),
        target_host=str(prepared.get('target_host') or ''),
        target_in_scope=bool(prepared.get('target_in_scope', False)),
        resolved_tool=str(prepared.get('resolved_tool') or ''),
        action_type=str(prepared.get('action_type') or ''),
        approval_required=bool(auditor.get('owner_gate', False)),
        constraints=_dict(auditor.get('constraints')),
        redaction_required=True,
    )


def redact_prepared_execution_spec(pipeline_data: Dict[str, Any]) -> Dict[str, Any]:
    """Map Ravenclaw's prepared-spec redaction into SCLite's v0.1 public artifact shape."""
    prepared = _prepared(pipeline_data)
    redacted = redact_prepared_execution_spec_for_auditor(prepared)
    safe = sanitize_public_artifact(redacted if isinstance(redacted, dict) else {})
    safe['artifact_type'] = REDACTED_PREPARED_EXECUTION_SPEC_ARTIFACT_TYPE
    safe['spec_version'] = str(safe.get('spec_version') or prepared.get('spec_version') or PREPARED_EXECUTION_SPEC_VERSION)
    safe['target'] = str(safe.get('target') or prepared.get('target') or '')
    safe['target_host'] = str(safe.get('target_host') or prepared.get('target_host') or '')
    safe['target_in_scope'] = bool(safe.get('target_in_scope', prepared.get('target_in_scope', False)))
    safe['resolved_tool'] = str(safe.get('resolved_tool') or prepared.get('resolved_tool') or '')
    safe['normalized_args'] = _list(safe.get('normalized_args') or prepared.get('normalized_args'))
    safe['execution_plan'] = _list(safe.get('execution_plan') or prepared.get('execution_plan'))
    safe['scope_facts'] = _dict(safe.get('scope_facts') or prepared.get('scope_facts') or {
        'target': safe['target'],
        'target_host': safe['target_host'],
        'target_in_scope': safe['target_in_scope'],
    })
    safe['redaction'] = {
        'status': 'redacted',
        'raw_stdout_stderr_included': False,
        'credentials_included': False,
        'private_paths_included': False,
        'notes': ['ravenclaw_adapter_redacted_prepared_spec'],
    }
    safe['public_safety'] = {
        'live_target_execution': False,
        'raw_live_evidence_included': False,
        'raw_stdout_stderr_included': False,
        'target_host': safe['target_host'],
        'fixture': False,
    }
    return safe


def build_proof_trace_artifacts(pipeline_data: Dict[str, Any]) -> Dict[str, Any]:
    """Build legacy SCL v0.1 proof artifacts from Ravenclaw runtime output."""
    return build_scl_proof_trace_artifacts(
        pipeline_data,
        policy_decision_artifact=build_policy_decision_artifact(pipeline_data),
        redacted_prepared_execution_spec=redact_prepared_execution_spec(pipeline_data),
    )


def build_intent_contract_v02(pipeline_data: Dict[str, Any]) -> Dict[str, Any]:
    prepared = _prepared(pipeline_data)
    settings = _dict(pipeline_data.get('settings'))
    target = str(prepared.get('target') or '')
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
        'target': {'uri': target, 'host': str(prepared.get('target_host') or '')},
        'constraints': ['ravenclaw_policy_gate_required', 'execution_ticket_required'],
        'authority': {'intent_is_authority': False, 'requires_policy_decision': True, 'requires_execution_ticket': True},
        'non_claims': ['intent_does_not_authorize_execution', 'sclite_does_not_prove_legal_authorization'],
    })


def build_policy_decision_artifact_v02(pipeline_data: Dict[str, Any], intent_contract: Mapping[str, Any]) -> Dict[str, Any]:
    v01 = build_policy_decision_artifact(pipeline_data)
    prepared = _prepared(pipeline_data)
    return sanitize_public_artifact({
        'artifact_type': 'policy_decision',
        'schema_version': 'v0.2',
        'schema_ref': 'schemas/policy_decision.v0.2.schema.json',
        'decision_id': str(v01.get('decision_id') or pipeline_data.get('run_id') or 'ravenclaw-policy-decision'),
        'created_at': _created_at(pipeline_data),
        'decision': str(v01.get('decision') or 'deny'),
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
        'reason_codes': [str(v01.get('reason_code') or v01.get('reason') or '')],
        'legacy_v0_1_descriptor': artifact_descriptor(v01),
    })



def _sclite_execution_mode(pipeline_data: Mapping[str, Any]) -> str:
    settings = _dict(pipeline_data.get('settings'))
    engine = _dict(pipeline_data.get('engine'))
    runtime_mode = str(settings.get('runtime_mode') or '').lower()
    if bool(settings.get('forced_dry_run')) or str(engine.get('status') or '').lower() == 'dry-run' or runtime_mode in {'demo', 'dry_run', 'dry-run'}:
        return 'dry_run'
    return 'live'


def _sclite_approval_status(approval: Mapping[str, Any]) -> str:
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

def build_execution_contract_v02(pipeline_data: Dict[str, Any], intent_contract: Mapping[str, Any], policy_decision: Mapping[str, Any]) -> Dict[str, Any]:
    prepared = _prepared(pipeline_data)
    approved = _approved(pipeline_data)
    truth = _dict(approved.get('execution_truth'))
    return sanitize_public_artifact({
        'artifact_type': 'execution_contract',
        'schema_version': 'v0.2',
        'schema_ref': 'schemas/execution_contract.v0.2.schema.json',
        'contract_id': str(approved.get('contract_id') or pipeline_data.get('run_id') or 'ravenclaw-execution-contract'),
        'created_at': _created_at(pipeline_data),
        'links': {'intent': _link('intent_contract', intent_contract), 'policy_decision': _link('policy_decision', policy_decision)},
        'target_binding': {
            'target': str(approved.get('target') or prepared.get('target') or ''),
            'target_host': str(approved.get('target_host') or prepared.get('target_host') or ''),
            'target_in_scope': bool(approved.get('target_in_scope', prepared.get('target_in_scope', False))),
        },
        'execution_shape': {
            'tool': str(approved.get('resolved_tool') or prepared.get('resolved_tool') or ''),
            'normalized_args': _list(approved.get('normalized_args') or prepared.get('normalized_args')),
            'plan': _list(truth.get('execution_plan') or approved.get('execution_plan') or prepared.get('execution_plan')),
        },
        'execution_bounds': {
            'mode': _sclite_execution_mode(pipeline_data),
            'dry_run': _sclite_execution_mode(pipeline_data) == 'dry_run',
            'max_commands': len(_list(truth.get('execution_plan') or approved.get('execution_plan') or prepared.get('execution_plan'))),
        },
        'expected_receipt': {'schema_ref': 'schemas/execution_receipt.v0.2.schema.json', 'required': True},
        'non_claims': ['execution_contract_is_not_runtime_execution', 'execution_contract_requires_ticket_before_use'],
    })


def build_execution_ticket_v02(pipeline_data: Dict[str, Any], policy_decision: Mapping[str, Any], execution_contract: Mapping[str, Any]) -> Dict[str, Any]:
    approved = _approved(pipeline_data)
    approval = _dict(approved.get('approval'))
    contract_desc = artifact_descriptor(execution_contract)
    return sanitize_public_artifact({
        'artifact_type': 'execution_ticket',
        'schema_version': 'v0.2',
        'schema_ref': 'schemas/execution_ticket.v0.2.schema.json',
        'ticket_id': str(approval.get('approval_id') or pipeline_data.get('run_id') or 'ravenclaw-execution-ticket'),
        'created_at': _created_at(pipeline_data),
        'links': {'policy_decision': _link('policy_decision', policy_decision), 'execution_contract': _link('execution_contract', execution_contract)},
        'approval': {
            'status': _sclite_approval_status(approval),
            'approval_source': str(approval.get('approval_source') or 'ravenclaw_auditor'),
            'reason': str(approval.get('reason') or ''),
        },
        'validity': {'not_before': _created_at(pipeline_data), 'not_after': str(approval.get('expires_at') or _created_at(pipeline_data))},
        'execution_limits': {'one_shot': True, 'max_runs': 1, 'mode': _sclite_execution_mode(pipeline_data)},
        'integrity': {'ticket_binds_execution_contract_digest': contract_desc['digest'], 'profile': 'sclite-v0.2-integrity-only'},
        'signature': {'mode': 'not_signed_integrity_only', 'identity_signature_required': False, 'note': 'Ravenclaw v0.2 adapter uses SCLite hash-linked integrity; signer identity can be added as an optional profile.'},
        'non_claims': ['ticket_does_not_prove_real_world_identity', 'runtime_must_enforce_ticket_bounds'],
    })


def build_execution_receipt_v02(pipeline_data: Dict[str, Any], execution_ticket: Mapping[str, Any], execution_contract: Mapping[str, Any]) -> Dict[str, Any]:
    engine = _dict(pipeline_data.get('engine'))
    return sanitize_public_artifact({
        'artifact_type': 'execution_receipt',
        'schema_version': 'v0.2',
        'schema_ref': 'schemas/execution_receipt.v0.2.schema.json',
        'receipt_id': str(pipeline_data.get('run_id') or 'ravenclaw-execution-receipt'),
        'created_at': _created_at(pipeline_data),
        'links': {'execution_ticket': _link('execution_ticket', execution_ticket), 'execution_contract': _link('execution_contract', execution_contract)},
        'runtime': {'name': 'ravenclaw', 'mode': str(_dict(pipeline_data.get('settings')).get('runtime_mode') or ''), 'version': str(pipeline_data.get('runtime_version') or '')},
        'execution': {
            'executed_command_count': len(_list(engine.get('executed_commands'))),
            'planned_command_count': len(_list(engine.get('planned_commands'))),
            'execution_source': str(engine.get('execution_source') or ''),
        },
        'outcome': {
            'status': str(engine.get('status') or ''),
            'returncode': int(engine.get('returncode', 0) or 0),
            'reason': str(engine.get('reason') or ''),
            'stdout_present': bool(engine.get('stdout')),
            'stderr_present': bool(engine.get('stderr')),
        },
        'evidence_refs': [{'kind': 'evidence_contract', 'path': 'evidence_contract.json'}],
        'non_claims': ['receipt_does_not_include_raw_logs', 'receipt_does_not_prove_live_vulnerability_evidence'],
    })


def build_evidence_contract_v02(pipeline_data: Dict[str, Any], execution_receipt: Mapping[str, Any], execution_ticket: Mapping[str, Any]) -> Dict[str, Any]:
    return sanitize_public_artifact({
        'artifact_type': 'evidence_contract',
        'schema_version': 'v0.2',
        'schema_ref': 'schemas/evidence_contract.v0.2.schema.json',
        'evidence_contract_id': str(pipeline_data.get('run_id') or 'ravenclaw-evidence-contract'),
        'created_at': _created_at(pipeline_data),
        'links': {'execution_receipt': _link('execution_receipt', execution_receipt), 'execution_ticket': _link('execution_ticket', execution_ticket)},
        'claims': [{'id': 'ravenclaw_lifecycle_chain_present', 'statement': 'Ravenclaw emitted a public-safe SCLite v0.2 lifecycle chain for this run.', 'status': 'met'}],
        'non_claims': ['does_not_claim_live_vulnerability_evidence', 'does_not_include_private_runtime_logs', 'does_not_prove_legal_authorization'],
        'verification': {'commands': ['sclite validate-chain artifact_chain_manifest.json']},
        'replay': {'mode': 'static_bundle_verification', 'live_execution_required': False},
    })


def build_lifecycle_artifacts_v02(pipeline_data: Dict[str, Any]) -> Dict[str, Any]:
    """Build SCLite v0.2 lifecycle artifacts plus a hash-linked chain manifest."""
    intent = build_intent_contract_v02(pipeline_data)
    policy = build_policy_decision_artifact_v02(pipeline_data, intent)
    contract = build_execution_contract_v02(pipeline_data, intent, policy)
    ticket = build_execution_ticket_v02(pipeline_data, policy, contract)
    receipt = build_execution_receipt_v02(pipeline_data, ticket, contract)
    evidence = build_evidence_contract_v02(pipeline_data, receipt, ticket)
    artifacts = {
        'intent_contract.json': intent,
        'policy_decision.v0.2.json': policy,
        'execution_contract.json': contract,
        'execution_ticket.json': ticket,
        'execution_receipt.v0.2.json': receipt,
        'evidence_contract.json': evidence,
    }
    manifest = build_artifact_chain_manifest([
        {'role': 'intent_contract', 'path': 'intent_contract.json', 'value': intent},
        {'role': 'policy_decision', 'path': 'policy_decision.v0.2.json', 'value': policy},
        {'role': 'execution_contract', 'path': 'execution_contract.json', 'value': contract},
        {'role': 'execution_ticket', 'path': 'execution_ticket.json', 'value': ticket},
        {'role': 'execution_receipt', 'path': 'execution_receipt.v0.2.json', 'value': receipt},
        {'role': 'evidence_contract', 'path': 'evidence_contract.json', 'value': evidence},
    ], chain_id=str(pipeline_data.get('run_id') or 'ravenclaw-sclite-v0.2-lifecycle'), created_at=_created_at(pipeline_data))
    artifacts['artifact_chain_manifest.json'] = manifest
    return artifacts
