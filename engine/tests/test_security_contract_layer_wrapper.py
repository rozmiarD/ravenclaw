from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINE_DIR = ROOT / 'engine'
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

import sclite_lifecycle_projection as projection  # type: ignore
import security_contract_layer as wrapper  # type: ignore
from sclite import artifacts as core_artifacts
from sclite.integrity import artifact_descriptor, verify_artifact_chain_manifest


def _demo_pipeline_data() -> dict:
    return {
        'run_id': 'test-run-001',
        'created_at': '2026-05-06T18:31:00+00:00',
        'settings': {'runtime_mode': 'demo'},
        'policy_gate': {'pass': True, 'reason': 'ok'},
        'auditor': {'owner_gate': False, 'constraints': {'aggression': 1}},
        'prepared_execution_spec': {
            'target': 'https://example.com',
            'target_host': 'example.com',
            'target_in_scope': True,
            'action_type': 'single_probe',
            'resolved_tool': 'curl',
            'normalized_args': ['https://example.com'],
            'execution_plan': [{'tool': 'curl', 'args': ['https://example.com']}],
            'scope_facts': {'target': 'https://example.com', 'target_host': 'example.com', 'target_in_scope': True},
        },
        'approved_execution_spec': {
            'spec_version': '2026-03-18.approved.v1',
            'target': 'https://example.com',
            'target_host': 'example.com',
            'target_in_scope': True,
            'resolved_tool': 'curl',
            'normalized_args': ['https://example.com'],
            'execution_plan': [{'tool': 'curl', 'args': ['https://example.com']}],
            'approval': {'decision': 'approve', 'reason': 'ok', 'approval_source': 'auditor'},
            'execution_truth': {
                'artifact_type': 'approved_execution_spec',
                'execution_plan': [{'tool': 'curl', 'args': ['https://example.com']}],
                'normalized_args': ['https://example.com'],
            },
        },
        'engine': {
            'status': 'dry-run',
            'returncode': 0,
            'reason': 'mock',
            'execution_source': 'mock_adapter',
            'planned_commands': [['curl', 'https://example.com']],
            'executed_commands': [],
        },
    }


def test_lifecycle_projection_is_ravenclaw_owned_not_govengine_adapter() -> None:
    wrapper_source = (ROOT / 'engine' / 'security_contract_layer.py').read_text(encoding='utf-8')
    projection_source = (ROOT / 'engine' / 'sclite_lifecycle_projection.py').read_text(encoding='utf-8')

    assert 'govengine.sclite_adapter' not in wrapper_source
    assert 'govengine.sclite_adapter' not in projection_source
    assert 'build_proof_trace_artifacts' not in wrapper_source
    assert wrapper.CURRENT_LIFECYCLE_TRACE_FILES == projection.CURRENT_LIFECYCLE_TRACE_FILES


def test_current_lifecycle_uses_scoped_ticket_and_verifies_chain(tmp_path: Path) -> None:
    artifacts = wrapper.build_current_lifecycle_artifacts(_demo_pipeline_data())

    assert list(artifacts) == projection.CURRENT_LIFECYCLE_TRACE_FILES
    assert artifacts['execution_ticket.json']['schema_version'] == 'v0.3'
    assert artifacts['execution_ticket.json']['ticket_profile'] == 'scoped_execution_ticket'
    for filename, artifact in artifacts.items():
        (tmp_path / filename).write_text(json.dumps(artifact, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        core_artifacts.validate_artifact(artifact, str(artifact['schema_ref']))
    result = verify_artifact_chain_manifest(artifacts['artifact_chain_manifest.json'], root=tmp_path)
    assert result['status'] == 'passed'


def test_current_lifecycle_adds_demo_signature_trust_metadata() -> None:
    artifacts = wrapper.build_current_lifecycle_artifacts(_demo_pipeline_data())
    ticket = artifacts['execution_ticket.json']

    assert ticket['signature']['mode'] == 'detached_demo_digest'
    assert ticket['signature']['binds_digest'] == artifact_descriptor(artifacts['execution_contract.json'])['digest']
    assert ticket['trust_decision']['trust_status'] == 'trusted'
    assert 'no_pki_ca_kms_or_key_store_in_govengine' in ticket['non_claims']


def test_current_lifecycle_keeps_integrity_only_signature_outside_demo_mode() -> None:
    pipeline_data = _demo_pipeline_data()
    pipeline_data['settings']['runtime_mode'] = 'test'

    artifacts = wrapper.build_current_lifecycle_artifacts(pipeline_data)

    assert artifacts['execution_ticket.json']['signature']['mode'] == 'not_signed_integrity_only'


def test_root_shared_schema_copies_remain_in_parity_with_sclite_dependency() -> None:
    ravenclaw_owned_schemas = {'security_contract_validation_receipt.v0.1.schema.json'}
    for schema_file in core_artifacts.SCHEMA_FILES.values():
        if schema_file in ravenclaw_owned_schemas:
            continue
        assert (core_artifacts.schema_dir() / schema_file).read_bytes() == (ROOT / 'schemas' / schema_file).read_bytes(), schema_file


def test_ravenclaw_owns_current_validation_receipt_trace() -> None:
    receipt_schema = json.loads(
        (ROOT / 'schemas' / 'security_contract_validation_receipt.v0.1.schema.json').read_text(encoding='utf-8')
    )
    assert receipt_schema['properties']['validated_trace']['const'] == (
        'runtime projection -> policy decision -> execution contract -> scoped execution ticket -> '
        'execution receipt -> evidence contract -> review bundle'
    )


def test_govengine_context_imports_without_ravenclaw_workspace(monkeypatch) -> None:
    monkeypatch.delenv('RAVENCLAW_WORKSPACE', raising=False)
    from govengine import GovEngineContext, ravenclaw_context

    context = ravenclaw_context(ROOT)
    assert isinstance(context, GovEngineContext)
    assert context.profile == 'ravenclaw'
    assert context.repo_root == ROOT


def test_current_execution_ticket_passes_runtime_gate() -> None:
    from executor import ExecutionEngine  # type: ignore

    pipeline_data = _demo_pipeline_data()
    artifacts = wrapper.build_current_lifecycle_artifacts(pipeline_data)
    engine = ExecutionEngine()
    engine.scope_domains = {'exact': ['example.com'], 'suffix': [], 'exclude_exact': [], 'exclude_suffix': []}
    result = engine.execute_approved_spec(
        pipeline_data['approved_execution_spec'],
        dry_run=True,
        execution_ticket=artifacts['execution_ticket.json'],
        execution_contract=artifacts['execution_contract.json'],
        require_execution_ticket=True,
    )

    assert result['execution_ticket_gate']['status'] == 'passed'


def test_current_lifecycle_projects_compact_ooda_without_raw_telemetry() -> None:
    pipeline_data = _demo_pipeline_data()
    pipeline_data['engine']['control_decisions'] = [{
        'decision': 'cooldown',
        'reason_code': 'host_health_transport_noise',
        'interrupting': True,
        'observations': [{
            'kind': 'before_step',
            'severity': 'warning',
            'subject': 'curl',
            'detail': 'raw stderr and token should not appear',
            'facts': {'step_index': 1, 'token': 'secret-token'},
        }],
        'orientation': {'notes': ['private detail']},
    }]

    lifecycle = wrapper.build_current_lifecycle_artifacts(pipeline_data)
    receipt = lifecycle['execution_receipt.v0.2.json']
    evidence = lifecycle['evidence_contract.json']

    assert receipt['control_decision_count'] == 1
    assert receipt['control_decisions'][0]['decision'] == 'cooldown'
    assert 'observations' not in receipt['control_decisions'][0]
    assert 'secret-token' not in json.dumps(lifecycle, sort_keys=True)
    assert 'private detail' not in json.dumps(lifecycle, sort_keys=True)
    assert evidence['governance_evidence']['control_decision_count'] == 1
