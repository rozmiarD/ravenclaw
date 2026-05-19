from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / 'scripts'
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import run_pytest_slice as pytest_slices  # type: ignore
import run_security_contract_validation as runner  # type: ignore


def test_security_contract_validation_runner_lists_core_checks() -> None:
    ids = runner.list_check_ids(include_pytest=False)
    assert ids == [
        'fixture_validation',
        'public_validation_surface_index',
        'demo_bundle_smoke',
        'assemble_public_snapshot',
        'demo_scenario_package_chain',
        'snapshot_fixture_validation',
        'snapshot_residue_audit',
        'snapshot_replayable_truth_fixture',
        'snapshot_scope_fidelity_fixture',
        'snapshot_manifest',
        'proof_of_value_scorecard',
        'proof_of_value_scorecard_fixture',
    ]


def test_security_contract_validation_runner_can_include_focused_pytest() -> None:
    ids = runner.list_check_ids(include_pytest=True)
    assert ids[-1] == 'focused_pytest'
    assert 'tests/test_public_snapshot_manifest.py' in runner.FOCUSED_PYTEST_TARGETS
    assert 'tests/test_demo_scenario.py' in runner.FOCUSED_PYTEST_TARGETS
    assert 'tests/test_reviewer_validation_guide.py' in runner.FOCUSED_PYTEST_TARGETS
    assert 'tests/test_proof_of_value_framing.py' in runner.FOCUSED_PYTEST_TARGETS
    assert 'tests/test_proof_of_value_scorecard.py' in runner.FOCUSED_PYTEST_TARGETS
    assert 'tests/test_proof_of_value_scorecard_fixture.py' in runner.FOCUSED_PYTEST_TARGETS
    assert 'engine/tests/test_security_contract_fixtures.py' in runner.FOCUSED_PYTEST_TARGETS
    assert 'tests/test_public_snapshot_residue_audit.py' in runner.FOCUSED_PYTEST_TARGETS
    assert 'tests/test_replayable_truth_fixture.py' in runner.FOCUSED_PYTEST_TARGETS


def test_security_contract_validation_runner_can_skip_demo_runtime_checks() -> None:
    ids = runner.list_check_ids(include_pytest=True, include_demo_runtime=False)
    assert 'demo_bundle_smoke' not in ids
    assert 'demo_scenario_package_chain' not in ids
    assert ids[-1] == 'focused_pytest'


def test_focused_pytest_targets_can_skip_demo_runtime_tests() -> None:
    targets = runner._focused_pytest_targets(include_demo_runtime=False)
    assert 'engine/tests/test_public_demo_bundle.py' not in targets
    assert 'tests/test_demo_scenario.py' not in targets
    assert 'tests/test_public_snapshot_manifest.py' in targets


def test_security_contract_validation_runner_can_include_github_actions_matrix() -> None:
    ids = runner.list_check_ids(include_pytest=True, include_github_actions_matrix=True)
    assert ids[-2:] == ['focused_pytest', 'github_actions_pytest_matrix']
    assert runner.GITHUB_ACTIONS_PYTEST_SLICES == list(pytest_slices.SLICE_ORDER)
    workflow = (ROOT / '.github/workflows/pytest.yml').read_text(encoding='utf-8')
    for slice_name in runner.GITHUB_ACTIONS_PYTEST_SLICES:
        assert f'- {slice_name}' in workflow


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
    assert receipt['schema_version'] == 'v0.1'
    assert receipt['schema_ref'] == 'schemas/security_contract_validation_receipt.v0.1.schema.json'
    assert receipt['status'] == 'passed'
    assert receipt['scope'] == {
        'mode': 'local_public_safe_validation',
        'live_target_execution': False,
        'protocol_adapter_work': False,
        'public_push': False,
    }
    assert receipt['checks_passed'] == ['fixture_validation']
    assert receipt['checks_failed'] == []
    runner.validate_receipt_schema(receipt)



def test_security_contract_validation_receipt_schema_rejects_live_target_claim() -> None:
    check = runner.CheckReceipt(
        check_id='fixture_validation',
        description='fixture check',
        status='passed',
        command=['python', 'scripts/validate_security_contract_fixtures.py'],
        cwd_label='.',
        returncode=0,
        duration_seconds=0.01,
        stdout_excerpt='',
        stderr_excerpt='',
    )
    receipt = runner._build_receipt([check], include_pytest=False)
    receipt['scope']['live_target_execution'] = True
    try:
        runner.validate_receipt_schema(receipt)
    except runner.ReceiptSchemaValidationError as exc:
        assert 'live_target_execution' in str(exc)
    else:  # pragma: no cover - assertion guard
        raise AssertionError('receipt schema should reject live target execution claims')



def test_security_contract_validation_receipt_schema_file_is_loadable() -> None:
    schema = json.loads((ROOT / runner.RECEIPT_SCHEMA_REF).read_text(encoding='utf-8'))
    assert schema['properties']['artifact_type']['const'] == runner.RECEIPT_ARTIFACT_TYPE
    assert schema['properties']['schema_version']['const'] == runner.RECEIPT_SCHEMA_VERSION
    assert schema['properties']['schema_ref']['const'] == runner.RECEIPT_SCHEMA_REF



def test_security_contract_validation_runner_list_checks_cli() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS_DIR / 'run_security_contract_validation.py'),
            '--list-checks',
            '--include-pytest',
            '--include-github-actions-matrix',
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    lines = proc.stdout.strip().splitlines()
    assert lines[0] == 'fixture_validation'
    assert lines[-2:] == ['focused_pytest', 'github_actions_pytest_matrix']


def test_security_contract_validation_runner_structural_list_checks_cli() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS_DIR / 'run_security_contract_validation.py'),
            '--list-checks',
            '--include-pytest',
            '--structural-only',
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    lines = proc.stdout.strip().splitlines()
    assert 'demo_bundle_smoke' not in lines
    assert 'demo_scenario_package_chain' not in lines
    assert lines[-1] == 'focused_pytest'


def test_security_contract_validation_runner_rejects_matrix_without_demo_runtime() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS_DIR / 'run_security_contract_validation.py'),
            '--list-checks',
            '--include-github-actions-matrix',
            '--no-demo-runtime',
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    assert 'requires demo runtime checks' in proc.stderr
