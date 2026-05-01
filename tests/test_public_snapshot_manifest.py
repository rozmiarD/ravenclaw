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
    assert manifest['schema_ref'] == 'schemas/public_snapshot_manifest.v0.1.schema.json'
    assert manifest['summary']['missing_path_count'] == 0
    ids = {surface['id'] for surface in manifest['surfaces']}
    assert {
        'security_contract_fixture',
        'security_contract_validation_receipt',
        'public_validation_surface_index',
        'public_snapshot_manifest',
    } <= ids

    for surface in manifest['surfaces']:
        assert surface['claim']
        assert surface['non_claim']
        assert surface['boundaries']['live_target_execution'] is False
        assert surface['boundaries']['protocol_adapter_work'] is False
        assert all(path['present'] for path in surface['paths'])


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
    assert 'DEMO.md' in manifest['summary'] or manifest['summary']['missing_path_count'] > 0


def test_public_snapshot_manifest_schema_rejects_unsafe_boundary(tmp_path: Path) -> None:
    snapshot = _assemble_snapshot(tmp_path)
    manifest = _manifest(snapshot)
    manifest['surfaces'][0]['boundaries']['protocol_adapter_work'] = True
    try:
        manifest_builder.validate_manifest_schema(manifest)
    except scl.JsonSchemaValidationError as exc:
        assert 'protocol_adapter_work' in str(exc)
    else:  # pragma: no cover - assertion guard
        raise AssertionError('public snapshot manifest must not authorize protocol adapter work')
