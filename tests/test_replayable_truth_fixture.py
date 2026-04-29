from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / 'scripts'
ENGINE_DIR = ROOT / 'engine'
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

import validate_replayable_truth_fixture as validator  # type: ignore
from evaluation_replay import replay_decision_bundle  # type: ignore

FIXTURE_DIR = ROOT / 'examples' / 'replayable-truth-runtime'


def test_replayable_truth_fixture_matches_deterministic_replay_result() -> None:
    validator.validate_fixture(FIXTURE_DIR)


def test_replayable_truth_fixture_states_public_safe_non_live_semantics() -> None:
    bundle = json.loads((FIXTURE_DIR / 'replay_bundle.json').read_text(encoding='utf-8'))
    result = json.loads((FIXTURE_DIR / 'replay_result.json').read_text(encoding='utf-8'))
    assert bundle['schema_version'] == 'phase5-replay-bundle-v1'
    assert bundle['run_identity']['target'] == 'https://api.example.com/v1/users'
    assert bundle['execution']['mode'] == 'demo'
    assert bundle['execution']['engine_status'] == 'dry-run'
    assert result['schema_version'] == 'phase5-replay-result-v1'
    assert result['status'] == 'ok'
    assert result['policy_blocked'] is False
    assert result['owner_gate_pending'] is False
    assert result['metric_exclusion_reasons'] == []


def test_replayable_truth_fixture_replay_is_stable() -> None:
    bundle = json.loads((FIXTURE_DIR / 'replay_bundle.json').read_text(encoding='utf-8'))
    expected = json.loads((FIXTURE_DIR / 'replay_result.json').read_text(encoding='utf-8'))
    assert replay_decision_bundle(bundle) == expected


def test_replayable_truth_fixture_cli() -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / 'validate_replayable_truth_fixture.py'), str(FIXTURE_DIR)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    assert 'replayable_truth_fixture_ok:' in proc.stdout
