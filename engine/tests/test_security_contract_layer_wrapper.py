from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINE_DIR = ROOT / 'engine'
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

import security_contract_layer as wrapper  # type: ignore
from govengine import sclite_adapter as adapter
from sclite import artifacts as core_artifacts
from sclite.integrity import artifact_descriptor, verify_artifact_chain_manifest


def test_engine_security_contract_layer_delegates_generic_helpers_to_scl() -> None:
    assert wrapper.validate_public_proof_trace_artifacts is core_artifacts.validate_public_proof_trace_artifacts
    assert wrapper.assert_public_proof_trace_artifacts is core_artifacts.assert_public_proof_trace_artifacts
    assert wrapper.build_execution_receipt_artifact is core_artifacts.build_execution_receipt_artifact
    assert wrapper.build_evidence_bundle_artifact is core_artifacts.build_evidence_bundle_artifact
    assert wrapper.proof_trace_manifest is core_artifacts.proof_trace_manifest
    assert 'import *' not in (ROOT / 'engine' / 'security_contract_layer.py').read_text(encoding='utf-8')


def test_engine_security_contract_layer_uses_ravenclaw_adapter_for_core_artifacts() -> None:
    assert wrapper.build_policy_decision_artifact is adapter.build_policy_decision_artifact
    assert wrapper.build_execution_contract_v02 is adapter.build_execution_contract_v02
    assert wrapper.build_execution_ticket_v02 is adapter.build_execution_ticket_v02
    assert wrapper.build_intent_contract_v02 is adapter.build_intent_contract_v02
    assert wrapper.LIFECYCLE_TRACE_FILES_V02 == adapter.LIFECYCLE_TRACE_FILES_V02


def test_ravenclaw_adapter_builds_policy_decision_from_engine_helpers() -> None:
    policy = adapter.build_policy_decision_artifact({
        'policy_gate': {'pass': True, 'reason': 'ok'},
        'prepared_execution_spec': {
            'target': 'https://example.com',
            'target_host': 'example.com',
            'target_in_scope': True,
            'resolved_tool': 'whatweb',
            'action_type': 'single_probe',
        },
    })
    assert policy['schema_version'] == core_artifacts.POLICY_DECISION_SCHEMA_VERSION
    assert policy['decision'] == 'allow_prepare'


def _demo_pipeline_data() -> dict:
    return {
        'run_id': 'test-run-001',
        'created_at': '2026-05-06T18:31:00+00:00',
        'settings': {'runtime_mode': 'demo'},
        'policy_gate': {'pass': True, 'reason': 'ok'},
        'auditor': {'owner_gate': False, 'constraints': {'aggression': 1}},
        'prepared_execution_spec': {
            'spec_version': '2026-03-18.prepared.v1',
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
            'execution_truth': {'artifact_type': 'approved_execution_spec', 'execution_plan': [{'tool': 'curl', 'args': ['https://example.com']}], 'normalized_args': ['https://example.com']},
        },
        'engine': {'status': 'dry-run', 'returncode': 0, 'reason': 'mock', 'execution_source': 'mock_adapter', 'planned_commands': [['curl', 'https://example.com']], 'executed_commands': []},
    }


def test_ravenclaw_adapter_builds_sclite_v02_lifecycle_chain(tmp_path: Path) -> None:
    artifacts = adapter.build_lifecycle_artifacts_v02(_demo_pipeline_data())

    assert list(artifacts) == adapter.LIFECYCLE_TRACE_FILES_V02
    assert artifacts['intent_contract.json']['artifact_type'] == 'intent_contract'
    assert artifacts['execution_ticket.json']['integrity']['ticket_binds_execution_contract_digest']
    for filename, artifact in artifacts.items():
        (tmp_path / filename).write_text(json.dumps(artifact, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        core_artifacts.validate_artifact(artifact, str(artifact['schema_ref']))
    result = verify_artifact_chain_manifest(artifacts['artifact_chain_manifest.json'], root=tmp_path)
    assert result['status'] == 'passed'
    assert result['checked_entries'] == [
        'intent_contract',
        'policy_decision',
        'execution_contract',
        'execution_ticket',
        'execution_receipt',
        'evidence_contract',
    ]



def test_wrapper_adds_demo_signature_trust_metadata_to_demo_lifecycle_chain() -> None:
    artifacts = wrapper.build_lifecycle_artifacts_v02(_demo_pipeline_data())
    ticket = artifacts['execution_ticket.json']

    assert ticket['signature']['mode'] == 'detached_demo_digest'
    assert ticket['signature']['binds_digest'] == artifact_descriptor(artifacts['execution_contract.json'])['digest']
    assert ticket['trust_decision']['trust_status'] == 'trusted'
    assert 'no_pki_ca_kms_or_key_store_in_govengine' in ticket['non_claims']


def test_wrapper_keeps_integrity_only_signature_outside_demo_runtime_mode() -> None:
    pipeline_data = _demo_pipeline_data()
    pipeline_data['settings']['runtime_mode'] = 'test'
    artifacts = wrapper.build_lifecycle_artifacts_v02(pipeline_data)

    assert artifacts['execution_ticket.json']['signature']['mode'] == 'not_signed_integrity_only'


def test_current_wrapper_lifecycle_uses_scoped_ticket_semantics() -> None:
    artifacts = wrapper.build_current_lifecycle_artifacts(_demo_pipeline_data())

    assert artifacts['execution_ticket.json']['schema_version'] == 'v0.3'
    assert artifacts['execution_ticket.json']['ticket_profile'] == 'scoped_execution_ticket'
    assert 'legacy_v0_1_descriptor' not in artifacts['policy_decision.v0.2.json']

def test_root_schema_fixture_copies_remain_in_parity_with_sclite_dependency() -> None:
    for schema_file in core_artifacts.SCHEMA_FILES.values():
        assert (core_artifacts.schema_dir() / schema_file).read_bytes() == (ROOT / 'schemas' / schema_file).read_bytes(), schema_file
    for proof_file in core_artifacts.PROOF_TRACE_FILES:
        assert (core_artifacts.examples_dir() / 'security-contract-proof' / proof_file).read_bytes() == (ROOT / 'examples' / 'security-contract-proof' / proof_file).read_bytes(), proof_file


def test_govengine_context_imports_without_ravenclaw_workspace(monkeypatch) -> None:
    monkeypatch.delenv('RAVENCLAW_WORKSPACE', raising=False)

    from govengine import GovEngineContext, ravenclaw_context

    context = ravenclaw_context(ROOT)
    assert isinstance(context, GovEngineContext)
    assert context.profile == 'ravenclaw'
    assert context.repo_root == ROOT
    assert context.paths.policy_file == ROOT / 'policy.yaml'


def test_ravenclaw_security_contract_repo_root_uses_govengine_context() -> None:
    assert wrapper.repo_root() == ROOT


def test_adapter_generated_execution_ticket_passes_runtime_gate() -> None:
    from executor import ExecutionEngine  # type: ignore

    pipeline_data = _demo_pipeline_data()
    artifacts = adapter.build_lifecycle_artifacts_v02(pipeline_data)
    ticket = artifacts['execution_ticket.json']
    contract = artifacts['execution_contract.json']

    assert ticket['approval']['status'] == 'approved_for_dry_run'

    engine = ExecutionEngine()
    engine.scope_domains = {'exact': ['example.com'], 'suffix': [], 'exclude_exact': [], 'exclude_suffix': []}
    result = engine.execute_approved_spec(
        pipeline_data['approved_execution_spec'],
        dry_run=True,
        execution_ticket=ticket,
        execution_contract=contract,
        require_execution_ticket=True,
    )

    assert result['execution_ticket_gate']['status'] == 'passed'
    assert result['execution_ticket_gate']['ticket_id'] == ticket['ticket_id']


def test_security_contract_layer_uses_govengine_sclite_adapter_directly() -> None:
    assert wrapper.build_execution_contract_v02 is adapter.build_execution_contract_v02
    assert wrapper.build_execution_ticket_v02 is adapter.build_execution_ticket_v02
    assert wrapper.LIFECYCLE_TRACE_FILES_V02 == adapter.LIFECYCLE_TRACE_FILES_V02


def test_wrapper_projects_compact_ooda_decisions_into_receipts_without_raw_telemetry() -> None:
    pipeline_data = _demo_pipeline_data()
    pipeline_data['engine']['control_decisions'] = [
        {
            'decision': 'cooldown',
            'reason_code': 'host_health_transport_noise',
            'interrupting': True,
            'cooldown_subject': str(Path.home() / 'private-host-label'),
            'observations': [
                {
                    'kind': 'before_step',
                    'severity': 'warning',
                    'subject': 'curl',
                    'detail': 'raw stderr and token should not appear',
                    'facts': {'step_index': 1, 'token': 'secret-token'},
                }
            ],
            'orientation': {
                'scope_ok': True,
                'policy_ok': True,
                'ticket_ok': True,
                'spec_ok': True,
                'host_health': 'transport_noise',
                'output_shape': 'expected',
                'operator_control': 'run',
                'budget_state': 'ok',
                'notes': ['private detail'],
            },
        }
    ]

    proof = wrapper.build_proof_trace_artifacts(pipeline_data)
    receipt = proof['execution_receipt.json']
    evidence = proof['evidence_bundle.json']
    summary = proof['evidence_summary.md']
    lifecycle = wrapper.build_lifecycle_artifacts_v02(pipeline_data)

    assert receipt['control_decision_count'] == 1
    decision = receipt['control_decisions'][0]
    assert decision['decision'] == 'cooldown'
    assert decision['step_index'] == 1
    assert decision['observation_kinds'] == ['before_step']
    assert 'observations' not in decision
    assert 'detail' not in str(decision)
    assert 'secret-token' not in json.dumps(proof, sort_keys=True)
    assert 'private detail' not in json.dumps(proof, sort_keys=True)
    assert evidence['governance_evidence']['ooda_control_evaluated'] is True
    assert 'OODA control decisions' in summary
    assert lifecycle['execution_receipt.v0.2.json']['control_decision_count'] == 1
    assert lifecycle['evidence_contract.json']['governance_evidence']['control_decision_count'] == 1
