from __future__ import annotations

import sys
from pathlib import Path

_BOOTSTRAP_ROOT = Path(__file__).resolve().parents[1]
if str(_BOOTSTRAP_ROOT) not in sys.path:
    sys.path.insert(0, str(_BOOTSTRAP_ROOT))

from govengine.context import ravenclaw_context
from paths import configured_workspace  # type: ignore

_CONTEXT = ravenclaw_context(configured_workspace(_BOOTSTRAP_ROOT))
ROOT = _CONTEXT.repo_root

from sclite.artifacts import (
    JsonSchemaValidationError,
    validate_json_schema_value,
    validate_schema_ref,
)
from sclite.integrity import artifact_descriptor
from sclite.redaction import sanitize_public_artifact  # noqa: F401
from sclite.scope_fidelity import (  # noqa: F401
    build_scope_fidelity_report,
    build_scope_fidelity_report_from_approved_spec,
    summarize_scope_fidelity,
    validate_scope_fidelity_report as _sclite_validate_scope_fidelity_report,
)
from sclite_lifecycle_projection import (  # type: ignore
    CURRENT_LIFECYCLE_TRACE_FILES,
    build_evidence_contract as _build_evidence_contract,
    build_execution_contract as _build_execution_contract,
    build_execution_receipt as _build_execution_receipt,
    build_execution_ticket as _build_execution_ticket,
    build_intent_contract as _build_intent_contract,
    build_policy_decision as _build_policy_decision,
)
from govengine_trust_demo import demo_sign_execution_contract  # type: ignore
from ooda_receipts import (  # type: ignore
    add_ooda_to_execution_receipt,
    compact_ooda_control_decisions,
)


def repo_root() -> Path:
    """Return the Ravenclaw repo root through GovEngine context."""
    return _CONTEXT.repo_root

def validate_scope_fidelity_report(report, root: Path | None = None) -> None:
    """Validate a Scope Fidelity report through the SCLite package surface."""
    _sclite_validate_scope_fidelity_report(report)


def build_execution_receipt(pipeline_data, execution_ticket, execution_contract):
    """Build a current receipt and project compact OODA summaries when present."""
    return add_ooda_to_execution_receipt(_build_execution_receipt(pipeline_data, execution_ticket, execution_contract), pipeline_data)


def build_evidence_contract(pipeline_data, execution_receipt, execution_ticket):
    """Build the current evidence contract with compact OODA governance evidence."""
    contract = _build_evidence_contract(pipeline_data, execution_receipt, execution_ticket)
    decisions = compact_ooda_control_decisions(pipeline_data)
    if decisions:
        claims = list(contract.get('claims') or []) if isinstance(contract.get('claims'), list) else []
        claims.append({
            'id': 'ooda_control_decisions_recorded',
            'statement': 'Compact GovEngine OODA control decisions were recorded as governance evidence without raw telemetry.',
            'status': 'met',
            'claim_type': 'receipt_bounded_dry_run',
            'bounded_by_receipt': True,
            'requires_live_execution': False,
            'source_receipt_id': str(execution_receipt.get('receipt_id') or ''),
        })
        contract['claims'] = claims
        contract['governance_evidence'] = {
            'ooda_control_evaluated': True,
            'control_decision_count': len(decisions),
            'interrupting_decision_count': sum(1 for decision in decisions if decision.get('interrupting') is True),
            'control_decisions': decisions,
            'source': 'execution_receipt.v0.2.json',
            'non_claim': 'OODA control decisions are governance evidence, not live vulnerability evidence.',
        }
    return sanitize_public_artifact(contract)


def build_current_lifecycle_artifacts(pipeline_data):
    """Build the current scoped-ticket lifecycle for runtime/demo review."""
    intent = _build_intent_contract(pipeline_data)
    policy = _build_policy_decision(pipeline_data, intent)
    contract = _build_execution_contract(pipeline_data, intent, policy)
    ticket = _build_execution_ticket(pipeline_data, policy, contract)
    if str(((pipeline_data.get('settings') or {}) if isinstance(pipeline_data.get('settings'), dict) else {}).get('runtime_mode') or '') == 'demo':
        trust = demo_sign_execution_contract(artifact_descriptor(contract), purpose='execution_contract_ticket_binding')
        ticket['signature'] = trust['signature']
        ticket['trust_decision'] = trust['trust_decision']
        ticket['non_claims'] = list(dict.fromkeys(list(ticket.get('non_claims') or []) + trust['non_claims']))
    receipt = build_execution_receipt(pipeline_data, ticket, contract)
    evidence = build_evidence_contract(pipeline_data, receipt, ticket)
    from sclite.tickets import verify_ticket_use

    verify_ticket_use(ticket, contract, receipt, evidence)
    from sclite.integrity import build_artifact_chain_manifest

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
    ], chain_id=str(pipeline_data.get('run_id') or 'ravenclaw-sclite-current-lifecycle'))
    artifacts['artifact_chain_manifest.json'] = manifest
    return artifacts
