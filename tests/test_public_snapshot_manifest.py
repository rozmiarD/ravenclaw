from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'build_public_snapshot_manifest.py'
if str(SCRIPT.parent) not in sys.path:
    sys.path.insert(0, str(SCRIPT.parent))
if str(ROOT / 'engine') not in sys.path:
    sys.path.insert(0, str(ROOT / 'engine'))

import build_public_snapshot_manifest as manifest_builder  # type: ignore
import security_contract_layer as scl  # type: ignore


def _assemble_snapshot(tmp_path: Path) -> Path:
    out = tmp_path / 'public-snapshot'
    subprocess.run(
        [str(ROOT / 'scripts' / 'assemble_public_snapshot.sh'), str(out)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    return out


def _manifest(snapshot: Path) -> dict:
    proc = subprocess.run(
        [sys.executable, str(snapshot / 'scripts' / 'build_public_snapshot_manifest.py'), '.', '--check'],
        cwd=str(snapshot),
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout)


def test_public_snapshot_manifest_maps_validation_surfaces_to_present_paths(tmp_path: Path) -> None:
    snapshot = _assemble_snapshot(tmp_path)
    manifest = _manifest(snapshot)

    assert manifest['artifact_type'] == 'public_snapshot_manifest'
    assert manifest['schema_version'] == 'v0.1'
    assert manifest['snapshot_name']
    assert manifest['summary']['file_count'] > 0
    paths = {file['path'] for file in manifest['files']}
    assert {
        'examples/security-contract-proof',
        'scripts/run_security_contract_validation.py',
        'scripts/list_public_validation_surfaces.py',
        'scripts/build_public_snapshot_manifest.py',
    } <= paths

    for file in manifest['files']:
        assert file['path']
        assert file['public_safe'] is True
    assert manifest['public_safety']['live_target_execution'] is False
    assert manifest['public_safety']['protocol_adapter_work'] is False


def test_public_snapshot_manifest_matches_schema(tmp_path: Path) -> None:
    snapshot = _assemble_snapshot(tmp_path)
    manifest = _manifest(snapshot)
    manifest_builder.validate_manifest_schema(manifest)


def test_public_snapshot_manifest_check_fails_when_surface_path_missing(tmp_path: Path) -> None:
    snapshot = _assemble_snapshot(tmp_path)
    (snapshot / 'DEMO.md').unlink()

    proc = subprocess.run(
        [sys.executable, str(snapshot / 'scripts' / 'build_public_snapshot_manifest.py'), '.', '--check'],
        cwd=str(snapshot),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 1
    manifest = json.loads(proc.stdout)
    assert proc.returncode == 1


def test_public_snapshot_manifest_schema_rejects_unsafe_boundary(tmp_path: Path) -> None:
    snapshot = _assemble_snapshot(tmp_path)
    manifest = _manifest(snapshot)
    manifest['public_safety']['protocol_adapter_work'] = True
    try:
        manifest_builder.validate_manifest_schema(manifest)
    except scl.JsonSchemaValidationError as exc:
        assert 'protocol_adapter_work' in str(exc)
    else:  # pragma: no cover - assertion guard
        raise AssertionError('public snapshot manifest must not authorize protocol adapter work')


def test_public_snapshot_manifest_markdown_is_reviewer_facing(tmp_path: Path) -> None:
    snapshot = _assemble_snapshot(tmp_path)
    proc = subprocess.run(
        [sys.executable, str(snapshot / 'scripts' / 'build_public_snapshot_manifest.py'), '.', '--format', 'markdown', '--check'],
        cwd=str(snapshot),
        capture_output=True,
        text=True,
        check=True,
    )
    assert '# Public Snapshot Manifest' in proc.stdout
    assert 'missing_paths: `0`' in proc.stdout
    assert '`scripts/list_public_validation_surfaces.py`' in proc.stdout


def test_public_snapshot_manifest_reviewer_report_is_publish_ready(tmp_path: Path) -> None:
    snapshot = _assemble_snapshot(tmp_path)
    proc = subprocess.run(
        [sys.executable, str(snapshot / 'scripts' / 'build_public_snapshot_manifest.py'), '.', '--format', 'reviewer-report', '--check'],
        cwd=str(snapshot),
        capture_output=True,
        text=True,
        check=True,
    )
    assert '# Ravenclaw Public Snapshot Reviewer Report' in proc.stdout
    assert 'Result: `PASS`' in proc.stdout
    assert '| File | Public safe | Kind |' in proc.stdout
    assert 'no live target execution authorization' in proc.stdout
