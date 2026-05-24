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

SCORECARD_ARTIFACT_TYPE = 'proof_of_value_scorecard'
SCORECARD_SCHEMA_VERSION = 'v0.1'
SCORECARD_SCHEMA_REF = 'schemas/proof_of_value_scorecard.v0.1.schema.json'

DIMENSIONS: list[dict[str, Any]] = [
    {
        'id': 'scope_fidelity',
        'title': 'Scope fidelity',
        'evidence_paths': [
            'examples/scope-fidelity-report',
            'scripts/build_scope_fidelity_report.py',
            'schemas/scope_fidelity_report.v0.1.schema.json',
            'schemas/scope_fidelity_report.v0.2.schema.json',
        ],
        'claim': 'Target-binding/request-shape drift can be classified from local public-safe artifacts.',
        'non_claim': 'Does not scan hosts or infer authorization beyond supplied artifacts.',
    },
    {
        'id': 'policy_decision_clarity',
        'title': 'Policy decision clarity',
        'evidence_paths': ['schemas/policy_decision.v0.2.schema.json', 'engine/public_demo_bundle.py', 'SECURITY_CONTRACT_LAYER.md'],
        'claim': 'Approval/rejection semantics are structured and inspectable in the current lifecycle/review-bundle path.',
        'non_claim': 'Does not prove every live policy configuration is correct.',
    },
    {
        'id': 'execution_spec_accountability',
        'title': 'Execution spec accountability',
        'evidence_paths': ['schemas/execution_contract.v0.2.schema.json', 'schemas/execution_ticket.v0.3.schema.json', 'engine/public_demo_bundle.py'],
        'claim': 'The execution contract and scoped ticket can be reviewed without trusting free-form model text.',
        'non_claim': 'Does not authorize live command execution.',
    },
    {
        'id': 'dry_run_evidence_separation',
        'title': 'Dry-run/evidence separation',
        'evidence_paths': ['schemas/execution_receipt.v0.2.schema.json', 'schemas/evidence_contract.v0.2.schema.json', 'engine/public_demo_bundle.py'],
        'claim': 'Current lifecycle receipts and evidence contracts explicitly separate illustrative proof from live evidence.',
        'non_claim': 'Does not claim live vulnerability evidence.',
    },
    {
        'id': 'replayability',
        'title': 'Replayability',
        'evidence_paths': ['examples/replayable-truth-runtime', 'scripts/validate_replayable_truth_fixture.py', 'REPLAYABLE_TRUTH_RUNTIME.md'],
        'claim': 'Representative runtime decisions can be replayed offline from public-safe fixtures.',
        'non_claim': 'Does not replay private operator state.',
    },
    {
        'id': 'snapshot_completeness',
        'title': 'Snapshot completeness',
        'evidence_paths': ['scripts/build_public_snapshot_manifest.py', 'schemas/public_snapshot_manifest.v0.1.schema.json', 'REVIEWER_VALIDATION_GUIDE.md'],
        'claim': 'Advertised validation surfaces can be mapped to concrete files in an assembled snapshot.',
        'non_claim': 'Does not prove the snapshot is the full live operator workspace.',
    },
    {
        'id': 'non_claim_preservation',
        'title': 'Non-claim preservation',
        'evidence_paths': ['PROOF_OF_VALUE.md', 'QUALITY_SIGNALS.md', 'PUBLIC_STATUS.md'],
        'claim': 'Public docs explicitly preserve non-claims around live exploits, production readiness, and protocol completeness.',
        'non_claim': 'Does not prove superior real-world outcomes by itself.',
    },
]


def _path_status(root: Path, rel: str) -> dict[str, Any]:
    return {'path': rel, 'present': (root / rel).exists()}


def build_scorecard(root: Path = ROOT) -> dict[str, Any]:
    dimensions: list[dict[str, Any]] = []
    for dimension in DIMENSIONS:
        evidence = [_path_status(root, rel) for rel in dimension['evidence_paths']]
        status = 'passed' if all(path['present'] for path in evidence) else 'failed'
        dimensions.append({
            'id': dimension['id'],
            'title': dimension['title'],
            'status': status,
            'evidence_paths': evidence,
            'claim': dimension['claim'],
            'non_claim': dimension['non_claim'],
        })
    failed = [dimension for dimension in dimensions if dimension['status'] != 'passed']
    scorecard = {
        'artifact_type': SCORECARD_ARTIFACT_TYPE,
        'schema_version': SCORECARD_SCHEMA_VERSION,
        'schema_ref': SCORECARD_SCHEMA_REF,
        'summary': {
            'dimension_count': len(dimensions),
            'passed': len(dimensions) - len(failed),
            'failed': len(failed),
            'status': 'passed' if not failed else 'failed',
        },
        'scope': {
            'public_safe': True,
            'dry_run_or_local_only': True,
            'live_target_execution': False,
            'protocol_adapter_work': False,
            'live_vulnerability_claim': False,
        },
        'dimensions': dimensions,
    }
    validate_scorecard_schema(scorecard)
    return scorecard


def validate_scorecard_schema(scorecard: Mapping[str, Any], root: Path = ROOT) -> None:
    scl.validate_schema_ref(SCORECARD_SCHEMA_REF, scorecard, root=root)


def print_markdown(scorecard: Mapping[str, Any]) -> None:
    print('# Proof-of-Value Scorecard')
    print('')
    print('This scorecard summarizes public-safe benchmark dimensions for Ravenclaw. It does not claim live vulnerability discovery, production readiness, or protocol-adapter completeness.')
    print('')
    print(f"status: `{scorecard['summary']['status']}`")
    print(f"dimensions: `{scorecard['summary']['dimension_count']}`")
    print(f"passed: `{scorecard['summary']['passed']}`")
    print(f"failed: `{scorecard['summary']['failed']}`")
    print('')
    print('| Dimension | Status | Evidence | Non-claim |')
    print('| --- | --- | --- | --- |')
    for dimension in scorecard['dimensions']:
        evidence = '<br>'.join(f"`{path['path']}`" for path in dimension['evidence_paths'])
        print(f"| {dimension['title']} | `{dimension['status']}` | {evidence} | {dimension['non_claim']} |")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Build a public-safe Ravenclaw proof-of-value scorecard.')
    parser.add_argument('root', nargs='?', default='.', help='repo or assembled snapshot root to inspect')
    parser.add_argument('--format', choices=['json', 'markdown'], default='json')
    parser.add_argument('--check', action='store_true', help='fail if any scorecard dimension is missing evidence paths')
    args = parser.parse_args(argv)

    scorecard = build_scorecard(Path(args.root).resolve())
    if args.format == 'markdown':
        print_markdown(scorecard)
    else:
        print(json.dumps(scorecard, indent=2, sort_keys=True))
    return 0 if (not args.check or scorecard['summary']['status'] == 'passed') else 1


if __name__ == '__main__':
    raise SystemExit(main())
