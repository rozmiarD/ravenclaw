from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / 'REVIEWER_VALIDATION_GUIDE.md'


def _guide_text() -> str:
    return GUIDE.read_text(encoding='utf-8')


def test_reviewer_validation_guide_links_core_validation_surfaces() -> None:
    text = _guide_text()
    assert 'pytest -q' in text
    assert 'python scripts/list_public_validation_surfaces.py --format json --check' in text
    assert 'python scripts/build_public_snapshot_manifest.py . --check' in text
    assert 'python scripts/run_security_contract_validation.py --include-pytest' in text
    assert 'python scripts/run_security_contract_validation.py --include-pytest --include-github-actions-matrix' in text


def test_reviewer_validation_guide_preserves_public_safe_non_claims() -> None:
    text = _guide_text()
    required_phrases = [
        'does **not** authorize live target execution',
        'protocol adapter work',
        'production-readiness claims',
        'not live vulnerability findings',
        'If a future change weakens these non-claims, treat it as a publication-safety regression.',
    ]
    for phrase in required_phrases:
        assert phrase in text


def test_reviewer_validation_guide_is_included_in_public_snapshot(tmp_path: Path) -> None:
    out = tmp_path / 'public-snapshot'
    subprocess.run(
        [str(ROOT / 'scripts' / 'assemble_public_snapshot.sh'), str(out)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    assert (out / 'REVIEWER_VALIDATION_GUIDE.md').exists()
    assert 'Public Snapshot Manifest' in (out / 'REVIEWER_VALIDATION_GUIDE.md').read_text(encoding='utf-8')
