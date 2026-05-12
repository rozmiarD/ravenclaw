from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Mapping, Sequence

from sclite.validation import (  # noqa: F401
    CheckReceipt,
    RECEIPT_ARTIFACT_TYPE,
    RECEIPT_SCHEMA_REF,
    RECEIPT_SCHEMA_VERSION,
    ReceiptSchemaValidationError,
    _print_markdown,
    build_validation_receipt,
    validate_receipt_schema,
)


FOCUSED_PYTEST_TARGETS = [
    'engine/tests/test_security_contract_fixtures.py',
    'engine/tests/test_public_demo_bundle.py',
    'engine/tests/test_security_contract_layer_schemas.py',
    'tests/test_public_snapshot_security_contract_fixtures.py',
    'tests/test_public_snapshot_residue_audit.py',
    'tests/test_replayable_truth_fixture.py',
]


class ValidationCheck:
    def __init__(self, check_id: str, description: str, command: List[str], cwd: Path, env: Mapping[str, str] | None = None) -> None:
        self.check_id = check_id
        self.description = description
        self.command = command
        self.cwd = cwd
        self.env = env


def repo_root() -> Path:
    from paths import configured_workspace  # type: ignore

    return configured_workspace(Path(__file__).resolve().parents[1])


def _excerpt(text: str, limit: int = 1600) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit] + '\n...[truncated]'


def _workspace_label(cwd: Path) -> str:
    root = repo_root()
    try:
        return cwd.resolve().relative_to(root.resolve()).as_posix() or '.'
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
        'fixture_validation',
        'Validate committed Security Contract proof fixtures against schemas, invariants, and clean-fixture rules.',
        [sys.executable, 'scripts/validate_security_contract_fixtures.py', 'examples/security-contract-proof'],
        repo_root(),
    )


def _demo_bundle_check(output_dir: Path, demo_repo: Path) -> ValidationCheck:
    return ValidationCheck(
        'demo_bundle_smoke',
        'Generate the public-safe Ravenclaw demo bundle from a disposable public snapshot and print its compact summary.',
        [
            'bash',
            '-lc',
            'scripts/assemble_public_snapshot.sh "$DEMO_REPO" >/dev/null && cd "$DEMO_REPO" && "$PYTHON_BIN" bin/demo-bundle --output-dir "$DEMO_OUTPUT" --print-summary',
        ],
        repo_root(),
        {'DEMO_REPO': str(demo_repo), 'DEMO_OUTPUT': str(output_dir), 'PYTHON_BIN': sys.executable},
    )


def _assemble_snapshot_check(snapshot_dir: Path) -> ValidationCheck:
    return ValidationCheck(
        'assemble_public_snapshot',
        'Assemble a temporary Ravenclaw public snapshot scaffold from the live workspace.',
        ['scripts/assemble_public_snapshot.sh', str(snapshot_dir)],
        repo_root(),
    )


def _snapshot_fixture_check(snapshot_dir: Path) -> ValidationCheck:
    return ValidationCheck(
        'snapshot_fixture_validation',
        'Validate the Security Contract proof fixtures copied into the assembled public snapshot.',
        [sys.executable, 'scripts/validate_security_contract_fixtures.py', 'examples/security-contract-proof'],
        snapshot_dir,
    )


def _snapshot_residue_check(snapshot_dir: Path) -> ValidationCheck:
    return ValidationCheck(
        'snapshot_residue_audit',
        'Audit the assembled public snapshot for private/local/generated residue blockers.',
        [sys.executable, 'scripts/audit_public_snapshot_residue.py', '.'],
        snapshot_dir,
    )


def _snapshot_replayable_truth_fixture_check(snapshot_dir: Path) -> ValidationCheck:
    return ValidationCheck(
        'snapshot_replayable_truth_fixture',
        'Validate the public-safe Replayable Truth Runtime fixture copied into the assembled public snapshot.',
        [sys.executable, 'scripts/validate_replayable_truth_fixture.py', 'examples/replayable-truth-runtime'],
        snapshot_dir,
    )


def _focused_pytest_check(pytest_repo: Path) -> ValidationCheck:
    return ValidationCheck(
        'focused_pytest',
        'Run focused Security Contract/public snapshot regression tests from a disposable public snapshot.',
        [
            'bash',
            '-lc',
            'scripts/assemble_public_snapshot.sh "$PYTEST_REPO" >/dev/null && cd "$PYTEST_REPO" && "$PYTHON_BIN" -m pytest -q "$@"',
            'focused_pytest',
            *FOCUSED_PYTEST_TARGETS,
        ],
        repo_root(),
        {'PYTEST_REPO': str(pytest_repo), 'PYTHON_BIN': sys.executable},
    )


def list_check_ids(include_pytest: bool) -> List[str]:
    ids = [
        'fixture_validation',
        'demo_bundle_smoke',
        'assemble_public_snapshot',
        'snapshot_fixture_validation',
        'snapshot_residue_audit',
        'snapshot_replayable_truth_fixture',
    ]
    if include_pytest:
        ids.append('focused_pytest')
    return ids


def _build_receipt(checks: Sequence[CheckReceipt], include_pytest: bool) -> Dict[str, object]:
    return build_validation_receipt(checks, checks_requested=list_check_ids(include_pytest))


def run_validation(include_pytest: bool) -> Dict[str, object]:
    receipts: List[CheckReceipt] = []
    with tempfile.TemporaryDirectory(prefix='ravenclaw-contract-validation.') as tmp:
        tmp_path = Path(tmp)
        snapshot_dir = tmp_path / 'public-snapshot'
        checks = [
            _fixture_check(),
            _demo_bundle_check(tmp_path / 'demo-output', tmp_path / 'demo-repo'),
            _assemble_snapshot_check(snapshot_dir),
            _snapshot_fixture_check(snapshot_dir),
            _snapshot_residue_check(snapshot_dir),
            _snapshot_replayable_truth_fixture_check(snapshot_dir),
        ]
        if include_pytest:
            checks.append(_focused_pytest_check(tmp_path / 'pytest-repo'))
        for check in checks:
            receipt = _run_check(check)
            receipts.append(receipt)
            if receipt.status != 'passed':
                break
    return _build_receipt(receipts, include_pytest=include_pytest)


def validation_receipt_main(argv: Sequence[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description='Run local/public-safe Ravenclaw Security Contract validation and emit a receipt.')
    parser.add_argument('--include-pytest', action='store_true', help='also run focused Security Contract/public snapshot pytest checks')
    parser.add_argument('--list-checks', action='store_true', help='print planned check identifiers and exit')
    parser.add_argument('--format', choices=['json', 'markdown'], default='json', help='receipt output format')
    args = parser.parse_args(argv)

    if args.list_checks:
        for check_id in list_check_ids(include_pytest=args.include_pytest):
            print(check_id)
        return 0

    receipt = run_validation(include_pytest=args.include_pytest)
    if args.format == 'markdown':
        _print_markdown(receipt)
    else:
        print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt['status'] == 'passed' else 1
