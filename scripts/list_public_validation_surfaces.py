#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
ENGINE_DIR = ROOT / 'engine'
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

import security_contract_layer as scl  # type: ignore

INDEX_ARTIFACT_TYPE = 'public_validation_surface_index'
INDEX_SCHEMA_VERSION = 'v0.1'
INDEX_SCHEMA_REF = 'schemas/public_validation_surface_index.v0.1.schema.json'

VALIDATION_SURFACES: list[dict[str, Any]] = [
    {
        'id': 'public_validation_surface_index',
        'title': 'Public validation surface index',
        'command': 'python scripts/list_public_validation_surfaces.py --format json --check',
        'paths': ['scripts/list_public_validation_surfaces.py', 'schemas/public_validation_surface_index.v0.1.schema.json', 'references/public-validation-surface-index-v0.1.md'],
        'claim': 'Lists local/public-safe validation entry points with explicit claims, non-claims, and boundaries.',
        'non_claim': 'Does not run validation checks or authorize publication by itself.',
    },
    {
        'id': 'repo_pytest',
        'title': 'Repository pytest suite',
        'command': 'python -m pytest -q',
        'paths': ['tests', 'engine/tests', '.github/workflows/pytest.yml'],
        'claim': 'Broad regression coverage for public runtime, policy, Logdash, and proof surfaces.',
        'non_claim': 'Does not prove live deployment readiness or authorize live target execution.',
    },
    {
        'id': 'github_actions_pytest_matrix',
        'title': 'GitHub Actions pytest slice matrix',
        'command': 'for slice in contracts_policy auto_campaign runtime_core runtime_runner logdash misc_public; do python scripts/run_pytest_slice.py "$slice"; done',
        'paths': ['scripts/run_pytest_slice.py', '.github/workflows/pytest.yml'],
        'claim': 'Local reproduction of the public CI pytest partitioning.',
        'non_claim': 'Does not replace post-push GitHub Actions status checks.',
    },
    {
        'id': 'security_contract_fixture',
        'title': 'Security Contract proof fixture',
        'command': 'PYTHONDONTWRITEBYTECODE=1 python scripts/validate_security_contract_fixtures.py examples/security-contract-proof',
        'paths': ['examples/security-contract-proof', 'scripts/validate_security_contract_fixtures.py', 'schemas'],
        'claim': 'Schema-backed dry-run proof trace from scope/input through evidence summary.',
        'non_claim': 'Does not claim live vulnerability evidence.',
    },
    {
        'id': 'security_contract_validation_receipt',
        'title': 'Security Contract validation receipt',
        'command': 'python scripts/run_security_contract_validation.py --include-pytest --include-github-actions-matrix',
        'paths': ['scripts/run_security_contract_validation.py', 'schemas/security_contract_validation_receipt.v0.1.schema.json'],
        'claim': 'Machine-readable receipt for public-safe fixture, snapshot, residue, focused pytest, and CI parity checks.',
        'non_claim': 'Does not authorize publication, protocol adapter work, or live target testing.',
    },
    {
        'id': 'replayable_truth_runtime_fixture',
        'title': 'Replayable Truth Runtime fixture',
        'command': 'PYTHONDONTWRITEBYTECODE=1 python scripts/validate_replayable_truth_fixture.py examples/replayable-truth-runtime',
        'paths': ['examples/replayable-truth-runtime', 'scripts/validate_replayable_truth_fixture.py'],
        'claim': 'Offline replay fixture showing deterministic governance-aware runtime truth.',
        'non_claim': 'Does not replay live private operator state.',
    },
    {
        'id': 'scope_fidelity_fixture',
        'title': 'Scope Fidelity fixtures and CLI',
        'command': 'PYTHONDONTWRITEBYTECODE=1 python scripts/validate_scope_fidelity_fixtures.py examples/scope-fidelity-report',
        'paths': ['examples/scope-fidelity-report', 'scripts/validate_scope_fidelity_fixtures.py', 'scripts/build_scope_fidelity_report.py'],
        'claim': 'Static host-binding evidence for pass/fail/review scope decisions.',
        'non_claim': 'Does not scan hosts or infer authorization beyond supplied local artifacts.',
    },
    {
        'id': 'public_snapshot_residue_audit',
        'title': 'Public snapshot residue audit',
        'command': 'python scripts/audit_public_snapshot_residue.py .',
        'paths': ['scripts/audit_public_snapshot_residue.py', 'PUBLISHING.md'],
        'claim': 'Checks a prepared public tree for private/generated residue blockers.',
        'non_claim': 'Warnings require human review and are not a blanket publication approval.',
    },
    {
        'id': 'demo_bundle_smoke',
        'title': 'Public demo bundle smoke test',
        'command': 'bin/demo-bundle --print-summary',
        'paths': ['bin/demo-bundle', 'DEMO.md'],
        'claim': 'Local dry-run demo path produces a compact public-safe summary.',
        'non_claim': 'Demo output is illustrative, not production telemetry.',
    },

    {
        'id': 'public_snapshot_manifest',
        'title': 'Public snapshot manifest',
        'command': 'python scripts/build_public_snapshot_manifest.py . --check',
        'paths': ['scripts/build_public_snapshot_manifest.py', 'schemas/public_snapshot_manifest.v0.1.schema.json', 'references/public-snapshot-manifest-v0.1.md'],
        'claim': 'Maps public validation surfaces to concrete files present in an assembled public snapshot.',
        'non_claim': 'Does not authorize publication or prove production deployment readiness.',
    },
    {
        'id': 'proof_of_value_scorecard',
        'title': 'Proof-of-Value scorecard',
        'command': 'python scripts/build_proof_of_value_scorecard.py . --check',
        'paths': ['scripts/build_proof_of_value_scorecard.py', 'scripts/validate_proof_of_value_scorecard.py', 'schemas/proof_of_value_scorecard.v0.1.schema.json', 'references/proof-of-value-scorecard-v0.1.md', 'examples/proof-of-value-scorecard', 'PROOF_OF_VALUE.md'],
        'claim': 'Machine-readable public-safe benchmark checklist for Ravenclaw governance/reviewability value dimensions.',
        'non_claim': 'Does not claim live vulnerability discovery, production readiness, or protocol-adapter completeness.',
    },

]

COMMON_BOUNDARIES = {
    'public_safe': True,
    'dry_run_or_local_only': True,
    'live_target_execution': False,
    'protocol_adapter_work': False,
}


def _missing_paths(surface: Mapping[str, Any], root: Path) -> list[str]:
    missing: list[str] = []
    for rel in surface['paths']:
        if not (root / rel).exists():
            missing.append(rel)
    return missing


def build_index(root: Path = ROOT) -> dict[str, Any]:
    surfaces: list[dict[str, Any]] = []
    for surface in VALIDATION_SURFACES:
        item = dict(surface)
        item['boundaries'] = dict(COMMON_BOUNDARIES)
        item['missing_paths'] = _missing_paths(surface, root)
        surfaces.append(item)
    return {
        'artifact_type': INDEX_ARTIFACT_TYPE,
        'schema_version': INDEX_SCHEMA_VERSION,
        'schema_ref': INDEX_SCHEMA_REF,
        'summary': {
            'surface_count': len(surfaces),
            'missing_path_count': sum(len(surface['missing_paths']) for surface in surfaces),
        },
        'surfaces': surfaces,
    }


def validate_index_schema(index: Mapping[str, Any], root: Path = ROOT) -> None:
    scl.validate_schema_ref(INDEX_SCHEMA_REF, index, root=root)


def print_markdown(index: Mapping[str, Any]) -> None:
    print('# Public Validation Surface Index')
    print('')
    print('These checks are local/public-safe entry points for understanding Ravenclaw validation. They do not authorize live target execution or protocol adapter work.')
    print('')
    for surface in index['surfaces']:
        print(f"## {surface['title']}")
        print('')
        print(f"- id: `{surface['id']}`")
        print(f"- command: `{surface['command']}`")
        print(f"- validates: {surface['claim']}")
        print(f"- does not claim: {surface['non_claim']}")
        if surface['missing_paths']:
            print(f"- missing paths: {', '.join(surface['missing_paths'])}")
        print('')


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='List Ravenclaw public validation surfaces and their evidence boundaries.')
    parser.add_argument('--format', choices=['markdown', 'json'], default='markdown')
    parser.add_argument('--check', action='store_true', help='fail if any referenced validation path is missing')
    args = parser.parse_args(argv)

    index = build_index()
    validate_index_schema(index)
    if args.format == 'json':
        print(json.dumps(index, indent=2, sort_keys=True))
    else:
        print_markdown(index)

    if args.check and index['summary']['missing_path_count']:
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
