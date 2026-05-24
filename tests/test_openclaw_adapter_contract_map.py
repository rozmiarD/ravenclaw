from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / 'references' / 'openclaw-adapter-contract-map.md'
DOCS_MAP = ROOT / 'DOCS_MAP.md'
SECURITY_CONTRACT_LAYER = ROOT / 'SECURITY_CONTRACT_LAYER.md'
PUBLIC_STATUS = ROOT / 'PUBLIC_STATUS.md'


def _map_text() -> str:
    return MAP.read_text(encoding='utf-8')


def test_openclaw_adapter_contract_map_preserves_non_implementation_boundary() -> None:
    text = _map_text()
    required = [
        'Adapter-prep reference only',
        'not an adapter implementation',
        'does **not**',
        'implement an OpenClaw Skill, plugin, node integration, or runtime hook',
        'start MCP or A2A adapter work',
        'authorize live target execution',
        'claim live vulnerability discovery',
        'replace Ravenclaw Runtime as the reference/proof implementation',
    ]
    for phrase in required:
        assert phrase in text


def test_openclaw_adapter_contract_map_covers_canonical_security_contract_trace() -> None:
    text = _map_text()
    required_artifacts = [
        'intent-contract scope fields',
        'PolicyDecision',
        'ExecutionContract',
        'ExecutionTicket',
        'ExecutionReceipt',
        'EvidenceContract',
        'scripts/run_security_contract_validation.py',
        'scripts/build_public_snapshot_manifest.py',
        'scripts/build_proof_of_value_scorecard.py',
    ]
    for artifact in required_artifacts:
        assert artifact in text


def test_openclaw_adapter_contract_map_keeps_carrier_order() -> None:
    text = _map_text()
    assert 'OpenClaw remains the recommended first carrier' in text
    assert 'MCP should remain later and policy-gated' in text
    assert 'A2A should remain last or example-first' in text


def test_openclaw_adapter_contract_map_is_linked_from_navigation_docs() -> None:
    rel = 'references/openclaw-adapter-contract-map.md'
    assert rel in DOCS_MAP.read_text(encoding='utf-8')
    assert rel in SECURITY_CONTRACT_LAYER.read_text(encoding='utf-8')
    assert rel in PUBLIC_STATUS.read_text(encoding='utf-8')


def test_openclaw_adapter_contract_map_is_included_in_public_snapshot(tmp_path: Path) -> None:
    out = tmp_path / 'public-snapshot'
    subprocess.run(
        [str(ROOT / 'scripts' / 'assemble_public_snapshot.sh'), str(out)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    copied = out / 'references' / 'openclaw-adapter-contract-map.md'
    assert copied.exists()
    assert 'Adapter-prep reference only' in copied.read_text(encoding='utf-8')
