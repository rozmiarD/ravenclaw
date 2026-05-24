from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'validate_openclaw_fixture_presenter.py'


def _load_validator():
    spec = importlib.util.spec_from_file_location('ravenclaw_validate_openclaw_fixture_presenter', SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_openclaw_fixture_presenter_validator_passes() -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    assert proc.stdout.strip() == 'openclaw_fixture_presenter_ok:adapter_status=not_implemented:fixture_mode=presenter_only'


def test_openclaw_fixture_presenter_rejects_sensitive_value_leak() -> None:
    validator = _load_validator()
    carrier_input = {
        'scope_ref': 'scope-1',
        'policy_decision': 'approved',
        'prepared_spec_ref': 'prepared-1',
        'approved_spec_ref': 'approved-1',
        'runner_supervision_status': 'ready',
        'tokens': 'leaked-token',
    }
    expected = validator.build_openclaw_fixture_packet(carrier_input)
    expected['public_summary']['token_debug'] = 'leaked-token'

    errors = validator.validate_fixture_packet(carrier_input, expected)

    assert 'fixture_packet_mismatch' in errors
    assert 'sensitive_value_leaked:tokens' in errors
