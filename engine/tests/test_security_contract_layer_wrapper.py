from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINE_DIR = ROOT / 'engine'
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

import security_contract_layer as wrapper  # type: ignore
import scl_ravenclaw_adapter as adapter  # type: ignore
from sclite import artifacts as core_artifacts


def test_engine_security_contract_layer_delegates_generic_helpers_to_scl() -> None:
    assert wrapper.validate_public_proof_trace_artifacts is core_artifacts.validate_public_proof_trace_artifacts
    assert wrapper.assert_public_proof_trace_artifacts is core_artifacts.assert_public_proof_trace_artifacts
    assert wrapper.build_execution_receipt_artifact is core_artifacts.build_execution_receipt_artifact
    assert wrapper.build_evidence_bundle_artifact is core_artifacts.build_evidence_bundle_artifact
    assert wrapper.proof_trace_manifest is core_artifacts.proof_trace_manifest


def test_engine_security_contract_layer_uses_ravenclaw_adapter_for_proof_trace() -> None:
    assert wrapper.build_proof_trace_artifacts is adapter.build_proof_trace_artifacts
    assert wrapper.build_policy_decision_artifact is adapter.build_policy_decision_artifact


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


def test_root_schema_fixture_copies_remain_in_parity_with_sclite_dependency() -> None:
    for schema_file in core_artifacts.SCHEMA_FILES.values():
        assert (core_artifacts.schema_dir() / schema_file).read_bytes() == (ROOT / 'schemas' / schema_file).read_bytes(), schema_file
    for proof_file in core_artifacts.PROOF_TRACE_FILES:
        assert (core_artifacts.examples_dir() / 'security-contract-proof' / proof_file).read_bytes() == (ROOT / 'examples' / 'security-contract-proof' / proof_file).read_bytes(), proof_file
