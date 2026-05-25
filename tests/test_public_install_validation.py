from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'validate_public_install.py'


def test_public_install_validation_runtime_json() -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), '--json', '--skip-pip-check'],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(proc.stdout)
    assert data['artifact_type'] == 'ravenclaw_public_install_validation'
    assert data['schema_version'] == 'v0.1'
    assert data['mode'] == 'runtime'
    assert data['status'] == 'passed'
    distributions = {dep['distribution'] for dep in data['dependencies']}
    assert {'PyYAML', 'sclite-core', 'govengine'} <= distributions
    assert data['pip_check'] is None
    assert data['govengine_surface_registry']['status'] == 'passed'
    assert data['govengine_surface_registry']['required'] == [
        'artifact_governance_core',
        'planning_contracts_core',
        'admission_policy_core',
        'evidence_review_core',
        'domain_profile_sdk',
        'runtime_contract_proofs',
        'controlled_execution_core',
    ]
    assert 'security_profile_helpers' not in data['govengine_surface_registry']['required']
    assert data['govengine_surface_registry']['missing_required'] == []
    assert data['govengine_surface_registry']['required_optional'] == []
    assert data['govengine_surface_registry']['tolerated_legacy_optional'] in ([], ['security_profile_helpers'])
    assert 'govengine_security_profile' not in data
    assert data['govengine_boundary_profile']['status'] == 'passed'
    assert data['govengine_boundary_profile']['available'] is True
    assert data['govengine_boundary_profile']['source'] == 'govengine.kernel_boundary_report'
    assert data['govengine_boundary_profile']['failed_checks'] == []
    assert data['ravenclaw_security_profile']['status'] == 'passed'
    assert data['ravenclaw_security_profile']['available'] is True
    assert data['ravenclaw_security_profile']['profile_name'] == 'ravenclaw-security'
    assert data['ravenclaw_security_profile']['checks']['adapter_readiness_packet_only'] is True
    assert data['ravenclaw_security_profile']['failed_checks'] == []
    assert any('live target execution' in item for item in data['non_claims'])


def test_public_install_validation_dev_mode_includes_test_dependencies() -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), '--json', '--dev', '--skip-pip-check'],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(proc.stdout)
    assert data['mode'] == 'dev'
    distributions = {dep['distribution'] for dep in data['dependencies']}
    assert {'pytest', 'Flask'} <= distributions
