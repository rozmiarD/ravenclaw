#!/usr/bin/env python3
from __future__ import annotations

import sys
import tomllib
from pathlib import Path
from typing import Mapping


ROOT = Path(__file__).resolve().parents[1]

EXPECTED_PACKAGE_FILES = (
    'ravenclaw/__init__.py',
    'ravenclaw/openclaw_readiness.py',
    'ravenclaw/security_profile.py',
)

PACKAGE_RUNTIME_DOCS = (
    'README.md',
    'INSTALL.md',
    'PUBLIC_STATUS.md',
    'VALIDATION.md',
    'VERSION_ROADMAP.md',
    'PUBLISHING.md',
    'QUALITY_SIGNALS.md',
    'REVIEWER_VALIDATION_GUIDE.md',
)

FORBIDDEN_RUNTIME_PACKAGE_CLAIMS = (
    'ravenclaw-security includes the full runtime',
    'ravenclaw-security packages engine/',
    'ravenclaw-security packages logdash/',
    'ravenclaw-security ships Logdash',
    'full runtime package is published',
    'complete PyPI-published Ravenclaw runtime runner is available',
    'production-ready runtime package',
    'OpenClaw adapter implementation is packaged',
)


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding='utf-8')


def _pyproject() -> Mapping[str, object]:
    return tomllib.loads(_read('pyproject.toml'))['project']


def _tool_setuptools() -> Mapping[str, object]:
    return tomllib.loads(_read('pyproject.toml')).get('tool', {}).get('setuptools', {})


def _project_dependency(project: Mapping[str, object], name: str) -> str:
    prefix = f'{name}>='
    for dependency in project.get('dependencies', []):  # type: ignore[union-attr]
        text = str(dependency)
        if text.startswith(prefix):
            return text
    raise AssertionError(f'missing_dependency:{name}')


def current_package_files(root: Path = ROOT) -> list[str]:
    return sorted(
        str(path.relative_to(root))
        for path in (root / 'ravenclaw').glob('*.py')
        if path.is_file()
    )


def packaging_errors(
    project: Mapping[str, object],
    setuptools_config: Mapping[str, object],
    package_files: list[str],
) -> list[str]:
    errors: list[str] = []
    if project.get('name') != 'ravenclaw-security':
        errors.append(f'distribution_name_mismatch:{project.get("name")}')
    if list(setuptools_config.get('packages', [])) != ['ravenclaw']:
        errors.append(f'setuptools_packages_mismatch:{setuptools_config.get("packages")}')
    if list(setuptools_config.get('py-modules', [])) != []:
        errors.append(f'setuptools_py_modules_not_empty:{setuptools_config.get("py-modules")}')
    for forbidden in ('engine', 'logdash', 'scripts', 'bin'):
        packages = [str(item) for item in setuptools_config.get('packages', [])]
        if any(item == forbidden or item.startswith(forbidden + '.') for item in packages):
            errors.append(f'runtime_package_included:{forbidden}')
    if package_files != list(EXPECTED_PACKAGE_FILES):
        errors.append(f'package_files_mismatch:{package_files}')
    return errors


def document_errors(text_by_path: Mapping[str, str], version: str, govengine_dep: str, sclite_dep: str) -> list[str]:
    required_by_path = {
        'README.md': (
            f'current published public helper package is `ravenclaw-security=={version}`',
            'The full\nruntime, demo, Logdash, and validation surfaces remain source/reference\nrepository workflows',
            govengine_dep,
            sclite_dep,
        ),
        'INSTALL.md': (
            f'pip install ravenclaw-security=={version}',
            'The `0.18.2` wheel is intentionally a narrow public contract/profile package.',
            'Use the repository install path above for the full source/reference runtime',
        ),
        'PUBLIC_STATUS.md': (
            f'ravenclaw-security=={version}',
            'narrow public profile/readiness package',
            'full runtime remains source/reference',
        ),
        'VALIDATION.md': (
            'python scripts/validate_package_runtime_boundary.py',
            'package/runtime boundary',
            'narrow public helper package',
        ),
        'VERSION_ROADMAP.md': (
            '`0.18.x` — Package/runtime readiness checkpoint',
            'keep the public distribution as the bounded\n`ravenclaw-security` helper/profile package',
        ),
        'PUBLISHING.md': (
            f'ravenclaw-security=={version}',
            'not the complete source runtime runner',
        ),
        'QUALITY_SIGNALS.md': (
            f'ravenclaw-security=={version}',
            'the full runtime remains source/reference-owned',
        ),
        'REVIEWER_VALIDATION_GUIDE.md': (
            'python scripts/validate_package_runtime_boundary.py',
            'package/runtime boundary',
        ),
    }
    errors: list[str] = []
    for path, expected_fragments in required_by_path.items():
        text = text_by_path.get(path, '')
        for expected in expected_fragments:
            if expected not in text:
                errors.append(f'{path}:missing_package_runtime_truth:{expected}')
        lowered = text.lower()
        for claim in FORBIDDEN_RUNTIME_PACKAGE_CLAIMS:
            if claim.lower() in lowered:
                errors.append(f'{path}:forbidden_runtime_package_claim:{claim}')
    return errors


def collect_errors() -> list[str]:
    project = _pyproject()
    version = str(project['version'])
    govengine_dep = _project_dependency(project, 'govengine')
    sclite_dep = _project_dependency(project, 'sclite-core')
    errors = packaging_errors(project, _tool_setuptools(), current_package_files())
    text_by_path = {path: _read(path) for path in PACKAGE_RUNTIME_DOCS}
    errors.extend(document_errors(text_by_path, version, govengine_dep, sclite_dep))
    return errors


def main() -> int:
    errors = collect_errors()
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    project = _pyproject()
    print(f'package_runtime_boundary_ok:ravenclaw-security=={project["version"]}:packages=ravenclaw')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
