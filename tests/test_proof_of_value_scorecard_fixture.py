from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'examples' / 'proof-of-value-scorecard' / 'scorecard.json'
VALIDATOR = ROOT / 'scripts' / 'validate_proof_of_value_scorecard.py'
if str(ROOT / 'scripts') not in sys.path:
    sys.path.insert(0, str(ROOT / 'scripts'))
if str(ROOT / 'engine') not in sys.path:
    sys.path.insert(0, str(ROOT / 'engine'))

import validate_proof_of_value_scorecard as validator  # type: ignore


def test_committed_proof_of_value_scorecard_fixture_validates() -> None:
    proc = subprocess.run(
        [sys.executable, str(VALIDATOR), str(FIXTURE)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    assert 'proof_of_value_scorecard_ok:7:' in proc.stdout


def test_committed_proof_of_value_scorecard_fixture_preserves_non_claims() -> None:
    scorecard = validator.validate_scorecard_file(FIXTURE)
    assert scorecard['scope']['live_target_execution'] is False
    assert scorecard['scope']['live_vulnerability_claim'] is False
    assert scorecard['scope']['protocol_adapter_work'] is False
    assert scorecard['summary']['status'] == 'passed'
    assert {dimension['id'] for dimension in scorecard['dimensions']} == {
        'scope_fidelity',
        'policy_decision_clarity',
        'execution_spec_accountability',
        'dry_run_evidence_separation',
        'replayability',
        'snapshot_completeness',
        'non_claim_preservation',
    }


def test_proof_of_value_scorecard_fixture_rejects_live_claim(tmp_path: Path) -> None:
    data = json.loads(FIXTURE.read_text(encoding='utf-8'))
    data['scope']['live_vulnerability_claim'] = True
    bad = tmp_path / 'bad-scorecard.json'
    bad.write_text(json.dumps(data), encoding='utf-8')
    proc = subprocess.run(
        [sys.executable, str(VALIDATOR), str(bad)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    assert 'live_vulnerability_claim' in proc.stderr or 'live_vulnerability_claim' in proc.stdout


def test_proof_of_value_scorecard_fixture_included_in_public_snapshot(tmp_path: Path) -> None:
    snapshot = tmp_path / 'public-snapshot'
    subprocess.run(
        [str(ROOT / 'scripts' / 'assemble_public_snapshot.sh'), str(snapshot)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    assert (snapshot / 'examples/proof-of-value-scorecard/scorecard.json').exists()
    assert (snapshot / 'examples/proof-of-value-scorecard/scorecard.md').exists()
    proc = subprocess.run(
        [sys.executable, str(snapshot / 'scripts' / 'validate_proof_of_value_scorecard.py'), 'examples/proof-of-value-scorecard/scorecard.json'],
        cwd=str(snapshot),
        capture_output=True,
        text=True,
        check=True,
    )
    assert 'proof_of_value_scorecard_ok:7:' in proc.stdout
