#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
ENGINE_DIR = ROOT / 'engine'
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

import security_contract_layer as scl  # type: ignore


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise SystemExit(f'{path}: expected JSON object')
    return value


def _list_of_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _execution_plan(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def report_from_spec(spec: Mapping[str, Any]) -> dict[str, Any]:
    target = str(spec.get('target') or spec.get('url') or '')
    normalized_args = _list_of_strings(spec.get('normalized_args') if 'normalized_args' in spec else spec.get('args'))
    execution_plan = _execution_plan(spec.get('execution_plan') if 'execution_plan' in spec else spec.get('tool_chain'))
    target_in_scope = spec.get('target_in_scope') if isinstance(spec.get('target_in_scope'), bool) else None
    return scl.build_scope_fidelity_report(
        target=target,
        normalized_args=normalized_args,
        execution_plan=execution_plan,
        target_in_scope=target_in_scope,
    )


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    if args.spec:
        spec = _load_json(Path(args.spec))
        report = report_from_spec(spec)
    else:
        execution_plan = []
        if args.execution_plan:
            value = json.loads(args.execution_plan)
            execution_plan = _execution_plan(value)
        report = scl.build_scope_fidelity_report(
            target=args.target or '',
            normalized_args=list(args.arg or []),
            execution_plan=execution_plan,
            target_in_scope=args.target_in_scope,
        )
    scl.validate_scope_fidelity_report(report, root=ROOT)
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Build a public-safe Scope Fidelity report from a local spec or CLI args.')
    parser.add_argument('--spec', help='local JSON spec containing target, normalized_args/args, and execution_plan/tool_chain')
    parser.add_argument('--target', help='target URL when not using --spec')
    parser.add_argument('--arg', action='append', default=[], help='repeatable normalized arg when not using --spec')
    parser.add_argument('--execution-plan', help='JSON array execution_plan when not using --spec')
    parser.add_argument('--target-in-scope', action='store_true', default=None, help='mark target_in_scope true for manual mode')
    parser.add_argument('--compact', action='store_true', help='emit compact JSON')
    parser.add_argument(
        '--fail-on',
        choices=['never', 'fail', 'review'],
        default='never',
        help='exit with code 2 when the verdict reaches the selected threshold: fail only, review/fail, or never',
    )
    args = parser.parse_args(argv)

    if bool(args.spec) == bool(args.target):
        parser.error('provide exactly one of --spec or --target')

    report = build_report(args)
    if args.compact:
        print(json.dumps(report, sort_keys=True, separators=(',', ':')))
    else:
        print(json.dumps(report, indent=2, sort_keys=True))

    verdict = str(report.get('verdict') or '')
    if args.fail_on == 'fail' and verdict == 'fail':
        return 2
    if args.fail_on == 'review' and verdict in {'review', 'fail'}:
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
