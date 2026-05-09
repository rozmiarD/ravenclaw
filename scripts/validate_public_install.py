#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import subprocess
import sys
from dataclasses import dataclass
from typing import Any


REQUIRED_RUNTIME = [
    ('PyYAML', 'yaml', 'PyYAML>=6,<7'),
    ('sclite-core', 'sclite', 'sclite-core>=0.2.1,<0.3'),
    ('govengine', 'govengine', 'govengine>=0.1,<0.2'),
]

REQUIRED_DEV = [
    ('pytest', 'pytest', 'pytest>=8,<9'),
    ('Flask', 'flask', 'Flask>=3,<4'),
]


@dataclass(frozen=True)
class DependencyCheck:
    distribution: str
    import_name: str
    requirement: str
    importable: bool
    version: str | None
    status: str
    error: str | None = None

    def to_json(self) -> dict[str, Any]:
        return {
            'distribution': self.distribution,
            'import_name': self.import_name,
            'requirement': self.requirement,
            'importable': self.importable,
            'version': self.version,
            'status': self.status,
            'error': self.error,
        }


def check_dependency(distribution: str, import_name: str, requirement: str) -> DependencyCheck:
    version: str | None = None
    try:
        version = metadata.version(distribution)
    except metadata.PackageNotFoundError as exc:
        return DependencyCheck(distribution, import_name, requirement, False, None, 'failed', str(exc))

    try:
        importlib.import_module(import_name)
    except Exception as exc:  # pragma: no cover - defensive diagnostic path
        return DependencyCheck(distribution, import_name, requirement, False, version, 'failed', f'{type(exc).__name__}: {exc}')

    return DependencyCheck(distribution, import_name, requirement, True, version, 'passed')


def run_pip_check() -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, '-m', 'pip', 'check'],
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        'command': [sys.executable, '-m', 'pip', 'check'],
        'returncode': proc.returncode,
        'status': 'passed' if proc.returncode == 0 else 'failed',
        'stdout': proc.stdout.strip(),
        'stderr': proc.stderr.strip(),
    }


def build_report(include_dev: bool, skip_pip_check: bool) -> dict[str, Any]:
    dependency_specs = list(REQUIRED_RUNTIME)
    if include_dev:
        dependency_specs.extend(REQUIRED_DEV)

    dependencies = [check_dependency(*spec) for spec in dependency_specs]
    pip_check = None if skip_pip_check else run_pip_check()
    python_ok = sys.version_info >= (3, 11)

    failed = [dep for dep in dependencies if dep.status != 'passed']
    if not python_ok:
        failed.append(DependencyCheck('python', 'python', 'Python>=3.11', False, sys.version.split()[0], 'failed', 'Python 3.11+ required'))
    if pip_check is not None and pip_check['status'] != 'passed':
        failed.append(DependencyCheck('pip-check', 'pip', 'python -m pip check', False, None, 'failed', pip_check.get('stdout') or pip_check.get('stderr') or 'pip check failed'))

    return {
        'artifact_type': 'ravenclaw_public_install_validation',
        'schema_version': 'v0.1',
        'mode': 'dev' if include_dev else 'runtime',
        'status': 'passed' if not failed else 'failed',
        'python': {
            'executable': sys.executable,
            'version': sys.version.split()[0],
            'requires': '>=3.11',
            'status': 'passed' if python_ok else 'failed',
        },
        'dependencies': [dep.to_json() for dep in dependencies],
        'pip_check': pip_check,
        'non_claims': [
            'Does not prove production deployment readiness.',
            'Does not authorize live target execution.',
            'Does not validate private operator overlays or credentials.',
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='Validate the public Ravenclaw install environment.')
    parser.add_argument('--dev', action='store_true', help='Require dev/test dependencies such as pytest and Flask.')
    parser.add_argument('--skip-pip-check', action='store_true', help='Skip python -m pip check.')
    parser.add_argument('--json', action='store_true', help='Emit machine-readable JSON.')
    args = parser.parse_args()

    report = build_report(include_dev=args.dev, skip_pip_check=args.skip_pip_check)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"ravenclaw_public_install_validation:{report['mode']}:{report['status']}")
        for dep in report['dependencies']:
            print(f"{dep['status']} {dep['distribution']} {dep['version'] or '-'} import={dep['import_name']}")
        if report['pip_check'] is not None:
            print(f"{report['pip_check']['status']} pip_check")
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
