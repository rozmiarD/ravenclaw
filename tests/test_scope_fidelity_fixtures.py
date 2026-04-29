from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / 'scripts'
ENGINE_DIR = ROOT / 'engine'
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

import validate_scope_fidelity_fixtures as validator  # type: ignore
import security_contract_layer as scl  # type: ignore

FIXTURE_DIR = ROOT / 'examples' / 'scope-fidelity-report'


def test_scope_fidelity_fixtures_validate() -> None:
    validator.validate_fixture_dir(FIXTURE_DIR)


def test_scope_fidelity_fixtures_cover_expected_verdicts() -> None:
    cases = {
        'exact.json': 'pass',
        'cross_host_mismatch.json': 'fail',
        'ambiguous.json': 'review',
    }
    for filename, verdict in cases.items():
        report = json.loads((FIXTURE_DIR / filename).read_text(encoding='utf-8'))
        scl.validate_scope_fidelity_report(report, root=ROOT)
        assert report['verdict'] == verdict
        assert report['public_safety']['live_target_execution'] is False
        assert report['public_safety']['protocol_adapter_work'] is False


def test_scope_fidelity_fixture_cli() -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / 'validate_scope_fidelity_fixtures.py'), str(FIXTURE_DIR)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    assert 'scope_fidelity_fixtures_ok:' in proc.stdout
