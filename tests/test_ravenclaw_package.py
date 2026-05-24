from __future__ import annotations

import importlib.metadata as metadata
import json
from pathlib import Path
import tomllib

import ravenclaw
from ravenclaw import openclaw_readiness, security_profile


ROOT = Path(__file__).resolve().parents[1]


def _distribution_or_source_version() -> str:
    try:
        return metadata.version('ravenclaw-security')
    except metadata.PackageNotFoundError:
        pyproject = tomllib.loads((ROOT / 'pyproject.toml').read_text(encoding='utf-8'))
        return str(pyproject['project']['version'])


def test_ravenclaw_package_version_matches_distribution() -> None:
    assert ravenclaw.__version__ == '0.18.0'
    assert _distribution_or_source_version() == '0.18.0'


def test_ravenclaw_package_exposes_public_profile_contracts() -> None:
    manifest = security_profile.security_profile_manifest()
    readiness = openclaw_readiness.openclaw_readiness_status()

    assert manifest['artifact_type'] == 'ravenclaw_security_profile_manifest'
    assert manifest['package_chain']['ravenclaw'] == '0.18.0'
    assert manifest['package_chain']['ravenclaw_distribution'] == 'ravenclaw-security'
    assert readiness['status'] == 'passed'
    assert json.loads(json.dumps(manifest)) == manifest
