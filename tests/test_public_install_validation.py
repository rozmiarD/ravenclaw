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
    assert data['govengine_surface_registry']['actual'] == [
        'artifact_governance_core',
        'controlled_execution_core',
        'security_profile_helpers',
    ]
    assert data['govengine_surface_registry']['optional_profile']['security_profile_helpers'] is True
    assert data['govengine_security_profile']['status'] == 'passed'
    assert data['govengine_security_profile']['source'] == 'govengine.security_profile'
    assert data['govengine_security_profile']['upstream_available'] is True
    assert data['govengine_security_profile']['actual_groups'] == [
        'action_tooling',
        'policy_scope',
        'review_contracts',
    ]
    assert 'govengine.action_schema' in data['govengine_security_profile']['expected_modules']
    assert data['govengine_security_profile']['surface']['name'] == 'security_profile_helpers'
    assert data['govengine_boundary_profile']['status'] in {'passed', 'unavailable'}
    if data['govengine_boundary_profile']['status'] == 'unavailable':
        assert data['govengine_boundary_profile']['reason_code'] == 'govengine_boundary_report_unavailable'
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
