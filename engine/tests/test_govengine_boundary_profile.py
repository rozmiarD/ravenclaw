from __future__ import annotations

import json
import sys
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parents[1]
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

import govengine_boundary_profile as boundary_profile


def _report() -> dict:
    return {
        'artifact_type': 'govengine_boundary_report',
        'summary': {
            'profile_count': 1,
            'surface_count': 6,
            'forbidden_profile_ownership_count': 5,
        },
        'boundary': {
            'forbidden_profile_ownership': [
                'govengine_core_modules',
                'sclite_schema_authority',
                'live_execution_authority',
                'credential_or_key_store',
                'carrier_adapter_ownership',
            ],
        },
        'profiles': [{'name': 'ravenclaw'}],
        'surfaces': [
            {'name': 'artifact_governance_core'},
            {'name': 'planning_contracts_core'},
            {'name': 'admission_policy_core'},
            {'name': 'evidence_review_core'},
            {'name': 'controlled_execution_core'},
            {'name': 'security_profile_helpers'},
        ],
    }


def test_boundary_report_evaluation_accepts_govengine_report_shape() -> None:
    status = boundary_profile.evaluate_boundary_report(_report(), source='fixture')

    assert status['status'] == 'passed'
    assert status['profile_names'] == ['ravenclaw']
    assert status['surface_names'] == list(boundary_profile.EXPECTED_SURFACES)
    assert status['failed_checks'] == []
    assert json.loads(json.dumps(status)) == status


def test_boundary_report_evaluation_rejects_profile_drift() -> None:
    report = _report()
    report['profiles'] = [{'name': 'tecrax'}]

    status = boundary_profile.evaluate_boundary_report(report, source='fixture')

    assert status['status'] == 'failed'
    assert status['failed_checks'] == ['ravenclaw_profile_present']


def test_published_govengine_boundary_report_is_required() -> None:
    status = boundary_profile.ravenclaw_boundary_status()

    assert boundary_profile.govengine_boundary_report_available() is True
    assert status['status'] == 'passed'
    assert status['source'] == 'govengine.kernel_boundary_report'
    assert status['profile_names'] == ['ravenclaw']
    assert status['surface_names'] == list(boundary_profile.EXPECTED_SURFACES)
    assert status['failed_checks'] == []
