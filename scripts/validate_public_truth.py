#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path
from typing import Iterable, Mapping

ROOT = Path(__file__).resolve().parents[1]
ENGINE_DIR = ROOT / 'engine'
SCRIPTS_DIR = ROOT / 'scripts'
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import ravenclaw  # noqa: E402
import ravenclaw_security_profile as security_profile  # noqa: E402
import validate_extraction_roadmap as extraction_roadmap  # noqa: E402
import validate_runtime_state_truth as runtime_state_truth  # noqa: E402


EXPECTED_GOVENGINE_SURFACES = (
    'artifact_governance_core',
    'planning_contracts_core',
    'admission_policy_core',
    'evidence_review_core',
    'domain_profile_sdk',
    'runtime_contract_proofs',
    'controlled_execution_core',
    'security_profile_helpers',
)

CURRENT_DEPENDENCY_DOCS = (
    'README.md',
    'INSTALL.md',
    'QUALITY_SIGNALS.md',
    'THREAT_MODEL.md',
    'VALIDATION.md',
    'VERSION_ROADMAP.md',
    'SECURITY_CONTRACT_LAYER.md',
    'references/ravenclaw-security-profile-boundary.md',
    'references/openclaw-adapter-readiness-packet-2026-05-20.md',
    'references/govengine-wrapper-audit.md',
    'references/govengine-extraction-readiness-roadmap.md',
)

PUBLIC_TRUTH_DOCS = (
    'README.md',
    'INSTALL.md',
    'PUBLIC_STATUS.md',
    'VALIDATION.md',
    'QUALITY_SIGNALS.md',
    'PROOF_OF_VALUE.md',
    'ARCHITECTURE_OVERVIEW.md',
    'THREAT_MODEL.md',
    'VERSION_ROADMAP.md',
    'SECURITY_CONTRACT_LAYER.md',
    'references/ravenclaw-security-profile-boundary.md',
    'references/openclaw-adapter-readiness-packet-2026-05-20.md',
    'references/govengine-extraction-readiness-roadmap.md',
)

FORBIDDEN_IMPLEMENTATION_CLAIMS = (
    'OpenClaw adapter is implemented',
    'OpenClaw Skill is implemented',
    'MCP adapter is implemented',
    'MCP implementation is complete',
    'A2A adapter is implemented',
    'A2A implementation is complete',
)


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def _pyproject() -> Mapping[str, object]:
    return tomllib.loads(_read('pyproject.toml'))['project']


def _project_dependency(project: Mapping[str, object], name: str) -> str:
    prefix = f'{name}>='
    for dependency in project.get('dependencies', []):  # type: ignore[union-attr]
        text = str(dependency)
        if text.startswith(prefix):
            return text
    raise AssertionError(f'missing_dependency:{name}')


def _require(errors: list[str], path: str, text: str, expected: str) -> None:
    if expected not in text:
        errors.append(f'{path}:missing:{expected}')


def stale_current_dependency_errors(text_by_path: Mapping[str, str], expected_govengine: str) -> list[str]:
    expected_fragment = expected_govengine.replace('govengine', '')
    stale = re.compile(
        r'(?i)(current|active|now|requires|consumes|dependency baseline|package chain|public install validation)'
        r'.{0,160}govengine>=0\.(1|2|3|4|5|6|7)\.[^`\s,)]*',
        flags=re.DOTALL,
    )
    errors: list[str] = []
    for path, text in text_by_path.items():
        for match in stale.finditer(text):
            errors.append(f'{path}:stale_current_govengine_dependency:{match.group(0).strip()}')
    return errors


def forbidden_claim_errors(paths: Iterable[str]) -> list[str]:
    errors: list[str] = []
    for path in paths:
        text = _read(path)
        for claim in FORBIDDEN_IMPLEMENTATION_CLAIMS:
            if claim in text:
                errors.append(f'{path}:forbidden_implementation_claim:{claim}')
    return errors


def collect_errors() -> list[str]:
    errors: list[str] = []
    project = _pyproject()
    version = str(project['version'])
    govengine_dep = _project_dependency(project, 'govengine')
    sclite_dep = _project_dependency(project, 'sclite-core')
    manifest = security_profile.security_profile_manifest()

    if ravenclaw.__version__ != version:
        errors.append(f'package_version_mismatch:{ravenclaw.__version__}!={version}')
    if project['name'] != 'ravenclaw-security':
        errors.append(f'distribution_name_mismatch:{project["name"]}')
    if manifest['package_chain']['ravenclaw'] != version:
        errors.append(f'manifest_ravenclaw_version_mismatch:{manifest["package_chain"]["ravenclaw"]}!={version}')
    if manifest['package_chain']['govengine'] != govengine_dep.removeprefix('govengine'):
        errors.append(f'manifest_govengine_dependency_mismatch:{manifest["package_chain"]["govengine"]}!={govengine_dep}')
    if manifest['package_chain']['sclite-core'] != sclite_dep.removeprefix('sclite-core'):
        errors.append(f'manifest_sclite_dependency_mismatch:{manifest["package_chain"]["sclite-core"]}!={sclite_dep}')
    if tuple(manifest['required_govengine_surfaces']) != EXPECTED_GOVENGINE_SURFACES:
        errors.append(f'manifest_surface_mismatch:{manifest["required_govengine_surfaces"]}')

    readme = _read('README.md')
    public_status = _read('PUBLIC_STATUS.md')
    validation = _read('VALIDATION.md')
    workflow = _read('.github/workflows/pytest.yml')

    _require(errors, 'README.md', readme, f'Source: Ravenclaw {version}')
    _require(errors, 'README.md', readme, f'ravenclaw-security=={version}')
    _require(errors, 'README.md', readme, 'Dependency: GovEngine >=0.10.1-alpha')
    _require(errors, 'README.md', readme, 'Dependency: SCLite >=0.6.0a0')
    _require(errors, 'INSTALL.md', _read('INSTALL.md'), f'ravenclaw-security=={version}')
    _require(errors, 'PUBLIC_STATUS.md', public_status, 'narrow public profile/readiness package')
    _require(errors, 'PUBLIC_STATUS.md', public_status, f'ravenclaw-security=={version}')
    _require(errors, 'PUBLIC_STATUS.md', public_status, 'full runtime remains source/reference')
    _require(errors, 'VALIDATION.md', validation, 'GovEngine `0.10.1-alpha`')
    _require(errors, '.github/workflows/pytest.yml', workflow, 'python scripts/validate_public_truth.py')
    _require(errors, '.github/workflows/pytest.yml', workflow, 'govengine @ git+https://github.com/rozmiarD/GovEngine.git@main')

    for path in CURRENT_DEPENDENCY_DOCS:
        text = _read(path)
        _require(errors, path, text, govengine_dep)
        _require(errors, path, text, sclite_dep)

    errors.extend(stale_current_dependency_errors({path: _read(path) for path in CURRENT_DEPENDENCY_DOCS}, govengine_dep))
    errors.extend(forbidden_claim_errors(PUBLIC_TRUTH_DOCS))
    errors.extend(f'extraction_roadmap:{error}' for error in extraction_roadmap.collect_errors())
    errors.extend(f'runtime_state_truth:{error}' for error in runtime_state_truth.collect_errors())

    for path in PUBLIC_TRUTH_DOCS:
        text = _read(path)
        if 'production-ready' in text.lower() and 'not production-ready' not in text.lower():
            errors.append(f'{path}:production_ready_overclaim')

    return errors


def main() -> int:
    errors = collect_errors()
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    project = _pyproject()
    version = str(project['version'])
    govengine_dep = _project_dependency(project, 'govengine')
    sclite_dep = _project_dependency(project, 'sclite-core')
    print(f'public_truth_ok:ravenclaw-security=={version}:{govengine_dep}:{sclite_dep}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
