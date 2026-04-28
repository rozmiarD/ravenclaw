from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT_SCRIPT = ROOT / 'scripts' / 'audit_public_snapshot_residue.py'


def _finding_checks(snapshot: Path) -> set[str]:
    sys.path.insert(0, str(ROOT / 'scripts'))
    import audit_public_snapshot_residue as audit  # type: ignore

    return {finding.check for finding in audit.audit_snapshot(snapshot)}


def test_public_snapshot_residue_audit_passes_on_assembled_snapshot(tmp_path: Path) -> None:
    out = tmp_path / 'public-snapshot'
    subprocess.run(
        [str(ROOT / 'scripts' / 'assemble_public_snapshot.sh'), str(out)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=True,
    )

    proc = subprocess.run(
        [sys.executable, str(AUDIT_SCRIPT), str(out)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    assert 'public_snapshot_residue_ok:' in proc.stdout


def test_public_snapshot_residue_audit_rejects_private_residue(tmp_path: Path) -> None:
    snapshot = tmp_path / 'snapshot'
    (snapshot / 'memory').mkdir(parents=True)
    (snapshot / 'memory' / 'private.md').write_text('private note\n', encoding='utf-8')
    (snapshot / 'README.md').write_text('leaked ' + '/home/' + 'privateuser/.openclaw/workspace path\n', encoding='utf-8')

    checks = _finding_checks(snapshot)
    assert 'forbidden_path' in checks
    assert 'absolute_home_path' in checks
