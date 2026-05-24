from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'validate_public_truth.py'


def _load_validator():
    spec = importlib.util.spec_from_file_location('ravenclaw_validate_public_truth', SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_public_truth_validator_passes() -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    assert proc.stdout.strip().startswith('public_truth_ok:ravenclaw-security==0.18.0:govengine>=0.11.0a0,<0.12:')


def test_public_truth_validator_negative_case_catches_stale_current_govengine_dependency() -> None:
    validator = _load_validator()

    errors = validator.stale_current_dependency_errors(
        {'README.md': 'Current dependency baseline: Ravenclaw -> govengine>=0.7.0,<0.8'},
        'govengine>=0.11.0a0,<0.12',
    )

    assert errors == [
        'README.md:stale_current_govengine_dependency:Current dependency baseline: Ravenclaw -> govengine>=0.7.0'
    ]


def test_public_truth_validator_rejects_legacy_fixture_as_active_readiness_evidence() -> None:
    validator = _load_validator()

    errors = validator.active_readiness_legacy_path_errors({
        'references/openclaw-adapter-contract-map.md':
            'Evidence: `examples/security-contract-proof/input_scope.json`',
    })

    assert errors == [
        'references/openclaw-adapter-contract-map.md:legacy_proof_fixture_advertised_in_active_readiness_doc'
    ]


def test_public_truth_validator_rejects_legacy_fixture_in_active_scope_reference() -> None:
    validator = _load_validator()

    errors = validator.active_readiness_legacy_path_errors({
        'references/scope-fidelity-report-v0.1.md':
            'python scripts/build_scope_fidelity_report.py --spec examples/security-contract-proof/approved_execution_spec.json',
    })

    assert errors == [
        'references/scope-fidelity-report-v0.1.md:legacy_proof_fixture_advertised_in_active_readiness_doc'
    ]


def test_public_truth_validator_rejects_upstream_gateway_as_active_architecture() -> None:
    validator = _load_validator()

    errors = validator.host_owned_gateway_doc_errors({
        'ARCHITECTURE.md': 'Main files:\n- `govengine.policy.gateway`\n',
    })

    assert errors == [
        'ARCHITECTURE.md:missing_host_owned_gateway_claim:`engine/security_policy_gateway.py`',
        'ARCHITECTURE.md:upstream_gateway_listed_as_active_main_file',
        'ARCHITECTURE.md:missing_host_owned_action_tooling_claim:engine/security_tool_registry.py',
        'ARCHITECTURE.md:missing_host_owned_action_tooling_claim:engine/security_policy_core.py',
        'ARCHITECTURE.md:missing_host_owned_action_tooling_claim:engine/security_capability_recipes.py',
        'ARCHITECTURE.md:missing_host_owned_action_tooling_claim:engine/security_semantic_loss_policy.py',
    ]


def test_public_truth_validator_rejects_upstream_action_tooling_as_active_architecture() -> None:
    validator = _load_validator()

    errors = validator.host_owned_gateway_doc_errors({
        'ARCHITECTURE.md': (
            'Main files:\n'
            '- `engine/security_policy_gateway.py`\n'
            '- `govengine.policy.core` / `govengine.tool_registry`\n'
        ),
    })

    assert 'ARCHITECTURE.md:upstream_action_tooling_listed_as_active_main_file' in errors
