from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_public_snapshot_generates_and_reviews_current_lifecycle_bundle(tmp_path: Path) -> None:
    out = tmp_path / 'public-snapshot'
    subprocess.run(
        [str(ROOT / 'scripts' / 'assemble_public_snapshot.sh'), str(out)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=True,
    )

    expected_paths = [
        'SECURITY_CONTRACT_LAYER.md',
        'REPLAYABLE_TRUTH_RUNTIME.md',
        'schemas/policy_decision.v0.2.schema.json',
        'schemas/execution_contract.v0.2.schema.json',
        'schemas/execution_ticket.v0.3.schema.json',
        'schemas/execution_receipt.v0.2.schema.json',
        'schemas/evidence_contract.v0.2.schema.json',
        'schemas/security_contract_validation_receipt.v0.1.schema.json',
        'schemas/public_validation_surface_index.v0.1.schema.json',
        'schemas/public_snapshot_manifest.v0.1.schema.json',
        'pyproject.toml',
        'references/security-contract-validation-receipt-v0.1.md',
        'examples/replayable-truth-runtime/replay_bundle.json',
        'examples/replayable-truth-runtime/replay_result.json',
        'bin/demo',
        'bin/demo-bundle',
        'scripts/assemble_public_snapshot.sh',
        'scripts/audit_public_snapshot_residue.py',
        'scripts/bootstrap_public_demo.sh',
        'scripts/run_security_contract_validation.py',
        'scripts/validate_replayable_truth_fixture.py',
        'scripts/run_pytest_slice.py',
    ]
    for rel in expected_paths:
        assert (out / rel).exists(), rel

    excluded_paths = [
        'examples/security-contract-proof',
        'examples/contract-lifecycle-v0.2',
        'scripts/validate_security_contract_fixtures.py',
        'demo-output',
        'memory',
        'reports',
        'engine/context_summary.json',
        'engine/pipeline_config.json',
        'logdash/logs.db',
        'out.json',
        'scl',
    ]
    for rel in excluded_paths:
        assert not (out / rel).exists(), rel

    bundle_dir = out / 'demo-output'
    runtime_dir = tmp_path / 'snapshot-runtime'
    env = {
        **os.environ,
        'PYTHONDONTWRITEBYTECODE': '1',
        'RAVENCLAW_WORKSPACE': str(out),
        'RAVENCLAW_REPORTS_DIR': str(runtime_dir / 'reports'),
        'RAVENCLAW_TMP_DIR': str(runtime_dir / 'tmp'),
        'RAVENCLAW_LOGDASH_DB': str(runtime_dir / 'logdash' / 'logs.db'),
        'RAVENCLAW_PIPELINE_CONFIG': str(runtime_dir / 'pipeline_config.json'),
        'RAVENCLAW_CONTEXT_SUMMARY_PATH': str(runtime_dir / 'reports' / 'cache' / 'context_summary.json'),
    }
    subprocess.run(
        [sys.executable, str(out / 'bin' / 'demo-bundle'), '--output-dir', str(bundle_dir), '--print-summary'],
        cwd=str(out),
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    review = subprocess.run(
        [sys.executable, '-m', 'sclite.cli', 'review', str(bundle_dir / 'review_bundle'), '--format', 'summary', '--fail-on', 'review'],
        cwd=str(out),
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert 'review_bundle:pass:' in review.stdout

    replay_proc = subprocess.run(
        [sys.executable, str(out / 'scripts' / 'validate_replayable_truth_fixture.py'), 'examples/replayable-truth-runtime'],
        cwd=str(out),
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert 'replayable_truth_fixture_ok:' in replay_proc.stdout
