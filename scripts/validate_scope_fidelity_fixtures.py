#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
ENGINE_DIR = ROOT / 'engine'
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

import security_contract_layer as scl  # type: ignore

EXPECTED_CASES = {
    'exact.json': 'pass',
    'cross_host_mismatch.json': 'fail',
    'ambiguous.json': 'review',
}
FORBIDDEN_MARKERS = (
    'authorization:',
    'bearer ',
    'cookie:',
    'set-cookie:',
    'password=',
    'github_pat',
    'api_key',
    'session=',
)


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise AssertionError(f'{path}: expected JSON object')
    return value


def _assert_public_safe(path: Path, report: Mapping[str, Any]) -> None:
    public_safety = report.get('public_safety') if isinstance(report.get('public_safety'), dict) else {}
    if public_safety.get('live_target_execution') is not False:
        raise AssertionError(f'{path}: live_target_execution must be false')
    if public_safety.get('protocol_adapter_work') is not False:
        raise AssertionError(f'{path}: protocol_adapter_work must be false')
    if public_safety.get('raw_stdout_stderr_included') is not False:
        raise AssertionError(f'{path}: raw_stdout_stderr_included must be false')
    payload = json.dumps(report, sort_keys=True).lower()
    leaked = [marker for marker in FORBIDDEN_MARKERS if marker in payload]
    if leaked:
        raise AssertionError(f'{path}: forbidden marker(s) present: {leaked!r}')


def validate_fixture_dir(fixture_dir: Path) -> None:
    for filename, expected_verdict in EXPECTED_CASES.items():
        path = fixture_dir / filename
        if not path.exists():
            raise FileNotFoundError(f'missing scope fidelity fixture: {path}')
        report = _load_json(path)
        scl.validate_scope_fidelity_report(report, root=ROOT)
        if report.get('verdict') != expected_verdict:
            raise AssertionError(f'{path}: expected verdict {expected_verdict!r}, got {report.get("verdict")!r}')
        _assert_public_safe(path, report)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Validate public-safe Scope Fidelity report fixtures.')
    parser.add_argument('fixture_dir', nargs='?', default='examples/scope-fidelity-report')
    args = parser.parse_args(argv)
    fixture_dir = Path(args.fixture_dir)
    validate_fixture_dir(fixture_dir)
    print(f'scope_fidelity_fixtures_ok:{fixture_dir}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
