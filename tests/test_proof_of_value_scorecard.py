from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'build_proof_of_value_scorecard.py'
if str(SCRIPT.parent) not in sys.path:
    sys.path.insert(0, str(SCRIPT.parent))
if str(ROOT / 'engine') not in sys.path:
    sys.path.insert(0, str(ROOT / 'engine'))

import build_proof_of_value_scorecard as scorecard_builder  # type: ignore
import security_contract_layer as scl  # type: ignore


def _scorecard() -> dict:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), '.', '--check'],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout)


def test_proof_of_value_scorecard_lists_core_dimensions() -> None:
    scorecard = _scorecard()
    assert scorecard['artifact_type'] == 'proof_of_value_scorecard'
    assert scorecard['schema_version'] == 'v0.1'
    assert scorecard['schema_ref'] == 'schemas/proof_of_value_scorecard.v0.1.schema.json'
    assert scorecard['summary'] == {
        'dimension_count': 7,
        'passed': 7,
        'failed': 0,
        'status': 'passed',
    }
    ids = {dimension['id'] for dimension in scorecard['dimensions']}
    assert ids == {
        'scope_fidelity',
        'policy_decision_clarity',
        'execution_spec_accountability',
        'dry_run_evidence_separation',
        'replayability',
        'snapshot_completeness',
        'non_claim_preservation',
    }


def test_proof_of_value_scorecard_preserves_public_safe_scope() -> None:
    scorecard = _scorecard()
    assert scorecard['scope'] == {
        'public_safe': True,
        'dry_run_or_local_only': True,
        'live_target_execution': False,
        'protocol_adapter_work': False,
        'live_vulnerability_claim': False,
    }
    for dimension in scorecard['dimensions']:
        assert dimension['status'] == 'passed'
        assert dimension['claim']
        assert dimension['non_claim']
        assert all(path['present'] for path in dimension['evidence_paths'])


def test_proof_of_value_scorecard_matches_schema() -> None:
    scorecard_builder.validate_scorecard_schema(_scorecard())


def test_proof_of_value_scorecard_schema_rejects_live_vulnerability_claim() -> None:
    scorecard = _scorecard()
    scorecard['scope']['live_vulnerability_claim'] = True
    try:
        scorecard_builder.validate_scorecard_schema(scorecard)
    except scl.JsonSchemaValidationError as exc:
        assert 'live_vulnerability_claim' in str(exc)
    else:  # pragma: no cover - assertion guard
        raise AssertionError('scorecard must not claim live vulnerability evidence')


def test_proof_of_value_scorecard_markdown_is_reviewer_facing() -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), '.', '--format', 'markdown', '--check'],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    assert '# Proof-of-Value Scorecard' in proc.stdout
    assert '| Dimension | Status | Evidence | Non-claim |' in proc.stdout
    assert 'live vulnerability discovery' in proc.stdout


def test_proof_of_value_scorecard_fails_when_evidence_missing(tmp_path: Path) -> None:
    snapshot = tmp_path / 'snapshot'
    subprocess.run(
        [str(ROOT / 'scripts' / 'assemble_public_snapshot.sh'), str(snapshot)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    (snapshot / 'PROOF_OF_VALUE.md').unlink()
    proc = subprocess.run(
        [sys.executable, str(snapshot / 'scripts' / 'build_proof_of_value_scorecard.py'), '.', '--check'],
        cwd=str(snapshot),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 1
    scorecard = json.loads(proc.stdout)
    assert scorecard['summary']['status'] == 'failed'
