from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINE_DIR = ROOT / 'engine'
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

import security_contract_layer as wrapper  # type: ignore
import scl_ravenclaw_adapter as adapter  # type: ignore
from sclite import artifacts as core_artifacts
from sclite.integrity import verify_artifact_chain_manifest


def test_engine_security_contract_layer_delegates_generic_helpers_to_scl() -> None:
    assert wrapper.validate_public_proof_trace_artifacts is core_artifacts.validate_public_proof_trace_artifacts
    assert wrapper.assert_public_proof_trace_artifacts is core_artifacts.assert_public_proof_trace_artifacts
    assert wrapper.build_execution_receipt_artifact is core_artifacts.build_execution_receipt_artifact
    assert wrapper.build_evidence_bundle_artifact is core_artifacts.build_evidence_bundle_artifact
    assert wrapper.proof_trace_manifest is core_artifacts.proof_trace_manifest


def test_engine_security_contract_layer_uses_ravenclaw_adapter_for_proof_trace() -> None:
    assert wrapper.build_proof_trace_artifacts is adapter.build_proof_trace_artifacts
    assert wrapper.build_policy_decision_artifact is adapter.build_policy_decision_artifact
    assert wrapper.build_lifecycle_artifacts_v02 is adapter.build_lifecycle_artifacts_v02


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
