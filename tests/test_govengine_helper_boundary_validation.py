from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'validate_govengine_helper_boundary.py'


def _load_validator():
    spec = importlib.util.spec_from_file_location('ravenclaw_validate_govengine_helper_boundary', SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_govengine_helper_boundary_validator_passes() -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    assert proc.stdout.strip() == 'govengine_helper_boundary_ok:engine_imports=wrapper_only'


def test_govengine_helper_boundary_rejects_direct_runtime_import() -> None:
    validator = _load_validator()

    errors = validator._source_errors(
        ROOT / 'engine' / 'fixture_runtime.py',
        'from govengine.policy.core import get_runtime_allowed_tools\n',
    )

    assert errors == ['engine/fixture_runtime.py:direct_optional_helper_import:govengine.policy.core']
