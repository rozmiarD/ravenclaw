from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'list_public_validation_surfaces.py'


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
    ids = {surface['id'] for surface in index['surfaces']}
    assert {
        'repo_pytest',
        'github_actions_pytest_matrix',
        'security_contract_fixture',
        'security_contract_validation_receipt',
        'replayable_truth_runtime_fixture',
        'scope_fidelity_fixture',
        'public_snapshot_residue_audit',
        'demo_bundle_smoke',
    } <= ids
    assert index['summary']['missing_path_count'] == 0


def test_public_validation_surface_index_boundaries_are_public_safe() -> None:
    index = _json_index()
    for surface in index['surfaces']:
        boundaries = surface['boundaries']
        assert boundaries['public_safe'] is True
        assert boundaries['dry_run_or_local_only'] is True
        assert boundaries['live_target_execution'] is False
        assert boundaries['protocol_adapter_work'] is False
        assert surface['claim']
        assert surface['non_claim']


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
