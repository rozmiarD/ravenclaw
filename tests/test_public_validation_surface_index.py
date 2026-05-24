from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'list_public_validation_surfaces.py'
if str(SCRIPT.parent) not in sys.path:
    sys.path.insert(0, str(SCRIPT.parent))
if str(ROOT / 'engine') not in sys.path:
    sys.path.insert(0, str(ROOT / 'engine'))

import list_public_validation_surfaces as surface_index  # type: ignore
import security_contract_layer as scl  # type: ignore


def _json_index() -> dict:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), '--format', 'json', '--check'],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout)


def test_public_validation_surface_index_lists_core_surfaces() -> None:
    index = _json_index()
    assert index['artifact_type'] == 'public_validation_surface_index'
    assert index['schema_version'] == 'v0.1'
    assert index['generated_at']
    ids = {surface['surface_id'] for surface in index['surfaces']}
    assert {
        'public_validation_surface_index',
        'public_install_validation',
        'ravenclaw_security_profile_boundary',
        'openclaw_readiness_contracts',
        'repo_pytest',
        'github_actions_pytest_matrix',
        'current_review_bundle_demo',
        'security_contract_validation_receipt',
        'replayable_truth_runtime_fixture',
        'scope_fidelity_fixture',
        'public_snapshot_residue_audit',
        'demo_bundle_smoke',
        'public_snapshot_manifest',
        'proof_of_value_scorecard',
    } <= ids
    assert 'security_contract_fixture' not in ids
    assert 'sclite_v02_lifecycle_chain' not in ids
    assert index['summary']['public_safe_surface_count'] == index['summary']['surface_count']


def test_public_validation_surface_index_boundaries_are_public_safe() -> None:
    index = _json_index()
    for surface in index['surfaces']:
        boundaries = surface['boundaries']
        assert boundaries['public_safe'] is True
        assert boundaries['dry_run_or_local_only'] is True
        assert boundaries['live_target_execution'] is False
        assert boundaries['protocol_adapter_work'] is False
        assert surface['purpose']
        assert surface['commands']


def test_public_validation_surface_index_matches_schema() -> None:
    index = _json_index()
    surface_index.validate_index_schema(index)


def test_public_validation_surface_index_schema_rejects_live_target_claim() -> None:
    index = surface_index.build_index()
    index['public_safety']['live_target_execution'] = True
    try:
        surface_index.validate_index_schema(index)
    except scl.JsonSchemaValidationError as exc:
        assert 'live_target_execution' in str(exc)
    else:  # pragma: no cover - assertion guard
        raise AssertionError('public validation surfaces must not authorize live target execution')


def test_public_validation_surface_index_markdown_is_reader_facing() -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    assert '# Public Validation Surface Index' in proc.stdout
    assert 'does not claim' in proc.stdout
    assert 'Security Contract validation receipt' in proc.stdout
