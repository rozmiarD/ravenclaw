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

from sclite.artifacts import *  # noqa: F401,F403
from sclite.redaction import sanitize_public_artifact  # noqa: F401
from sclite.scope_fidelity import (  # noqa: F401
    build_scope_fidelity_report,
    build_scope_fidelity_report_from_approved_spec,
    summarize_scope_fidelity,
    validate_scope_fidelity_report as _sclite_validate_scope_fidelity_report,
)
from scl_ravenclaw_adapter import (  # noqa: F401
    LIFECYCLE_TRACE_FILES_V02,
    build_evidence_contract_v02 as _build_evidence_contract_v02,
    build_execution_contract_v02,
    build_execution_receipt_v02 as _build_execution_receipt_v02,
    build_execution_ticket_v02,
    build_intent_contract_v02,
    build_policy_decision_artifact,
    build_policy_decision_artifact_v02,
    build_proof_trace_artifacts as _build_proof_trace_artifacts,
    redact_prepared_execution_spec as redact_prepared_spec,
)
from ooda_receipts import (  # type: ignore
    add_ooda_to_evidence_bundle,
    add_ooda_to_execution_receipt,
    append_ooda_to_evidence_summary,
    compact_ooda_control_decisions,
)


def repo_root() -> Path:
    """Return the Ravenclaw compatibility repo root through GovEngine context."""
    return _CONTEXT.repo_root

def validate_scope_fidelity_report(report, root: Path | None = None) -> None:
    """Compatibility wrapper for pre-SCLite Ravenclaw callers."""
    _sclite_validate_scope_fidelity_report(report)


def build_proof_trace_artifacts(pipeline_data):
    """Build v0.1 proof artifacts and project compact OODA summaries when present."""
    artifacts = _build_proof_trace_artifacts(pipeline_data)
    if compact_ooda_control_decisions(pipeline_data):
        artifacts['execution_receipt.json'] = add_ooda_to_execution_receipt(artifacts['execution_receipt.json'], pipeline_data)
        artifacts['evidence_bundle.json'] = add_ooda_to_evidence_bundle(artifacts['evidence_bundle.json'], pipeline_data)
        artifacts['evidence_summary.md'] = append_ooda_to_evidence_summary(str(artifacts['evidence_summary.md']), pipeline_data)
    return artifacts


def build_execution_receipt_v02(pipeline_data, execution_ticket, execution_contract):
    """Build v0.2 execution receipt and project compact OODA summaries when present."""
    return add_ooda_to_execution_receipt(_build_execution_receipt_v02(pipeline_data, execution_ticket, execution_contract), pipeline_data)


def build_evidence_contract_v02(pipeline_data, execution_receipt, execution_ticket):
    """Build v0.2 evidence contract with governance evidence for compact OODA summaries."""
    contract = _build_evidence_contract_v02(pipeline_data, execution_receipt, execution_ticket)
    decisions = compact_ooda_control_decisions(pipeline_data)
    if decisions:
        claims = list(contract.get('claims') or []) if isinstance(contract.get('claims'), list) else []
        claims.append({
            'id': 'ooda_control_decisions_recorded',
            'statement': 'Compact GovEngine OODA control decisions were recorded as governance evidence without raw telemetry.',
            'status': 'met',
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


def build_lifecycle_artifacts_v02(pipeline_data):
    """Build v0.2 lifecycle artifacts using Ravenclaw's OODA-aware receipt wrappers."""
    intent = build_intent_contract_v02(pipeline_data)
    policy = build_policy_decision_artifact_v02(pipeline_data, intent)
    contract = build_execution_contract_v02(pipeline_data, intent, policy)
    ticket = build_execution_ticket_v02(pipeline_data, policy, contract)
    receipt = build_execution_receipt_v02(pipeline_data, ticket, contract)
    evidence = build_evidence_contract_v02(pipeline_data, receipt, ticket)
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
    ], chain_id=str(pipeline_data.get('run_id') or 'ravenclaw-sclite-v0.2-lifecycle'))
    artifacts['artifact_chain_manifest.json'] = manifest
    return artifacts

