#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ENGINE_DIR = ROOT / 'engine'
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))


REQUIRED_RUNTIME = [
    ('PyYAML', 'yaml', 'PyYAML>=6,<7'),
    ('sclite-core', 'sclite', 'sclite-core>=0.5.1,<0.6'),
    ('govengine', 'govengine', 'govengine>=0.2.0,<0.3'),
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


def check_govengine_surface_registry() -> dict[str, Any]:
    expected = ['artifact_governance_core', 'controlled_execution_core', 'security_profile_helpers']
    try:
        from govengine import public_surface_index  # type: ignore
    except Exception as exc:  # pragma: no cover - defensive diagnostic path
        return {
            'status': 'failed',
            'expected': expected,
            'actual': [],
            'error': f'{type(exc).__name__}: {exc}',
        }

    try:
        surfaces = list(public_surface_index())
        actual = [str(surface.name) for surface in surfaces]
        optional = {str(surface.name): bool(surface.optional_profile) for surface in surfaces}
        passed = actual == expected and optional.get('security_profile_helpers') is True
        return {
            'status': 'passed' if passed else 'failed',
            'expected': expected,
            'actual': actual,
            'optional_profile': optional,
            'error': None if passed else 'unexpected GovEngine public surface registry shape',
        }
    except Exception as exc:  # pragma: no cover - defensive diagnostic path
        return {
            'status': 'failed',
            'expected': expected,
            'actual': [],
            'error': f'{type(exc).__name__}: {exc}',
        }


def check_govengine_security_profile() -> dict[str, Any]:
    expected_groups = ['action_tooling', 'policy_scope', 'review_contracts']
    expected_modules = [
        'govengine.action_schema',
        'govengine.policy.gateway',
        'govengine.contracts.signal',
    ]
    try:
        from govengine import security_profile  # type: ignore
    except Exception as exc:  # pragma: no cover - defensive diagnostic path
        return {
            'status': 'failed',
            'source': None,
            'expected_groups': expected_groups,
            'actual_groups': [],
            'expected_modules': expected_modules,
            'error': f'{type(exc).__name__}: {exc}',
        }

    try:
        payload = security_profile.security_profile_index()
        groups = [str(group.get('name')) for group in payload.get('groups', [])]
        modules = tuple(security_profile.security_profile_module_names())
        security_profile.assert_security_profile_boundary()
        imported = security_profile.import_security_profile_module('govengine.action_schema')
        passed = (
            payload.get('surface', {}).get('name') == 'security_profile_helpers'
            and payload.get('surface', {}).get('optional_profile') is True
            and groups == expected_groups
            and all(module in modules for module in expected_modules)
            and 'govengine.core' not in modules
            and 'govengine.execution.gate' not in modules
            and getattr(imported, 'DEFAULT_ACTION_TYPE', None) == 'single_probe'
        )
        return {
            'status': 'passed' if passed else 'failed',
            'source': payload.get('entrypoint'),
            'expected_groups': expected_groups,
            'actual_groups': groups,
            'expected_modules': expected_modules,
            'surface': payload.get('surface'),
            'error': None if passed else 'unexpected GovEngine security-profile shape',
        }
    except Exception as exc:  # pragma: no cover - defensive diagnostic path
        return {
            'status': 'failed',
            'source': None,
            'expected_groups': expected_groups,
            'actual_groups': [],
            'expected_modules': expected_modules,
            'error': f'{type(exc).__name__}: {exc}',
        }


def check_govengine_boundary_profile() -> dict[str, Any]:
    try:
        import govengine_boundary_profile as boundary_profile  # type: ignore
    except Exception as exc:  # pragma: no cover - defensive diagnostic path
        return {
            'status': 'failed',
            'available': False,
            'error': f'{type(exc).__name__}: {exc}',
        }

    try:
        status = dict(boundary_profile.ravenclaw_boundary_status())
        status['available'] = bool(boundary_profile.govengine_boundary_report_available())
        return status
    except Exception as exc:  # pragma: no cover - defensive diagnostic path
        return {
            'status': 'failed',
            'available': False,
            'error': f'{type(exc).__name__}: {exc}',
        }


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
    govengine_surface_registry = check_govengine_surface_registry()
    govengine_security_profile = check_govengine_security_profile()
    govengine_boundary_profile = check_govengine_boundary_profile()
    python_ok = sys.version_info >= (3, 11)

    failed = [dep for dep in dependencies if dep.status != 'passed']
    if not python_ok:
        failed.append(DependencyCheck('python', 'python', 'Python>=3.11', False, sys.version.split()[0], 'failed', 'Python 3.11+ required'))
    if pip_check is not None and pip_check['status'] != 'passed':
        failed.append(DependencyCheck('pip-check', 'pip', 'python -m pip check', False, None, 'failed', pip_check.get('stdout') or pip_check.get('stderr') or 'pip check failed'))
    if govengine_surface_registry['status'] != 'passed':
        failed.append(DependencyCheck('govengine-surfaces', 'govengine', 'govengine.surfaces.public_surface_index', False, None, 'failed', govengine_surface_registry.get('error') or 'surface registry check failed'))
    if govengine_security_profile['status'] != 'passed':
        failed.append(DependencyCheck('govengine-security-profile', 'govengine.security_profile', 'GovEngine security-profile facade', False, None, 'failed', govengine_security_profile.get('error') or 'security-profile check failed'))
    if govengine_boundary_profile['status'] != 'passed':
        failed.append(DependencyCheck('govengine-boundary-profile', 'govengine_boundary_profile', 'Ravenclaw GovEngine boundary-profile compatibility seam', False, None, 'failed', govengine_boundary_profile.get('error') or 'boundary-profile compatibility check failed'))

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
        'govengine_surface_registry': govengine_surface_registry,
        'govengine_security_profile': govengine_security_profile,
        'govengine_boundary_profile': govengine_boundary_profile,
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
        print(f"{report['govengine_surface_registry']['status']} govengine_surface_registry")
        print(f"{report['govengine_security_profile']['status']} govengine_security_profile source={report['govengine_security_profile'].get('source')}")
        print(f"{report['govengine_boundary_profile']['status']} govengine_boundary_profile source={report['govengine_boundary_profile'].get('source')}")
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
