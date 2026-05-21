from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'validate_public_truth.py'


def _load_validator():
    spec = importlib.util.spec_from_file_location('ravenclaw_validate_public_truth', SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_public_truth_validator_passes() -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    assert proc.stdout.strip().startswith('public_truth_ok:ravenclaw-security==0.16.3:govengine>=0.10.1a0,<0.11:')


def test_public_truth_validator_negative_case_catches_stale_current_govengine_dependency() -> None:
    validator = _load_validator()

    errors = validator.stale_current_dependency_errors(
        {'README.md': 'Current dependency baseline: Ravenclaw -> govengine>=0.7.0,<0.8'},
        'govengine>=0.10.1a0,<0.11',
    )

    assert errors == [
        'README.md:stale_current_govengine_dependency:Current dependency baseline: Ravenclaw -> govengine>=0.7.0'
    ]
