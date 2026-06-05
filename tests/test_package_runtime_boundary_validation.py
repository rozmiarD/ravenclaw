from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'validate_package_runtime_boundary.py'


def _load_validator():
    spec = importlib.util.spec_from_file_location('ravenclaw_validate_package_runtime_boundary', SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_package_runtime_boundary_validator_passes() -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    assert proc.stdout.strip() == 'package_runtime_boundary_ok:ravenclaw-security==0.18.3:packages=ravenclaw'


def test_package_runtime_boundary_rejects_runtime_package_inclusion() -> None:
    validator = _load_validator()

    errors = validator.packaging_errors(
        {'name': 'ravenclaw-security'},
        {'packages': ['ravenclaw', 'engine', 'logdash'], 'py-modules': []},
        list(validator.EXPECTED_PACKAGE_FILES),
    )

    assert 'setuptools_packages_mismatch:[\'ravenclaw\', \'engine\', \'logdash\']' in errors
    assert 'runtime_package_included:engine' in errors
    assert 'runtime_package_included:logdash' in errors


def test_package_runtime_boundary_rejects_full_runtime_overclaim() -> None:
    validator = _load_validator()

    errors = validator.document_errors(
        {
            'README.md': (
                'The current published public helper package is `ravenclaw-security==0.18.3`.\n'
                'ravenclaw-security includes the full runtime.\n'
                'govengine>=0.12.2a0,<0.13\n'
                'sclite-core>=1.0.1,<1.1\n'
            )
        },
        '0.18.3',
        'govengine>=0.12.2a0,<0.13',
        'sclite-core>=1.0.1,<1.1',
    )

    assert 'README.md:forbidden_runtime_package_claim:ravenclaw-security includes the full runtime' in errors
