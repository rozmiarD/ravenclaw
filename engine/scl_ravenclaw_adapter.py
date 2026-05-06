from __future__ import annotations

from typing import Any, Dict

from execution_contracts import redact_prepared_execution_spec_for_auditor  # type: ignore
from policy_gateway import normalize_policy_decision_v0  # type: ignore
from sclite.artifacts import (
    PREPARED_EXECUTION_SPEC_VERSION,
    REDACTED_PREPARED_EXECUTION_SPEC_ARTIFACT_TYPE,
    build_proof_trace_artifacts as build_scl_proof_trace_artifacts,
)
from sclite.redaction import sanitize_public_artifact


def build_policy_decision_artifact(pipeline_data: Dict[str, Any]) -> Dict[str, Any]:
    """Map Ravenclaw pipeline policy/auditor output to an SCL PolicyDecision artifact."""
    prepared = dict(pipeline_data.get('prepared_execution_spec') or {}) if isinstance(pipeline_data.get('prepared_execution_spec'), dict) else {}
    auditor = dict(pipeline_data.get('auditor') or {}) if isinstance(pipeline_data.get('auditor'), dict) else {}
    return normalize_policy_decision_v0(
        dict(pipeline_data.get('policy_gate') or {}),
        target=str(prepared.get('target') or ''),
        target_host=str(prepared.get('target_host') or ''),
        target_in_scope=bool(prepared.get('target_in_scope', False)),
        resolved_tool=str(prepared.get('resolved_tool') or ''),
        action_type=str(prepared.get('action_type') or ''),
        approval_required=bool(auditor.get('owner_gate', False)),
        constraints=dict(auditor.get('constraints') or {}) if isinstance(auditor.get('constraints'), dict) else {},
        redaction_required=True,
    )


def redact_prepared_execution_spec(pipeline_data: Dict[str, Any]) -> Dict[str, Any]:
    """Map Ravenclaw's prepared-spec redaction into SCLite's v0.1 public artifact shape."""
    prepared = dict(pipeline_data.get('prepared_execution_spec') or {}) if isinstance(pipeline_data.get('prepared_execution_spec'), dict) else {}
    redacted = redact_prepared_execution_spec_for_auditor(prepared)
    safe = sanitize_public_artifact(redacted if isinstance(redacted, dict) else {})
    safe['artifact_type'] = REDACTED_PREPARED_EXECUTION_SPEC_ARTIFACT_TYPE
    safe['spec_version'] = str(safe.get('spec_version') or prepared.get('spec_version') or PREPARED_EXECUTION_SPEC_VERSION)
    safe['target'] = str(safe.get('target') or prepared.get('target') or '')
    safe['target_host'] = str(safe.get('target_host') or prepared.get('target_host') or '')
    safe['target_in_scope'] = bool(safe.get('target_in_scope', prepared.get('target_in_scope', False)))
    safe['resolved_tool'] = str(safe.get('resolved_tool') or prepared.get('resolved_tool') or '')
    safe['normalized_args'] = list(safe.get('normalized_args') or prepared.get('normalized_args') or [])
    safe['execution_plan'] = list(safe.get('execution_plan') or prepared.get('execution_plan') or [])
    safe['scope_facts'] = dict(safe.get('scope_facts') or prepared.get('scope_facts') or {
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
    """Build SCL proof artifacts from Ravenclaw runtime output via the Ravenclaw adapter."""
    return build_scl_proof_trace_artifacts(
        pipeline_data,
        policy_decision_artifact=build_policy_decision_artifact(pipeline_data),
        redacted_prepared_execution_spec=redact_prepared_execution_spec(pipeline_data),
    )
