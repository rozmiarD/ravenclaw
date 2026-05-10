from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROOF_OF_VALUE = ROOT / 'PROOF_OF_VALUE.md'


def _text() -> str:
    return PROOF_OF_VALUE.read_text(encoding='utf-8')


def test_proof_of_value_links_public_evidence_surfaces() -> None:
    text = _text()
    required = [
        'SECURITY_CONTRACT_LAYER.md',
        'examples/security-contract-proof/',
        'scripts/run_security_contract_validation.py',
        'schemas/security_contract_validation_receipt.v0.1.schema.json',
        'scripts/build_public_snapshot_manifest.py',
        'examples/replayable-truth-runtime/',
        'examples/scope-fidelity-report/',
    ]
    for item in required:
        assert item in text


def test_proof_of_value_preserves_non_claims() -> None:
    text = _text()
    required = [
        'does **not** currently claim',
        'live vulnerability discovery in the public fixtures',
        'readiness for every production deployment',
        'complete OpenClaw/MCP/A2A adapter ecosystem',
        'passing local tests replaces human authorization or legal scope review',
        'superior real-world outcomes by itself',
    ]
    for phrase in required:
        assert phrase in text


def test_proof_of_value_benchmark_dimensions_are_governance_first() -> None:
    text = _text()
    dimensions = [
        'Scope fidelity',
        'Policy decision clarity',
        'Execution spec accountability',
        'Dry-run/evidence separation',
        'Replayability',
        'Snapshot completeness',
        'Non-claim preservation',
    ]
    for dimension in dimensions:
        assert dimension in text
    assert 'number of discovered vulnerabilities' in text
