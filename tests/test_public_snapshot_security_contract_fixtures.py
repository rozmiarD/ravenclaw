from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_public_snapshot_includes_and_validates_security_contract_fixtures(tmp_path: Path) -> None:
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
        'schemas/policy_decision.v0.1.schema.json',
        'schemas/approved_execution_spec.v0.1.schema.json',
        'schemas/execution_receipt.v0.1.schema.json',
        'schemas/evidence_bundle.v0.1.schema.json',
        'schemas/security_contract_validation_receipt.v0.1.schema.json',
        'schemas/prepared_execution_spec.v0.1.schema.json',
        'schemas/redacted_prepared_execution_spec.v0.1.schema.json',
        'schemas/redaction_policy.v0.1.schema.json',
        'schemas/redaction_receipt.v0.1.schema.json',
        'schemas/public_validation_surface_index.v0.1.schema.json',
        'schemas/public_snapshot_manifest.v0.1.schema.json',
        'pyproject.toml',
        'references/policy-decision-v0.1.md',
        'references/approved-execution-spec-v0.1.md',
        'references/execution-receipt-v0.1.md',
        'references/evidence-bundle-v0.1.md',
        'references/security-contract-validation-receipt-v0.1.md',
        'examples/security-contract-proof/policy_decision.json',
        'examples/security-contract-proof/prepared_execution_spec.redacted.json',
        'examples/security-contract-proof/approved_execution_spec.json',
        'examples/security-contract-proof/execution_receipt.json',
        'examples/security-contract-proof/evidence_bundle.json',
        'examples/security-contract-proof/evidence_summary.md',
        'examples/replayable-truth-runtime/replay_bundle.json',
        'examples/replayable-truth-runtime/replay_result.json',
        'examples/replayable-truth-runtime/README.md',
        '.devcontainer/devcontainer.json',
        '.devcontainer/Dockerfile',
        'compose.demo.yaml',
        'bin/demo',
        'bin/demo-bundle',
        'scripts/assemble_public_snapshot.sh',
        'scripts/audit_public_snapshot_residue.py',
        'scripts/bootstrap_public_demo.sh',
        'scripts/validate_security_contract_fixtures.py',
        'scripts/run_security_contract_validation.py',
        'scripts/validate_replayable_truth_fixture.py',
        'scripts/run_pytest_slice.py',
    ]
    for rel in expected_paths:
        assert (out / rel).exists(), rel

    excluded_paths = [
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

    proc = subprocess.run(
        [sys.executable, str(out / 'scripts' / 'validate_security_contract_fixtures.py'), 'examples/security-contract-proof'],
        cwd=str(out),
        env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'},
        capture_output=True,
        text=True,
        check=True,
    )
    assert 'security_contract_fixtures_ok:' in proc.stdout

    replay_proc = subprocess.run(
        [sys.executable, str(out / 'scripts' / 'validate_replayable_truth_fixture.py'), 'examples/replayable-truth-runtime'],
        cwd=str(out),
        env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'},
        capture_output=True,
        text=True,
        check=True,
    )
    assert 'replayable_truth_fixture_ok:' in replay_proc.stdout
