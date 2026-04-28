from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / 'scripts'
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import validate_security_contract_fixtures as validator  # type: ignore


FIXTURE_DIR = ROOT / 'examples' / 'security-contract-proof'


def test_security_contract_proof_fixture_validates() -> None:
    assert validator.validate_fixture_dir(FIXTURE_DIR) == []


def test_security_contract_fixture_validator_rejects_missing_artifact(tmp_path: Path) -> None:
    missing_dir = tmp_path / 'missing-fixture'
    missing_dir.mkdir()
    errors = validator.validate_fixture_dir(missing_dir)
    assert errors
    assert errors[0].startswith('load_failed:')
    assert 'policy_decision.json' in errors[0]
