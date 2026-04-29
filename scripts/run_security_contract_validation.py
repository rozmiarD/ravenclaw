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
RECEIPT_ARTIFACT_TYPE = 'security_contract_validation_receipt'
RECEIPT_SCHEMA_VERSION = 'v0.1'
RECEIPT_SCHEMA_REF = 'schemas/security_contract_validation_receipt.v0.1.schema.json'
VALIDATED_TRACE = 'scope/input -> policy decision -> prepared execution spec -> approved execution spec -> dry-run execution receipt -> evidence summary'

FOCUSED_PYTEST_TARGETS = [
    'engine/tests/test_security_contract_fixtures.py',
    'engine/tests/test_public_demo_bundle.py',
    'engine/tests/test_security_contract_layer_schemas.py',
    'tests/test_public_snapshot_security_contract_fixtures.py',
    'tests/test_public_snapshot_residue_audit.py',
    'tests/test_replayable_truth_fixture.py',
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


class ReceiptSchemaValidationError(AssertionError):
    pass


def _json_type_name(value: Any) -> str:
    if isinstance(value, bool):
        return 'boolean'
    if isinstance(value, dict):
        return 'object'
    if isinstance(value, list):
        return 'array'
    if isinstance(value, int) and not isinstance(value, bool):
        return 'integer'
    if isinstance(value, float):
        return 'number'
    if isinstance(value, str):
        return 'string'
    if value is None:
        return 'null'
    return type(value).__name__


def _assert_schema_type(value: Any, expected: Any, path: str) -> None:
    expected_types = expected if isinstance(expected, list) else [expected]
    actual = _json_type_name(value)
    if actual == 'integer' and 'number' in expected_types:
        return
    if actual not in expected_types:
        raise ReceiptSchemaValidationError(f'{path}: expected {expected_types}, got {actual}')


def _validate_schema_value(schema: Mapping[str, Any], value: Any, path: str = '$') -> None:
    if 'const' in schema and value != schema['const']:
        raise ReceiptSchemaValidationError(f'{path}: expected const {schema["const"]!r}, got {value!r}')
    if 'enum' in schema and value not in schema['enum']:
        raise ReceiptSchemaValidationError(f'{path}: expected one of {schema["enum"]!r}, got {value!r}')
    if 'type' in schema:
        _assert_schema_type(value, schema['type'], path)
    if isinstance(value, str) and 'minLength' in schema and len(value) < int(schema['minLength']):
        raise ReceiptSchemaValidationError(f'{path}: expected minLength {schema["minLength"]}')
    if isinstance(value, (int, float)) and not isinstance(value, bool) and 'minimum' in schema and value < float(schema['minimum']):
        raise ReceiptSchemaValidationError(f'{path}: expected minimum {schema["minimum"]}')
    if schema.get('type') == 'object':
        if not isinstance(value, dict):
            raise ReceiptSchemaValidationError(f'{path}: expected object')
        for key in schema.get('required', []):
            if key not in value:
                raise ReceiptSchemaValidationError(f'{path}: missing required field {key!r}')
        properties = schema.get('properties') if isinstance(schema.get('properties'), dict) else {}
        for key, subschema in properties.items():
            if key in value and isinstance(subschema, dict):
                _validate_schema_value(subschema, value[key], f'{path}.{key}')
        if schema.get('additionalProperties') is False:
            extra = sorted(set(value) - set(properties))
            if extra:
                raise ReceiptSchemaValidationError(f'{path}: unexpected fields {extra!r}')
    if schema.get('type') == 'array':
        if not isinstance(value, list):
            raise ReceiptSchemaValidationError(f'{path}: expected array')
        item_schema = schema.get('items')
        if isinstance(item_schema, dict):
            for idx, item in enumerate(value):
                _validate_schema_value(item_schema, item, f'{path}[{idx}]')


def _load_receipt_schema() -> Dict[str, Any]:
    value = json.loads((ROOT / RECEIPT_SCHEMA_REF).read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise ReceiptSchemaValidationError('receipt schema root is not an object')
    return value


def validate_receipt_schema(receipt: Mapping[str, Any]) -> None:
    _validate_schema_value(_load_receipt_schema(), receipt)


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


def _build_receipt(checks: Sequence[CheckReceipt], include_pytest: bool) -> Dict[str, Any]:
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
        'checks_requested': list_check_ids(include_pytest),
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


def run_validation(include_pytest: bool) -> Dict[str, Any]:
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


def main(argv: Sequence[str] | None = None) -> int:
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


if __name__ == '__main__':
    raise SystemExit(main())
