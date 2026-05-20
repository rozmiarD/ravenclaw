from __future__ import annotations

import importlib.metadata as metadata
import json

import ravenclaw
from ravenclaw import openclaw_readiness, security_profile


def test_ravenclaw_package_version_matches_distribution() -> None:
    assert ravenclaw.__version__ == '0.16.1'
    assert metadata.version('ravenclaw-security') == '0.16.1'


def test_ravenclaw_package_exposes_public_profile_contracts() -> None:
    manifest = security_profile.security_profile_manifest()
    readiness = openclaw_readiness.openclaw_readiness_status()

    assert manifest['artifact_type'] == 'ravenclaw_security_profile_manifest'
    assert manifest['package_chain']['ravenclaw'] == '0.16.1'
    assert manifest['package_chain']['ravenclaw_distribution'] == 'ravenclaw-security'
    assert readiness['status'] == 'passed'
    assert json.loads(json.dumps(manifest)) == manifest
