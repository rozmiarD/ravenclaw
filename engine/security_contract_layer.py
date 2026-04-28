from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from execution_contracts import redact_prepared_execution_spec_for_auditor  # type: ignore
from policy_gateway import normalize_policy_decision_v0  # type: ignore


POLICY_DECISION_SCHEMA_VERSION = '2026-04-27.policy-decision.v0.1'
APPROVED_EXECUTION_SPEC_VERSION = '2026-03-18.approved.v1'
EXECUTION_RECEIPT_ARTIFACT_TYPE = 'execution_receipt'
EVIDENCE_BUNDLE_SCHEMA_VERSION = '2026-04-28.evidence-bundle.v0.1'
EVIDENCE_BUNDLE_ARTIFACT_TYPE = 'evidence_bundle'
DEMO_PROOF_MODE = 'dry_run_contract_proof'
PUBLIC_DEMO_TARGET_HOST = 'example.com'

POLICY_DECISION_FILE = 'policy_decision.json'
REDACTED_PREPARED_EXECUTION_SPEC_FILE = 'prepared_execution_spec.redacted.json'
APPROVED_EXECUTION_SPEC_FILE = 'approved_execution_spec.json'
EXECUTION_RECEIPT_FILE = 'execution_receipt.json'
EVIDENCE_BUNDLE_FILE = 'evidence_bundle.json'
EVIDENCE_SUMMARY_FILE = 'evidence_summary.md'

PUBLIC_DEMO_NON_CLAIMS = [
    'does_not_claim_live_vulnerability_evidence',
    'does_not_execute_against_live_private_targets',
    'does_not_include_raw_stdout_stderr_or_private_paths',
]

PROOF_TRACE_FILES = [
    POLICY_DECISION_FILE,
    REDACTED_PREPARED_EXECUTION_SPEC_FILE,
    APPROVED_EXECUTION_SPEC_FILE,
    EXECUTION_RECEIPT_FILE,
    EVIDENCE_BUNDLE_FILE,
    EVIDENCE_SUMMARY_FILE,
]


class ProofTraceInvariantError(ValueError):
    pass


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _sanitize_string(value: Any) -> str:
    text = str(value or '')
    root = str(repo_root())
    if root and root in text:
        text = text.replace(root, '<workspace_path_redacted>')
    if text.startswith('/home/'):
        return '<path_redacted>'
    for header in ('X-Bug-Bounty:', 'X-Test-Account-Email:', 'X-Canary:'):
        if text.startswith(header):
            return f'{header} <redacted>'
    if 'session=' in text:
        return 'session=<redacted>'
    return text


def sanitize_public_artifact(value: Any) -> Any:
    if isinstance(value, dict):
        if isinstance(value.get('name'), str) and ('value' in value or 'raw' in value):
            out = {k: sanitize_public_artifact(v) for k, v in value.items()}
            out['value'] = '<redacted>'
            if 'raw' in out:
                out['raw'] = f"{value.get('name')}: <redacted>"
            return out
        out: Dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key or '').lower()
            if key_text in {'password', 'password_ref', 'secret', 'token', 'api_key', 'apikey'} and item:
                out[key] = '<redacted>'
            elif key_text in {'stdout', 'stderr'}:
                out[key] = '' if not item else '<omitted_for_public_demo>'
            else:
                out[key] = sanitize_public_artifact(item)
        return out
    if isinstance(value, list):
        return [sanitize_public_artifact(item) for item in value]
    if isinstance(value, str):
        return _sanitize_string(value)
    return value


def build_policy_decision_artifact(pipeline_data: Dict[str, Any]) -> Dict[str, Any]:
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


def build_execution_receipt_artifact(pipeline_data: Dict[str, Any]) -> Dict[str, Any]:
    engine = dict(pipeline_data.get('engine') or {}) if isinstance(pipeline_data.get('engine'), dict) else {}
    return sanitize_public_artifact({
        'artifact_type': EXECUTION_RECEIPT_ARTIFACT_TYPE,
        'runtime_mode': str((pipeline_data.get('settings') or {}).get('runtime_mode') or ''),
        'status': str(engine.get('status') or ''),
        'returncode': int(engine.get('returncode', 0) or 0),
        'reason': str(engine.get('reason') or ''),
        'execution_source': str(engine.get('execution_source') or ''),
        'dry_run': str(engine.get('status') or '') == 'dry-run',
        'compiled_action': dict(engine.get('compiled_action') or {}) if isinstance(engine.get('compiled_action'), dict) else {},
        'command_input_summary': dict(engine.get('command_input_summary') or {}) if isinstance(engine.get('command_input_summary'), dict) else {},
        'planned_command_count': len(engine.get('planned_commands') or []) if isinstance(engine.get('planned_commands'), list) else 0,
        'executed_command_count': len(engine.get('executed_commands') or []) if isinstance(engine.get('executed_commands'), list) else 0,
        'stdout_present': bool(engine.get('stdout')),
        'stderr_present': bool(engine.get('stderr')),
    })


def build_demo_success_criteria(pipeline_data: Dict[str, Any]) -> Dict[str, Any]:
    """Return public-safe proof criteria for the demo bundle.

    This is deliberately about contract/proof-trace completeness, not live
    vulnerability evidence. Public demo mode must stay local/dry-run and should
    say exactly what was proven.
    """
    existing = pipeline_data.get('success_criteria')
    if isinstance(existing, dict) and isinstance(existing.get('evidence'), list) and existing.get('evidence'):
        return sanitize_public_artifact(existing)

    runtime_mode = str((pipeline_data.get('settings') or {}).get('runtime_mode') or '')
    engine = dict(pipeline_data.get('engine') or {}) if isinstance(pipeline_data.get('engine'), dict) else {}
    policy_gate = dict(pipeline_data.get('policy_gate') or {}) if isinstance(pipeline_data.get('policy_gate'), dict) else {}
    approved = pipeline_data.get('approved_execution_spec') if isinstance(pipeline_data.get('approved_execution_spec'), dict) else {}
    prepared = pipeline_data.get('prepared_execution_spec') if isinstance(pipeline_data.get('prepared_execution_spec'), dict) else {}

    criteria = [
        {
            'id': 'demo_runtime_mode',
            'claim': 'Demo bundle was generated in demo mode.',
            'source': 'run_pipeline.demo.json',
            'status': 'met' if runtime_mode == 'demo' else 'not_met',
            'observed': runtime_mode,
        },
        {
            'id': 'policy_decision_recorded',
            'claim': 'Policy gate decision was captured as a contract artifact.',
            'source': POLICY_DECISION_FILE,
            'status': 'met' if policy_gate else 'not_met',
            'observed': str(policy_gate.get('reason') or ''),
        },
        {
            'id': 'prepared_spec_redacted',
            'claim': 'Prepared execution spec can be redacted for public/auditor review.',
            'source': REDACTED_PREPARED_EXECUTION_SPEC_FILE,
            'status': 'met' if prepared else 'not_met',
        },
        {
            'id': 'approved_spec_recorded',
            'claim': 'Approved execution spec was produced before executor handoff.',
            'source': APPROVED_EXECUTION_SPEC_FILE,
            'status': 'met' if approved else 'not_met',
            'observed': str((approved or {}).get('spec_version') or ''),
        },
        {
            'id': 'dry_run_receipt_recorded',
            'claim': 'Execution receipt records dry-run/mock execution instead of live offensive execution.',
            'source': EXECUTION_RECEIPT_FILE,
            'status': 'met' if str(engine.get('status') or '') == 'dry-run' else 'not_met',
            'observed': str(engine.get('status') or ''),
        },
        {
            'id': 'public_safe_target',
            'claim': 'Public demo target remains example.com/local-safe.',
            'source': APPROVED_EXECUTION_SPEC_FILE,
            'status': 'met' if str((approved or {}).get('target_host') or '') == PUBLIC_DEMO_TARGET_HOST else 'not_met',
            'observed': str((approved or {}).get('target_host') or ''),
        },
    ]
    met = all(item.get('status') == 'met' for item in criteria)
    return sanitize_public_artifact({
        'status': DEMO_PROOF_MODE,
        'met': met,
        'gap': 'live_target_evidence_not_collected_by_design',
        'evidence': criteria,
        'non_claims': list(PUBLIC_DEMO_NON_CLAIMS),
    })


def build_evidence_bundle_artifact(pipeline_data: Dict[str, Any]) -> Dict[str, Any]:
    success = build_demo_success_criteria(pipeline_data)
    evidence = success.get('evidence') if isinstance(success.get('evidence'), list) else []
    settings = dict(pipeline_data.get('settings') or {}) if isinstance(pipeline_data.get('settings'), dict) else {}
    approved = dict(pipeline_data.get('approved_execution_spec') or {}) if isinstance(pipeline_data.get('approved_execution_spec'), dict) else {}
    engine = dict(pipeline_data.get('engine') or {}) if isinstance(pipeline_data.get('engine'), dict) else {}
    runtime_mode = str(settings.get('runtime_mode') or '')
    target_host = str(approved.get('target_host') or '')
    dry_run = str(engine.get('status') or '') == 'dry-run'
    return sanitize_public_artifact({
        'schema_version': EVIDENCE_BUNDLE_SCHEMA_VERSION,
        'artifact_type': EVIDENCE_BUNDLE_ARTIFACT_TYPE,
        'proof_mode': DEMO_PROOF_MODE,
        'status': str(success.get('status') or ''),
        'met': bool(success.get('met', False)),
        'gap': str(success.get('gap') or ''),
        'evidence_items': len(evidence),
        'criteria': evidence,
        'non_claims': list(success.get('non_claims') or []) if isinstance(success.get('non_claims'), list) else [],
        'source_artifacts': {
            'policy_decision': POLICY_DECISION_FILE,
            'prepared_execution_spec': REDACTED_PREPARED_EXECUTION_SPEC_FILE,
            'approved_execution_spec': APPROVED_EXECUTION_SPEC_FILE,
            'execution_receipt': EXECUTION_RECEIPT_FILE,
            'evidence_summary': EVIDENCE_SUMMARY_FILE,
        },
        'public_safety': {
            'runtime_mode': runtime_mode,
            'target_host': target_host,
            'dry_run': dry_run,
            'raw_live_evidence_included': False,
            'raw_stdout_stderr_included': False,
        },
    })


def build_evidence_summary_markdown(pipeline_data: Dict[str, Any]) -> str:
    bundle = build_evidence_bundle_artifact(pipeline_data)
    evidence = bundle.get('criteria') if isinstance(bundle.get('criteria'), list) else []
    lines = [
        '# Ravenclaw Demo Evidence Summary',
        '',
        f"- final_status: `{pipeline_data.get('final_status', '')}`",
        f"- reason_code: `{pipeline_data.get('reason_code', '')}`",
        f"- success_status: `{bundle.get('status', 'not_provided')}`",
        f"- success_met: `{bool(bundle.get('met', False))}`",
        f"- evidence_items: `{len(evidence)}`",
        '',
        '## Evidence criteria',
        '',
    ]
    gap = str(bundle.get('gap') or '').strip()
    if gap:
        lines.insert(6, f"- evidence_gap: `{gap}`")
    for item in evidence:
        if not isinstance(item, dict):
            continue
        observed = str(item.get('observed') or '').strip()
        suffix = f" Observed: `{observed}`." if observed else ''
        lines.append(f"- `{item.get('status', '')}` — {item.get('id', '')}: {item.get('claim', '')} Source: `{item.get('source', '')}`.{suffix}")
    non_claims = bundle.get('non_claims') if isinstance(bundle.get('non_claims'), list) else []
    if non_claims:
        lines.extend(['', '## Non-claims', ''])
        for item in non_claims:
            lines.append(f"- `{item}`")
    lines.extend([
        '',
        'This public demo bundle is dry-run/local and intentionally does not include raw live-target evidence.',
    ])
    return '\n'.join(lines) + '\n'


def build_proof_trace_artifacts(pipeline_data: Dict[str, Any]) -> Dict[str, Any]:
    prepared = dict(pipeline_data.get('prepared_execution_spec') or {}) if isinstance(pipeline_data.get('prepared_execution_spec'), dict) else {}
    approved = dict(pipeline_data.get('approved_execution_spec') or {}) if isinstance(pipeline_data.get('approved_execution_spec'), dict) else {}
    return {
        POLICY_DECISION_FILE: sanitize_public_artifact(build_policy_decision_artifact(pipeline_data)),
        REDACTED_PREPARED_EXECUTION_SPEC_FILE: sanitize_public_artifact(redact_prepared_execution_spec_for_auditor(prepared)),
        APPROVED_EXECUTION_SPEC_FILE: sanitize_public_artifact(approved),
        EXECUTION_RECEIPT_FILE: build_execution_receipt_artifact(pipeline_data),
        EVIDENCE_BUNDLE_FILE: build_evidence_bundle_artifact(pipeline_data),
        EVIDENCE_SUMMARY_FILE: build_evidence_summary_markdown(pipeline_data),
    }


def proof_trace_manifest() -> Dict[str, Dict[str, str]]:
    return {
        POLICY_DECISION_FILE: {
            'kind': 'json',
            'schema': 'schemas/policy_decision.v0.1.schema.json',
            'schema_version': POLICY_DECISION_SCHEMA_VERSION,
        },
        REDACTED_PREPARED_EXECUTION_SPEC_FILE: {
            'kind': 'json',
            'schema': '',
            'schema_version': '2026-03-18.prepared.v1',
        },
        APPROVED_EXECUTION_SPEC_FILE: {
            'kind': 'json',
            'schema': 'schemas/approved_execution_spec.v0.1.schema.json',
            'schema_version': APPROVED_EXECUTION_SPEC_VERSION,
        },
        EXECUTION_RECEIPT_FILE: {
            'kind': 'json',
            'schema': 'schemas/execution_receipt.v0.1.schema.json',
            'artifact_type': EXECUTION_RECEIPT_ARTIFACT_TYPE,
        },
        EVIDENCE_BUNDLE_FILE: {
            'kind': 'json',
            'schema': 'schemas/evidence_bundle.v0.1.schema.json',
            'schema_version': EVIDENCE_BUNDLE_SCHEMA_VERSION,
        },
        EVIDENCE_SUMMARY_FILE: {
            'kind': 'markdown',
            'schema': '',
            'schema_version': '',
        },
    }


def _expect_dict(artifacts: Dict[str, Any], filename: str, errors: List[str]) -> Dict[str, Any]:
    value = artifacts.get(filename)
    if not isinstance(value, dict):
        errors.append(f'{filename}:not_object')
        return {}
    return value


def validate_public_proof_trace_artifacts(artifacts: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    for filename in PROOF_TRACE_FILES:
        if filename not in artifacts:
            errors.append(f'{filename}:missing')

    policy = _expect_dict(artifacts, POLICY_DECISION_FILE, errors)
    if policy:
        if policy.get('schema_version') != POLICY_DECISION_SCHEMA_VERSION:
            errors.append(f'{POLICY_DECISION_FILE}:schema_version')
        if policy.get('decision') not in {'allow_prepare', 'owner_approval_required', 'deny'}:
            errors.append(f'{POLICY_DECISION_FILE}:decision')
        if policy.get('redaction_required') is not True:
            errors.append(f'{POLICY_DECISION_FILE}:redaction_required')

    prepared = _expect_dict(artifacts, REDACTED_PREPARED_EXECUTION_SPEC_FILE, errors)
    if prepared:
        if any(secret in str(prepared) for secret in ('private-researcher-handle', 'session=abc', str(repo_root()))):
            errors.append(f'{REDACTED_PREPARED_EXECUTION_SPEC_FILE}:public_sanitization')

    approved = _expect_dict(artifacts, APPROVED_EXECUTION_SPEC_FILE, errors)
    if approved:
        if approved.get('spec_version') != APPROVED_EXECUTION_SPEC_VERSION:
            errors.append(f'{APPROVED_EXECUTION_SPEC_FILE}:spec_version')
        if str(approved.get('target_host') or '') != PUBLIC_DEMO_TARGET_HOST:
            errors.append(f'{APPROVED_EXECUTION_SPEC_FILE}:public_target')

    receipt = _expect_dict(artifacts, EXECUTION_RECEIPT_FILE, errors)
    if receipt:
        if receipt.get('artifact_type') != EXECUTION_RECEIPT_ARTIFACT_TYPE:
            errors.append(f'{EXECUTION_RECEIPT_FILE}:artifact_type')
        if receipt.get('dry_run') is not True:
            errors.append(f'{EXECUTION_RECEIPT_FILE}:dry_run')
        if 'stdout' in receipt or 'stderr' in receipt:
            errors.append(f'{EXECUTION_RECEIPT_FILE}:raw_output_present')

    bundle = _expect_dict(artifacts, EVIDENCE_BUNDLE_FILE, errors)
    if bundle:
        if bundle.get('schema_version') != EVIDENCE_BUNDLE_SCHEMA_VERSION:
            errors.append(f'{EVIDENCE_BUNDLE_FILE}:schema_version')
        if bundle.get('artifact_type') != EVIDENCE_BUNDLE_ARTIFACT_TYPE:
            errors.append(f'{EVIDENCE_BUNDLE_FILE}:artifact_type')
        if bundle.get('proof_mode') != DEMO_PROOF_MODE:
            errors.append(f'{EVIDENCE_BUNDLE_FILE}:proof_mode')
        criteria = bundle.get('criteria') if isinstance(bundle.get('criteria'), list) else []
        evidence_items = bundle.get('evidence_items')
        if not isinstance(evidence_items, int) or evidence_items != len(criteria):
            errors.append(f'{EVIDENCE_BUNDLE_FILE}:evidence_items_mismatch')
        safety = bundle.get('public_safety') if isinstance(bundle.get('public_safety'), dict) else {}
        if safety.get('runtime_mode') != 'demo':
            errors.append(f'{EVIDENCE_BUNDLE_FILE}:runtime_mode')
        if safety.get('target_host') != PUBLIC_DEMO_TARGET_HOST:
            errors.append(f'{EVIDENCE_BUNDLE_FILE}:target_host')
        if safety.get('dry_run') is not True:
            errors.append(f'{EVIDENCE_BUNDLE_FILE}:dry_run')
        if safety.get('raw_live_evidence_included') is not False:
            errors.append(f'{EVIDENCE_BUNDLE_FILE}:raw_live_evidence')
        if safety.get('raw_stdout_stderr_included') is not False:
            errors.append(f'{EVIDENCE_BUNDLE_FILE}:raw_stdout_stderr')
        non_claims = set(str(item) for item in (bundle.get('non_claims') or []))
        for item in PUBLIC_DEMO_NON_CLAIMS:
            if item not in non_claims:
                errors.append(f'{EVIDENCE_BUNDLE_FILE}:missing_non_claim:{item}')

    summary = artifacts.get(EVIDENCE_SUMMARY_FILE)
    if not isinstance(summary, str):
        errors.append(f'{EVIDENCE_SUMMARY_FILE}:not_markdown')
    elif 'does_not_claim_live_vulnerability_evidence' not in summary:
        errors.append(f'{EVIDENCE_SUMMARY_FILE}:missing_non_claims')
    return errors


def assert_public_proof_trace_artifacts(artifacts: Dict[str, Any]) -> None:
    errors = validate_public_proof_trace_artifacts(artifacts)
    if errors:
        raise ProofTraceInvariantError(';'.join(errors))
