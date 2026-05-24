from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'references' / 'carrier-readiness-packet-template.md'
CHECKLIST = ROOT / 'references' / 'carrier-readiness-checklist.md'
DOCS_MAP = ROOT / 'DOCS_MAP.md'
SECURITY_CONTRACT_LAYER = ROOT / 'SECURITY_CONTRACT_LAYER.md'
PUBLIC_STATUS = ROOT / 'PUBLIC_STATUS.md'


def _text() -> str:
    return TEMPLATE.read_text(encoding='utf-8')


def test_carrier_readiness_packet_template_preserves_non_implementation_boundary() -> None:
    text = _text()
    required = [
        'Template for future carrier proposals',
        'not** an adapter implementation',
        'does **not** authorize OpenClaw, MCP, A2A',
        'live target execution',
        'offensive tooling',
        'production-readiness claims',
        'live vulnerability discovery',
        'bypass Ravenclaw policy/auditor/execution-engine authority',
    ]
    for phrase in required:
        assert phrase in text


def test_carrier_readiness_packet_template_contains_required_packet_fields() -> None:
    text = _text()
    required_fields = [
        'Packet ID',
        'Reviewer checklist owner',
        'Target carrier',
        'Proposed mode',
        'Explicit non-goals',
        'Scope UX',
        'Secrets and redaction',
        'Command authority boundary',
        'Contracts consumed and emitted',
        'Policy and tool allowlists',
        'Dry-run/live truth and evidence provenance',
        'Replayability and validation commands',
        'Rollback and stop conditions',
        'Public/private output boundary',
        'Reviewer checklist',
    ]
    for field in required_fields:
        assert field in text


def test_carrier_readiness_packet_template_requires_contract_inventory() -> None:
    text = _text()
    required_contracts = [
        'IntentContract',
        'PolicyDecision',
        'ExecutionContract',
        'ExecutionTicket',
        'ExecutionReceipt',
        'EvidenceContract',
        'Validation receipt',
        'Public snapshot manifest',
        'Proof-of-value scorecard',
    ]
    for contract in required_contracts:
        assert contract in text


def test_carrier_readiness_packet_template_requires_validation_and_stop_conditions() -> None:
    text = _text()
    assert 'python scripts/run_security_contract_validation.py --include-pytest' in text
    assert 'python scripts/run_security_contract_validation.py --include-pytest --include-github-actions-matrix' in text
    required_stop_conditions = [
        'scope ambiguity',
        'missing policy decision',
        'missing scoped execution ticket or ticket/contract binding',
        'unredacted secret/operator state risk',
        'command authority ambiguity',
        'dry-run/live truth ambiguity',
        'channel leakage risk',
        'budget/risk stop-loss trigger',
    ]
    for condition in required_stop_conditions:
        assert condition in text


def test_carrier_readiness_packet_template_is_linked_from_core_docs() -> None:
    rel = 'references/carrier-readiness-packet-template.md'
    assert rel in CHECKLIST.read_text(encoding='utf-8')
    assert rel in DOCS_MAP.read_text(encoding='utf-8')
    assert rel in SECURITY_CONTRACT_LAYER.read_text(encoding='utf-8')
    assert rel in PUBLIC_STATUS.read_text(encoding='utf-8')


def test_carrier_readiness_packet_template_is_included_in_public_snapshot(tmp_path: Path) -> None:
    out = tmp_path / 'public-snapshot'
    subprocess.run(
        [str(ROOT / 'scripts' / 'assemble_public_snapshot.sh'), str(out)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    copied = out / 'references' / 'carrier-readiness-packet-template.md'
    assert copied.exists()
    assert 'Template for future carrier proposals' in copied.read_text(encoding='utf-8')
