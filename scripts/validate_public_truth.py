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
import validate_govengine_helper_boundary as govengine_helper_boundary  # noqa: E402
import validate_openclaw_fixture_presenter as openclaw_fixture_presenter  # noqa: E402
import validate_package_runtime_boundary as package_runtime_boundary  # noqa: E402
import validate_reviewer_path as reviewer_path  # noqa: E402
import validate_runtime_state_truth as runtime_state_truth  # noqa: E402


EXPECTED_GOVENGINE_SURFACES = (
    'artifact_governance_core',
    'planning_contracts_core',
    'admission_policy_core',
    'evidence_review_core',
    'domain_profile_sdk',
    'runtime_contract_proofs',
    'controlled_execution_core',
)

CURRENT_DEPENDENCY_DOCS = (
    'README.md',
    'INSTALL.md',
    'QUALITY_SIGNALS.md',
    'THREAT_MODEL.md',
    'VALIDATION.md',
    'VERSION_ROADMAP.md',
    'PUBLISHING.md',
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
    'PUBLISHING.md',
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


def active_readiness_legacy_path_errors(text_by_path: Mapping[str, str]) -> list[str]:
    errors: list[str] = []
    for path, text in text_by_path.items():
        if 'examples/security-contract-proof/' in text:
            errors.append(f'{path}:legacy_proof_fixture_advertised_in_active_readiness_doc')
    return errors


def host_owned_gateway_doc_errors(text_by_path: Mapping[str, str]) -> list[str]:
    required_claims = {
        'ARCHITECTURE.md': '`engine/security_policy_gateway.py`',
        'PUBLIC_STATUS.md': '`engine/security_policy_gateway.py`',
        'VALIDATION.md': '`engine/security_policy_gateway.py`',
        'references/govengine-wrapper-audit.md': 'host-owned active replacement',
        'references/ravenclaw-security-profile-boundary.md': '`engine/security_policy_gateway.py`',
    }
    errors: list[str] = []
    for path, text in text_by_path.items():
        required = required_claims.get(path)
        if required and required not in text:
            errors.append(f'{path}:missing_host_owned_gateway_claim:{required}')
        if path == 'ARCHITECTURE.md' and '- `govengine.policy.gateway`' in text:
            errors.append('ARCHITECTURE.md:upstream_gateway_listed_as_active_main_file')
        if path == 'ARCHITECTURE.md' and 'govengine.policy.core` / `govengine.tool_registry`' in text:
            errors.append('ARCHITECTURE.md:upstream_action_tooling_listed_as_active_main_file')
        if path == 'ARCHITECTURE.md' and any(
            f'- `govengine.contracts.{module}`' in text
            for module in ('signal', 'analysis', 'evidence_policy')
        ):
            errors.append('ARCHITECTURE.md:upstream_security_review_helper_listed_as_active_main_file')
        if path in {'ARCHITECTURE.md', 'PUBLIC_STATUS.md', 'VALIDATION.md', 'references/govengine-wrapper-audit.md', 'references/ravenclaw-security-profile-boundary.md'}:
            for required_local in (
                'engine/security_tool_registry.py',
                'engine/security_policy_core.py',
                'engine/security_capability_recipes.py',
                'engine/security_semantic_loss_policy.py',
                'engine/security_signal_contract.py',
                'engine/security_analysis_contract.py',
                'engine/security_evidence_policy.py',
            ):
                if required_local not in text:
                    errors.append(f'{path}:missing_host_owned_action_tooling_claim:{required_local}')
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
    stack_workflow = _read('.github/workflows/stack-compatibility.yml')

    _require(errors, 'README.md', readme, f'Source: Ravenclaw {version}')
    _require(errors, 'README.md', readme, f'ravenclaw-security=={version}')
    _require(errors, 'README.md', readme, 'Dependency: GovEngine >=0.11.0-alpha')
    _require(errors, 'README.md', readme, 'Dependency: SCLite >=0.8.0a0')
    _require(errors, 'INSTALL.md', _read('INSTALL.md'), f'ravenclaw-security=={version}')
    _require(errors, 'PUBLIC_STATUS.md', public_status, 'narrow public profile/readiness package')
    _require(errors, 'PUBLIC_STATUS.md', public_status, f'ravenclaw-security=={version}')
    _require(errors, 'PUBLIC_STATUS.md', public_status, 'full runtime remains source/reference')
    _require(errors, 'PUBLISHING.md', _read('PUBLISHING.md'), f'ravenclaw-security=={version}')
    _require(errors, 'PUBLISHING.md', _read('PUBLISHING.md'), f'ravenclaw_security-{version}-py3-none-any.whl')
    _require(errors, 'VALIDATION.md', validation, 'neutral-only `0.12.0a0` candidate')
    _require(
        errors,
        'references/ravenclaw-security-profile-boundary.md',
        _read('references/ravenclaw-security-profile-boundary.md'),
        'current 0.18 boundary',
    )
    _require(
        errors,
        'references/repository-publication-readiness-2026-05-08.md',
        _read('references/repository-publication-readiness-2026-05-08.md'),
        'Historical record:',
    )
    security_contract = _read('engine/security_contract_layer.py')
    lifecycle_projection = _read('engine/sclite_lifecycle_projection.py')
    public_demo = _read('engine/public_demo_bundle.py')
    run_pipeline = _read('engine/run_pipeline.py')
    validation_surfaces = _read('scripts/list_public_validation_surfaces.py')
    security_contract_docs = _read('SECURITY_CONTRACT_LAYER.md')
    docs_map = _read('DOCS_MAP.md')
    active_readiness_packet = _read('references/openclaw-adapter-readiness-packet-2026-05-20.md')
    adapter_contract_map = _read('references/openclaw-adapter-contract-map.md')
    scope_fidelity_reference = _read('references/scope-fidelity-report-v0.1.md')
    demo_scenario = _read('scripts/run_demo_scenario.py')
    public_install = _read('scripts/validate_public_install.py')
    errors.extend(host_owned_gateway_doc_errors({
        'ARCHITECTURE.md': _read('ARCHITECTURE.md'),
        'PUBLIC_STATUS.md': public_status,
        'VALIDATION.md': validation,
        'references/govengine-wrapper-audit.md': _read('references/govengine-wrapper-audit.md'),
        'references/ravenclaw-security-profile-boundary.md': _read('references/ravenclaw-security-profile-boundary.md'),
    }))
    _require(errors, 'VALIDATION.md', validation, 'canonical `review_bundle/`')
    _require(errors, 'VALIDATION.md', validation, 'tolerated legacy optional surface')
    _require(errors, 'engine/security_contract_layer.py', security_contract, 'def build_current_lifecycle_artifacts(')
    _require(errors, 'engine/sclite_lifecycle_projection.py', lifecycle_projection, 'def build_current_lifecycle_artifacts(')
    _require(errors, 'engine/public_demo_bundle.py', public_demo, 'materialize_review_bundle')
    _require(errors, 'engine/run_pipeline.py', run_pipeline, 'from security_contract_layer import build_current_lifecycle_artifacts')
    _require(errors, 'SECURITY_CONTRACT_LAYER.md', security_contract_docs, "Ravenclaw-owned local/public-safe current validation receipt")
    _require(errors, 'DOCS_MAP.md', docs_map, 'current scoped-ticket lifecycle')
    _require(errors, 'references/openclaw-adapter-readiness-packet-2026-05-20.md', active_readiness_packet, 'generated `demo-output/intent_contract.json`')
    _require(errors, 'references/openclaw-adapter-contract-map.md', adapter_contract_map, 'generated `demo-output/intent_contract.json`')
    _require(errors, 'scripts/run_demo_scenario.py', demo_scenario, "'version_source': 'executed_import_modules'")
    _require(errors, 'scripts/run_demo_scenario.py', demo_scenario, 'govengine_boundary_source')
    if 'check_govengine_security_profile' in public_install:
        errors.append('scripts/validate_public_install.py:retired_govengine_security_profile_check_retained')
    if 'from govengine.security_profile' in demo_scenario or 'from govengine.security_profile' in public_install:
        errors.append('scripts:retired_govengine_security_profile_import_retained')
    if 'from sclite.artifacts import *' in security_contract:
        errors.append('engine/security_contract_layer.py:wildcard_legacy_import')
    if 'govengine.sclite_adapter' in security_contract or 'govengine.sclite_adapter' in lifecycle_projection:
        errors.append('engine/security_contract_layer.py:govengine_host_projection_dependency')
    if 'build_proof_trace_artifacts' in security_contract:
        errors.append('engine/security_contract_layer.py:legacy_proof_api_retained')
    if 'build_proof_trace_artifacts' in public_demo:
        errors.append('engine/public_demo_bundle.py:legacy_proof_in_active_demo')
    if "'id': 'security_contract_fixture'" in validation_surfaces:
        errors.append('scripts/list_public_validation_surfaces.py:legacy_proof_advertised_as_current_surface')
    if "'id': 'sclite_v02_lifecycle_chain'" in validation_surfaces:
        errors.append('scripts/list_public_validation_surfaces.py:version_named_lifecycle_advertised_as_current_surface')
    errors.extend(active_readiness_legacy_path_errors({
        'DOCS_MAP.md': docs_map,
        'references/openclaw-adapter-readiness-packet-2026-05-20.md': active_readiness_packet,
        'references/openclaw-adapter-contract-map.md': adapter_contract_map,
        'references/scope-fidelity-report-v0.1.md': scope_fidelity_reference,
    }))
    if 'metadata.version' in demo_scenario:
        errors.append('scripts/run_demo_scenario.py:distribution_metadata_used_for_executed_source_truth')
    _require(errors, 'engine/tool_registry.yaml', _read('engine/tool_registry.yaml'), 'planner_profiles_env: GOVENGINE_TOOL_PROFILES')
    _require(errors, '.github/workflows/pytest.yml', workflow, 'python scripts/validate_public_truth.py')
    _require(errors, '.github/workflows/pytest.yml', workflow, 'sclite-core @ git+https://github.com/rozmiarD/SCLite.git@main')
    _require(errors, '.github/workflows/pytest.yml', workflow, 'govengine @ git+https://github.com/rozmiarD/GovEngine.git@main')
    _require(errors, '.github/workflows/pytest.yml', workflow, 'python scripts/validate_package_runtime_boundary.py')
    _require(errors, '.github/workflows/pytest.yml', workflow, 'python scripts/validate_openclaw_fixture_presenter.py')
    _require(errors, '.github/workflows/pytest.yml', workflow, 'public-helper-smoke:')
    _require(errors, '.github/workflows/pytest.yml', workflow, 'package-dry-run:')
    _require(errors, '.github/workflows/pytest.yml', workflow, 'RAVENCLAW_REPORTS_DIR: ${{ runner.temp }}/ravenclaw-reports')
    _require(errors, '.github/workflows/pytest.yml', workflow, 'RAVENCLAW_LOGDASH_DB: ${{ runner.temp }}/ravenclaw-logdash/logs.db')
    _require(errors, '.github/workflows/pytest.yml', workflow, 'rm -rf dist build *.egg-info')
    _require(errors, '.github/workflows/pytest.yml', workflow, 'python -m twine check dist/*')
    _require(errors, '.github/workflows/pytest.yml', workflow, 'python -m pip check')
    _require(errors, '.github/workflows/stack-compatibility.yml', stack_workflow, 'workflow_dispatch:')
    _require(errors, '.github/workflows/stack-compatibility.yml', stack_workflow, 'schedule:')
    _require(errors, '.github/workflows/stack-compatibility.yml', stack_workflow, 'sclite-core @ git+https://github.com/rozmiarD/SCLite.git@main')
    _require(errors, '.github/workflows/stack-compatibility.yml', stack_workflow, 'govengine @ git+https://github.com/rozmiarD/GovEngine.git@main')
    _require(errors, '.github/workflows/stack-compatibility.yml', stack_workflow, 'RAVENCLAW_REPORTS_DIR: ${{ runner.temp }}/ravenclaw-reports')
    _require(errors, '.github/workflows/stack-compatibility.yml', stack_workflow, 'engine/tests/test_govengine_dependency_isolation.py')

    for path in CURRENT_DEPENDENCY_DOCS:
        text = _read(path)
        _require(errors, path, text, govengine_dep)
        _require(errors, path, text, sclite_dep)

    errors.extend(stale_current_dependency_errors({path: _read(path) for path in CURRENT_DEPENDENCY_DOCS}, govengine_dep))
    errors.extend(forbidden_claim_errors(PUBLIC_TRUTH_DOCS))
    errors.extend(f'extraction_roadmap:{error}' for error in extraction_roadmap.collect_errors())
    errors.extend(f'govengine_helper_boundary:{error}' for error in govengine_helper_boundary.collect_errors())
    errors.extend(f'package_runtime_boundary:{error}' for error in package_runtime_boundary.collect_errors())
    errors.extend(f'openclaw_fixture_presenter:{error}' for error in openclaw_fixture_presenter.collect_errors())
    errors.extend(f'reviewer_path:{error}' for error in reviewer_path.collect_errors())
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
