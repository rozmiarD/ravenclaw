from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'validate_extraction_roadmap.py'


def _load_validator():
    spec = importlib.util.spec_from_file_location('ravenclaw_validate_extraction_roadmap', SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_extraction_roadmap_validator_passes() -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    assert proc.stdout.strip() == 'extraction_roadmap_ok:ravenclaw-security==0.18.4'


def test_extraction_roadmap_rejects_unknown_status() -> None:
    validator = _load_validator()

    errors = validator.status_errors(
        '| Candidate | Ravenclaw source files | Generic concept | Recommendation | Risk | Status |\n'
        '| --- | --- | --- | --- | --- | --- |\n'
        '| queue loop | `engine/auto_campaign_runner.py` | scheduler | move it | high | extract implementation now |\n'
    )

    assert errors == ['unknown_status:extract implementation now']


def test_extraction_roadmap_rejects_forbidden_claims() -> None:
    validator = _load_validator()

    errors = validator.forbidden_claim_errors('GovEngine owns Ravenclaw runtime and OpenClaw adapter is implemented.')

    assert errors == [
        'forbidden_claim:OpenClaw adapter is implemented',
        'forbidden_claim:GovEngine owns Ravenclaw runtime',
    ]
