from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / 'scripts'
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import run_security_contract_validation as runner  # type: ignore


def test_security_contract_validation_runner_lists_core_checks() -> None:
    ids = runner.list_check_ids(include_pytest=False)
    assert ids == [
        'fixture_validation',
        'demo_bundle_smoke',
        'assemble_public_snapshot',
        'snapshot_fixture_validation',
        'snapshot_residue_audit',
    ]


def test_security_contract_validation_runner_can_include_focused_pytest() -> None:
    ids = runner.list_check_ids(include_pytest=True)
    assert ids[-1] == 'focused_pytest'
    assert 'engine/tests/test_security_contract_fixtures.py' in runner.FOCUSED_PYTEST_TARGETS
    assert 'tests/test_public_snapshot_residue_audit.py' in runner.FOCUSED_PYTEST_TARGETS


def test_security_contract_validation_receipt_marks_public_safe_scope() -> None:
    check = runner.CheckReceipt(
        check_id='fixture_validation',
        description='fixture check',
        status='passed',
        command=['python', 'scripts/validate_security_contract_fixtures.py'],
        cwd_label='.',
        returncode=0,
        duration_seconds=0.01,
        stdout_excerpt='security_contract_fixtures_ok:...',
        stderr_excerpt='',
    )
    receipt = runner._build_receipt([check], include_pytest=False)
    assert receipt['artifact_type'] == 'security_contract_validation_receipt'
    assert receipt['status'] == 'passed'
    assert receipt['scope'] == {
        'mode': 'local_public_safe_validation',
        'live_target_execution': False,
        'protocol_adapter_work': False,
        'public_push': False,
    }
    assert receipt['checks_passed'] == ['fixture_validation']
    assert receipt['checks_failed'] == []


def test_security_contract_validation_runner_list_checks_cli() -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / 'run_security_contract_validation.py'), '--list-checks', '--include-pytest'],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    lines = proc.stdout.strip().splitlines()
    assert lines[0] == 'fixture_validation'
    assert lines[-1] == 'focused_pytest'
