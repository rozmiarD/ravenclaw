#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
ENGINE_DIR = ROOT / 'engine'
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

import security_contract_layer as scl  # type: ignore
import run_pytest_slice as pytest_slices  # type: ignore

RECEIPT_ARTIFACT_TYPE = 'security_contract_validation_receipt'
RECEIPT_SCHEMA_VERSION = 'v0.1'
RECEIPT_SCHEMA_REF = 'schemas/security_contract_validation_receipt.v0.1.schema.json'
VALIDATED_TRACE = 'scope/input -> policy decision -> prepared execution spec -> approved execution spec -> dry-run execution receipt -> evidence summary'

GITHUB_ACTIONS_PYTEST_SLICES = list(pytest_slices.SLICE_ORDER)

FOCUSED_PYTEST_TARGETS = [
    'engine/tests/test_security_contract_fixtures.py',
    'engine/tests/test_public_demo_bundle.py',
    'engine/tests/test_security_contract_layer_schemas.py',
    'engine/tests/test_scope_fidelity_report.py',
    'tests/test_public_snapshot_security_contract_fixtures.py',
    'tests/test_public_snapshot_residue_audit.py',
    'tests/test_replayable_truth_fixture.py',
    'tests/test_scope_fidelity_fixtures.py',
    'tests/test_scope_fidelity_cli.py',
    'tests/test_public_validation_surface_index.py',
    'tests/test_public_snapshot_manifest.py',
]


@dataclass(frozen=True)
class ValidationCheck:
    check_id: str
    description: str
    command: List[str]
    cwd: Path
    env: Mapping[str, str] | None = None


@dataclass(frozen=True)
class CheckReceipt:
    check_id: str
    description: str
    status: str
    command: List[str]
    cwd_label: str
    returncode: int
    duration_seconds: float
    stdout_excerpt: str
    stderr_excerpt: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _excerpt(text: str, limit: int = 1600) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit] + '\n...[truncated]'


def _workspace_label(cwd: Path) -> str:
    try:
        return cwd.resolve().relative_to(ROOT.resolve()).as_posix() or '.'
    except ValueError:
        return '<temporary-directory>'


def _base_env(extra: Mapping[str, str] | None = None) -> Dict[str, str]:
    env = dict(os.environ)
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    if extra:
        env.update(extra)
    return env


def _run_check(check: ValidationCheck) -> CheckReceipt:
    started = time.monotonic()
    proc = subprocess.run(
        check.command,
        cwd=str(check.cwd),
        env=_base_env(check.env),
        text=True,
        capture_output=True,
    )
    duration = time.monotonic() - started
    return CheckReceipt(
        check_id=check.check_id,
        description=check.description,
        status='passed' if proc.returncode == 0 else 'failed',
        command=check.command,
        cwd_label=_workspace_label(check.cwd),
        returncode=proc.returncode,
        duration_seconds=round(duration, 3),
        stdout_excerpt=_excerpt(proc.stdout),
        stderr_excerpt=_excerpt(proc.stderr),
    )


def _fixture_check() -> ValidationCheck:
    return ValidationCheck(
        check_id='fixture_validation',
        description='Validate committed Security Contract proof fixtures against schemas, invariants, and sanitization rules.',
        command=[sys.executable, 'scripts/validate_security_contract_fixtures.py', 'examples/security-contract-proof'],
        cwd=ROOT,
    )


def _public_validation_surface_index_check() -> ValidationCheck:
    return ValidationCheck(
        check_id='public_validation_surface_index',
        description='Validate the public-facing index of local/public-safe validation surfaces.',
        command=[sys.executable, 'scripts/list_public_validation_surfaces.py', '--format', 'json', '--check'],
        cwd=ROOT,
    )


def _demo_bundle_check(output_dir: Path, demo_repo: Path) -> ValidationCheck:
    return ValidationCheck(
        check_id='demo_bundle_smoke',
        description='Generate the public-safe demo bundle from a disposable public snapshot and print its compact summary.',
        command=[
            'bash',
            '-lc',
            'scripts/assemble_public_snapshot.sh "$DEMO_REPO" >/dev/null && cd "$DEMO_REPO" && bin/demo-bundle --output-dir "$DEMO_OUTPUT" --print-summary',
        ],
        cwd=ROOT,
        env={'DEMO_REPO': str(demo_repo), 'DEMO_OUTPUT': str(output_dir)},
    )


def _assemble_snapshot_check(snapshot_dir: Path) -> ValidationCheck:
    return ValidationCheck(
        check_id='assemble_public_snapshot',
        description='Assemble a temporary public snapshot scaffold from the live workspace.',
        command=['scripts/assemble_public_snapshot.sh', str(snapshot_dir)],
        cwd=ROOT,
    )


def _snapshot_fixture_check(snapshot_dir: Path) -> ValidationCheck:
    return ValidationCheck(
        check_id='snapshot_fixture_validation',
        description='Validate the Security Contract proof fixtures copied into the assembled public snapshot.',
        command=[sys.executable, 'scripts/validate_security_contract_fixtures.py', 'examples/security-contract-proof'],
        cwd=snapshot_dir,
    )


def _snapshot_residue_check(snapshot_dir: Path) -> ValidationCheck:
    return ValidationCheck(
        check_id='snapshot_residue_audit',
        description='Audit the assembled public snapshot for private/local/generated residue blockers.',
        command=[sys.executable, 'scripts/audit_public_snapshot_residue.py', '.'],
        cwd=snapshot_dir,
    )


def _snapshot_replayable_truth_fixture_check(snapshot_dir: Path) -> ValidationCheck:
    return ValidationCheck(
        check_id='snapshot_replayable_truth_fixture',
        description='Validate the public-safe Replayable Truth Runtime fixture copied into the assembled public snapshot.',
        command=[sys.executable, 'scripts/validate_replayable_truth_fixture.py', 'examples/replayable-truth-runtime'],
        cwd=snapshot_dir,
    )


def _snapshot_scope_fidelity_fixture_check(snapshot_dir: Path) -> ValidationCheck:
    return ValidationCheck(
        check_id='snapshot_scope_fidelity_fixture',
        description='Validate public-safe Scope Fidelity report fixtures copied into the assembled public snapshot.',
        command=[sys.executable, 'scripts/validate_scope_fidelity_fixtures.py', 'examples/scope-fidelity-report'],
        cwd=snapshot_dir,
    )


def _snapshot_manifest_check(snapshot_dir: Path) -> ValidationCheck:
    return ValidationCheck(
        check_id='snapshot_manifest',
        description='Build and validate the public snapshot manifest against copied validation-surface paths.',
        command=[sys.executable, 'scripts/build_public_snapshot_manifest.py', '.', '--check'],
        cwd=snapshot_dir,
    )


def _github_actions_pytest_matrix_check(matrix_repo: Path) -> ValidationCheck:
    return ValidationCheck(
        check_id='github_actions_pytest_matrix',
        description='Run the full GitHub Actions pytest slice matrix from a disposable public snapshot.',
        command=[
            'bash',
            '-lc',
            'scripts/assemble_public_snapshot.sh "$MATRIX_REPO" >/dev/null && cd "$MATRIX_REPO" && for slice in $MATRIX_SLICES; do echo "== $slice =="; python scripts/run_pytest_slice.py "$slice"; done',
        ],
        cwd=ROOT,
        env={'MATRIX_REPO': str(matrix_repo), 'MATRIX_SLICES': ' '.join(GITHUB_ACTIONS_PYTEST_SLICES)},
    )


def _focused_pytest_check(pytest_repo: Path) -> ValidationCheck:
    return ValidationCheck(
        check_id='focused_pytest',
        description='Run focused Security Contract/public snapshot regression tests from a disposable public snapshot.',
        command=[
            'bash',
            '-lc',
            'scripts/assemble_public_snapshot.sh "$PYTEST_REPO" >/dev/null && cd "$PYTEST_REPO" && python -m pytest -q "$@"',
            'focused_pytest',
            *FOCUSED_PYTEST_TARGETS,
        ],
        cwd=ROOT,
        env={'PYTEST_REPO': str(pytest_repo)},
    )


ReceiptSchemaValidationError = scl.JsonSchemaValidationError


def validate_receipt_schema(receipt: Mapping[str, Any]) -> None:
    scl.validate_schema_ref(RECEIPT_SCHEMA_REF, receipt, root=ROOT)


def list_check_ids(include_pytest: bool, include_github_actions_matrix: bool = False) -> List[str]:
    ids = [
        'fixture_validation',
        'public_validation_surface_index',
        'demo_bundle_smoke',
        'assemble_public_snapshot',
        'snapshot_fixture_validation',
        'snapshot_residue_audit',
        'snapshot_replayable_truth_fixture',
        'snapshot_scope_fidelity_fixture',
        'snapshot_manifest',
    ]
    if include_pytest:
        ids.append('focused_pytest')
    if include_github_actions_matrix:
        ids.append('github_actions_pytest_matrix')
    return ids


def _build_receipt(
    checks: Sequence[CheckReceipt],
    include_pytest: bool,
    include_github_actions_matrix: bool = False,
) -> Dict[str, Any]:
    failed = [check for check in checks if check.status != 'passed']
    receipt = {
        'artifact_type': RECEIPT_ARTIFACT_TYPE,
        'schema_version': RECEIPT_SCHEMA_VERSION,
        'schema_ref': RECEIPT_SCHEMA_REF,
        'generated_at': _utc_now(),
        'status': 'passed' if not failed else 'failed',
        'scope': {
            'mode': 'local_public_safe_validation',
            'live_target_execution': False,
            'protocol_adapter_work': False,
            'public_push': False,
        },
        'validated_trace': VALIDATED_TRACE,
        'checks_requested': list_check_ids(include_pytest, include_github_actions_matrix),
        'checks_passed': [check.check_id for check in checks if check.status == 'passed'],
        'checks_failed': [check.check_id for check in failed],
        'checks': [asdict(check) for check in checks],
        'summary': {
            'total': len(checks),
            'passed': len(checks) - len(failed),
            'failed': len(failed),
        },
    }
    validate_receipt_schema(receipt)
    return receipt


def _print_markdown(receipt: Mapping[str, Any]) -> None:
    print('# Security Contract Validation Receipt')
    print('')
    print(f"status: `{receipt['status']}`")
    print(f"generated_at: `{receipt['generated_at']}`")
    print(f"trace: `{receipt['validated_trace']}`")
    print('')
    print('## Checks')
    for check in receipt['checks']:
        marker = 'OK' if check['status'] == 'passed' else 'FAIL'
        print(f"- {marker} `{check['check_id']}` ({check['duration_seconds']}s)")
    if receipt['checks_failed']:
        print('')
        print('## Failed checks')
        for check in receipt['checks']:
            if check['status'] == 'failed':
                print(f"### {check['check_id']}")
                if check['stdout_excerpt']:
                    print('stdout:')
                    print('```text')
                    print(check['stdout_excerpt'])
                    print('```')
                if check['stderr_excerpt']:
                    print('stderr:')
                    print('```text')
                    print(check['stderr_excerpt'])
                    print('```')


def run_validation(include_pytest: bool, include_github_actions_matrix: bool = False) -> Dict[str, Any]:
    receipts: List[CheckReceipt] = []
    with tempfile.TemporaryDirectory(prefix='ravenclaw-contract-validation.') as tmp:
        tmp_path = Path(tmp)
        snapshot_dir = tmp_path / 'public-snapshot'
        checks = [
            _fixture_check(),
            _public_validation_surface_index_check(),
            _demo_bundle_check(tmp_path / 'demo-output', tmp_path / 'demo-repo'),
            _assemble_snapshot_check(snapshot_dir),
            _snapshot_fixture_check(snapshot_dir),
            _snapshot_residue_check(snapshot_dir),
            _snapshot_replayable_truth_fixture_check(snapshot_dir),
            _snapshot_scope_fidelity_fixture_check(snapshot_dir),
            _snapshot_manifest_check(snapshot_dir),
        ]
        if include_pytest:
            checks.append(_focused_pytest_check(tmp_path / 'pytest-repo'))
        if include_github_actions_matrix:
            checks.append(_github_actions_pytest_matrix_check(tmp_path / 'github-actions-pytest-repo'))

        for check in checks:
            receipt = _run_check(check)
            receipts.append(receipt)
            if receipt.status != 'passed':
                break
    return _build_receipt(
        receipts,
        include_pytest=include_pytest,
        include_github_actions_matrix=include_github_actions_matrix,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Run local/public-safe Ravenclaw Security Contract validation and emit a receipt.')
    parser.add_argument('--include-pytest', action='store_true', help='also run focused Security Contract/public snapshot pytest checks')
    parser.add_argument(
        '--include-github-actions-matrix',
        action='store_true',
        help='also run the full GitHub Actions pytest slice matrix from a disposable public snapshot',
    )
    parser.add_argument('--list-checks', action='store_true', help='print planned check identifiers and exit')
    parser.add_argument('--format', choices=['json', 'markdown'], default='json', help='receipt output format')
    args = parser.parse_args(argv)

    if args.list_checks:
        for check_id in list_check_ids(
            include_pytest=args.include_pytest,
            include_github_actions_matrix=args.include_github_actions_matrix,
        ):
            print(check_id)
        return 0

    receipt = run_validation(
        include_pytest=args.include_pytest,
        include_github_actions_matrix=args.include_github_actions_matrix,
    )
    if args.format == 'markdown':
        _print_markdown(receipt)
    else:
        print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
