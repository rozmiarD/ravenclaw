from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKLIST = ROOT / 'references' / 'carrier-readiness-checklist.md'
DOCS_MAP = ROOT / 'DOCS_MAP.md'
SECURITY_CONTRACT_LAYER = ROOT / 'SECURITY_CONTRACT_LAYER.md'
PUBLIC_STATUS = ROOT / 'PUBLIC_STATUS.md'


def _text() -> str:
    return CHECKLIST.read_text(encoding='utf-8')


def test_carrier_readiness_checklist_preserves_non_implementation_boundary() -> None:
    text = _text()
    required = [
        'Docs/contracts-only readiness checklist',
        'not** an implementation plan for an adapter',
        'implement OpenClaw, MCP, A2A, or any protocol adapter',
        'authorize live target execution',
        'claim production deployment readiness',
        'claim live vulnerability discovery',
        'permit private operator state, credentials, memory, raw logs, or unredacted runtime artifacts',
    ]
    for phrase in required:
        assert phrase in text


def test_carrier_readiness_checklist_keeps_carrier_order() -> None:
    text = _text()
    assert 'OpenClaw first' in text
    assert 'MCP later' in text
    assert 'A2A last or example-first' in text
    assert 'Do not pivot protocol-first into MCP or A2A' in text


def test_carrier_readiness_checklist_covers_required_gates() -> None:
    text = _text()
    required_gates = [
        'Scope UX',
        'Policy decision preservation',
        'Command authority boundary',
        'Prepared/approved spec separation',
        'Secrets and redaction',
        'Tool allowlists',
        'Dry-run/live truth',
        'Evidence provenance',
        'Replayability',
        'Channel leakage review',
        'Stop-loss and escalation',
        'Public non-claims',
    ]
    for gate in required_gates:
        assert gate in text


def test_carrier_readiness_checklist_requires_implementation_entry_packet() -> None:
    text = _text()
    required_items = [
        'target carrier and mode',
        'explicit non-goals',
        'scope UX sketch',
        'secret/redaction handling sketch',
        'command authority boundary statement',
        'contract artifacts consumed and emitted',
        'validation commands',
        'rollback/stop conditions',
        'public/private output boundary',
        'reviewer checklist owner',
    ]
    for item in required_items:
        assert item in text


def test_carrier_readiness_checklist_is_linked_from_navigation_docs() -> None:
    rel = 'references/carrier-readiness-checklist.md'
    assert rel in DOCS_MAP.read_text(encoding='utf-8')
    assert rel in SECURITY_CONTRACT_LAYER.read_text(encoding='utf-8')
    assert rel in PUBLIC_STATUS.read_text(encoding='utf-8')


def test_carrier_readiness_checklist_is_included_in_public_snapshot(tmp_path: Path) -> None:
    out = tmp_path / 'public-snapshot'
    subprocess.run(
        [str(ROOT / 'scripts' / 'assemble_public_snapshot.sh'), str(out)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    copied = out / 'references' / 'carrier-readiness-checklist.md'
    assert copied.exists()
    assert 'Docs/contracts-only readiness checklist' in copied.read_text(encoding='utf-8')
