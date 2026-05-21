from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'validate_runtime_state_truth.py'


def _load_validator():
    spec = importlib.util.spec_from_file_location('ravenclaw_validate_runtime_state_truth', SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_runtime_state_truth_validator_passes() -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    assert proc.stdout.strip() == 'runtime_state_truth_ok:artifacts=10:projected=4'


def test_runtime_state_truth_validator_rejects_missing_state_file_doc_entry() -> None:
    validator = _load_validator()
    docs = {path: validator._read(path) for path in validator.DOC_PATHS}
    docs['STATE_FILES.md'] = docs['STATE_FILES.md'].replace('reports/.runtime_snapshot.json', '')

    errors = validator.documentation_errors(docs)

    assert 'STATE_FILES.md:missing_runtime_state_path:reports/.runtime_snapshot.json' in errors
