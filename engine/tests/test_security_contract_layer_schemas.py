from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
ROOT = Path(__file__).resolve().parents[2]
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import public_demo_bundle as pdb  # type: ignore
import security_contract_layer as scl  # type: ignore


class SchemaValidationError(AssertionError):
    pass


def _type_name(value: Any) -> str:
    if isinstance(value, bool):
        return 'boolean'
    if isinstance(value, dict):
        return 'object'
    if isinstance(value, list):
        return 'array'
    if isinstance(value, int) and not isinstance(value, bool):
        return 'integer'
    if isinstance(value, str):
        return 'string'
    if value is None:
        return 'null'
    return type(value).__name__


def _assert_type(value: Any, expected: Any, path: str) -> None:
    expected_types = expected if isinstance(expected, list) else [expected]
    actual = _type_name(value)
    if actual not in expected_types:
        raise SchemaValidationError(f'{path}: expected {expected_types}, got {actual}')


def _validate(schema: Dict[str, Any], value: Any, path: str = '$') -> None:
    if 'const' in schema and value != schema['const']:
        raise SchemaValidationError(f'{path}: expected const {schema["const"]!r}, got {value!r}')
    if 'enum' in schema and value not in schema['enum']:
        raise SchemaValidationError(f'{path}: expected one of {schema["enum"]!r}, got {value!r}')
    if 'type' in schema:
        _assert_type(value, schema['type'], path)
    if isinstance(value, str) and 'minLength' in schema and len(value) < int(schema['minLength']):
        raise SchemaValidationError(f'{path}: expected minLength {schema["minLength"]}')
    if isinstance(value, int) and 'minimum' in schema and value < int(schema['minimum']):
        raise SchemaValidationError(f'{path}: expected minimum {schema["minimum"]}')
    if schema.get('type') == 'object':
        assert isinstance(value, dict)
        for key in schema.get('required', []):
            if key not in value:
                raise SchemaValidationError(f'{path}: missing required field {key!r}')
        properties = schema.get('properties') if isinstance(schema.get('properties'), dict) else {}
        for key, subschema in properties.items():
            if key in value and isinstance(subschema, dict):
                _validate(subschema, value[key], f'{path}.{key}')
    if schema.get('type') == 'array':
        assert isinstance(value, list)
        item_schema = schema.get('items')
        if isinstance(item_schema, dict):
            for idx, item in enumerate(value):
                _validate(item_schema, item, f'{path}[{idx}]')


def _load_schema(name: str) -> Dict[str, Any]:
    return json.loads((ROOT / 'schemas' / name).read_text(encoding='utf-8'))


def _demo_pipeline_data() -> Dict[str, Any]:
    return {
        'settings': {'runtime_mode': 'demo'},
        'policy_gate': {'pass': True, 'reason': 'demo_scope_target_override'},
        'auditor': {'owner_gate': False, 'constraints': {'aggression': 6}},
        'prepared_execution_spec': {
            'spec_version': '2026-03-18.prepared.v1',
            'target': 'https://example.com',
            'target_host': 'example.com',
            'target_in_scope': True,
            'action_type': 'single_probe',
            'resolved_tool': 'curl',
            'normalized_args': ['-I', 'https://example.com'],
            'execution_plan': [{'tool': 'curl', 'role': 'probe', 'args': ['-I', 'https://example.com']}],
            'scope_facts': {'target': 'https://example.com', 'target_host': 'example.com', 'target_in_scope': True},
        },
        'approved_execution_spec': {
            'spec_version': '2026-03-18.approved.v1',
            'target': 'https://example.com',
            'target_host': 'example.com',
            'target_in_scope': True,
            'resolved_tool': 'curl',
            'normalized_args': ['-I', 'https://example.com'],
            'execution_plan': [{'tool': 'curl', 'role': 'probe', 'args': ['-I', 'https://example.com']}],
            'scope_facts': {'target': 'https://example.com', 'target_host': 'example.com', 'target_in_scope': True},
            'approval': {'decision': 'approve', 'reason': 'ok', 'reason_code': 'approve_in_scope', 'constraints': {}, 'approval_source': 'auditor', 'owner_override_applied': False, 'approval_transform_chain': []},
            'execution_truth': {'artifact_type': 'approved_execution_spec', 'resolved_tool': 'curl', 'normalized_args': ['-I', 'https://example.com'], 'execution_plan': [], 'command_preview': [], 'command_input_summary': {'target_delivery_mode': 'argv', 'tool': 'curl', 'stdin_present': False}, 'execution_input_summaries': [], 'target_host_match_status': 'exact', 'request_shape_hygiene_status': 'clean'},
        },
        'engine': {
            'status': 'dry-run',
            'returncode': 0,
            'reason': 'mock_execution_adapter',
            'execution_source': 'mock_adapter',
            'stdout': '',
            'stderr': '',
            'planned_commands': [['curl', '-I', 'https://example.com']],
            'executed_commands': [],
            'compiled_action': {'action_type': 'single_probe', 'compiler_tool_choice': 'curl', 'execution_mode': 'normalized', 'recipe_name': ''},
            'command_input_summary': {'preview_source': 'execution_plan_first_step', 'target_delivery_mode': 'argv', 'tool': 'curl', 'role': 'probe', 'stdin_present': False, 'stdin_char_count': 0, 'stdin_line_count': 0, 'stdin_preview': '', 'stdin_preview_truncated': False},
        },
        'final_status': 'warning',
        'reason_code': 'pipeline_warning',
    }


def test_policy_decision_artifact_matches_schema() -> None:
    artifacts = pdb.build_proof_trace_artifacts(_demo_pipeline_data())
    _validate(_load_schema('policy_decision.v0.1.schema.json'), artifacts['policy_decision.json'])


def test_execution_receipt_artifact_matches_schema() -> None:
    artifacts = pdb.build_proof_trace_artifacts(_demo_pipeline_data())
    _validate(_load_schema('execution_receipt.v0.1.schema.json'), artifacts['execution_receipt.json'])


def test_evidence_bundle_artifact_matches_schema() -> None:
    artifacts = pdb.build_proof_trace_artifacts(_demo_pipeline_data())
    _validate(_load_schema('evidence_bundle.v0.1.schema.json'), artifacts['evidence_bundle.json'])


def test_policy_decision_schema_rejects_unknown_decision() -> None:
    artifact = pdb.build_proof_trace_artifacts(_demo_pipeline_data())['policy_decision.json']
    artifact['decision'] = 'maybe'
    try:
        _validate(_load_schema('policy_decision.v0.1.schema.json'), artifact)
    except SchemaValidationError as exc:
        assert 'expected one of' in str(exc)
    else:  # pragma: no cover - assertion guard
        raise AssertionError('unknown policy decision should fail schema validation')


def test_execution_receipt_schema_rejects_raw_receipt_without_artifact_type() -> None:
    artifact = pdb.build_proof_trace_artifacts(_demo_pipeline_data())['execution_receipt.json']
    artifact.pop('artifact_type')
    try:
        _validate(_load_schema('execution_receipt.v0.1.schema.json'), artifact)
    except SchemaValidationError as exc:
        assert 'artifact_type' in str(exc)
    else:  # pragma: no cover - assertion guard
        raise AssertionError('missing artifact_type should fail schema validation')


def test_evidence_bundle_schema_requires_public_safety_non_claims() -> None:
    artifact = pdb.build_proof_trace_artifacts(_demo_pipeline_data())['evidence_bundle.json']
    artifact['public_safety']['raw_live_evidence_included'] = True
    try:
        _validate(_load_schema('evidence_bundle.v0.1.schema.json'), artifact)
    except SchemaValidationError as exc:
        assert 'expected const False' in str(exc)
    else:  # pragma: no cover - assertion guard
        raise AssertionError('public demo evidence bundle must not include raw live evidence')


def test_demo_evidence_summary_states_dry_run_contract_proof_without_live_claims() -> None:
    summary = pdb.build_evidence_summary_markdown(_demo_pipeline_data())
    assert 'success_status: `dry_run_contract_proof`' in summary
    assert 'demo_runtime_mode' in summary
    assert 'dry_run_receipt_recorded' in summary
    assert 'does_not_claim_live_vulnerability_evidence' in summary
    assert 'intentionally does not include raw live-target evidence' in summary


def test_proof_trace_includes_evidence_bundle_before_summary() -> None:
    assert 'evidence_bundle.json' in pdb.PROOF_TRACE_FILES
    assert pdb.PROOF_TRACE_FILES.index('evidence_bundle.json') < pdb.PROOF_TRACE_FILES.index('evidence_summary.md')


def test_security_contract_layer_manifest_tracks_schema_backed_artifacts() -> None:
    manifest = scl.proof_trace_manifest()
    assert list(manifest) == scl.PROOF_TRACE_FILES
    assert manifest['policy_decision.json']['schema_version'] == scl.POLICY_DECISION_SCHEMA_VERSION
    assert manifest['approved_execution_spec.json']['schema_version'] == scl.APPROVED_EXECUTION_SPEC_VERSION
    assert manifest['execution_receipt.json']['artifact_type'] == scl.EXECUTION_RECEIPT_ARTIFACT_TYPE
    assert manifest['evidence_bundle.json']['schema_version'] == scl.EVIDENCE_BUNDLE_SCHEMA_VERSION


def test_security_contract_layer_public_invariant_validation_accepts_demo_trace() -> None:
    artifacts = scl.build_proof_trace_artifacts(_demo_pipeline_data())
    assert scl.validate_public_proof_trace_artifacts(artifacts) == []
    scl.assert_public_proof_trace_artifacts(artifacts)


def test_security_contract_layer_public_invariant_validation_rejects_unsafe_trace() -> None:
    artifacts = scl.build_proof_trace_artifacts(_demo_pipeline_data())
    artifacts['execution_receipt.json']['dry_run'] = False
    artifacts['evidence_bundle.json']['public_safety']['raw_stdout_stderr_included'] = True
    errors = scl.validate_public_proof_trace_artifacts(artifacts)
    assert 'execution_receipt.json:dry_run' in errors
    assert 'evidence_bundle.json:raw_stdout_stderr' in errors
    try:
        scl.assert_public_proof_trace_artifacts(artifacts)
    except scl.ProofTraceInvariantError as exc:
        assert 'execution_receipt.json:dry_run' in str(exc)
    else:  # pragma: no cover - assertion guard
        raise AssertionError('unsafe proof trace should fail invariant assertion')
