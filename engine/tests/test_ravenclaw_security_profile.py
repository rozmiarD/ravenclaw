from __future__ import annotations

import json
import sys
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parents[1]
ROOT = ENGINE_DIR.parent
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

import ravenclaw_security_profile as profile


def test_security_profile_manifest_is_json_safe_and_current() -> None:
    manifest = profile.security_profile_manifest()

    assert manifest['profile']['name'] == 'ravenclaw-security'
    assert manifest['profile']['domain'] == 'security-research-runtime'
    assert manifest['package_chain']['ravenclaw'] == '0.16.1'
    assert manifest['package_chain']['govengine'] == '>=0.7.0,<0.8'
    assert manifest['package_chain']['sclite-core'] == '>=0.5.1,<0.6'
    assert manifest['required_govengine_surfaces'] == list(profile.REQUIRED_GOVENGINE_SURFACES)
    assert json.loads(json.dumps(manifest)) == manifest


def test_security_profile_status_requires_readiness_packet_not_adapter() -> None:
    status = profile.ravenclaw_security_profile_status(root=ROOT)

    assert status['status'] == 'passed'
    assert status['failed_checks'] == []
    assert status['missing_paths'] == []
    assert status['checks']['adapter_readiness_packet_only'] is True
    assert status['checks']['carrier_order'] is True


def test_security_profile_rejects_carrier_or_live_authority_drift() -> None:
    manifest = profile.security_profile_manifest()
    manifest['adapter_readiness']['status'] = 'implementation_ready'
    manifest['forbidden_profile_claims'] = [
        item for item in manifest['forbidden_profile_claims'] if item != 'live_execution_authority'
    ]

    status = profile.evaluate_security_profile_manifest(manifest, root=ROOT)

    assert status['status'] == 'failed'
    assert 'adapter_readiness_packet_only' in status['failed_checks']
    assert 'forbidden_claims' in status['failed_checks']
