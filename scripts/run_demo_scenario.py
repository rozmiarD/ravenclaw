#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
ROOT = Path(os.getenv('RAVENCLAW_WORKSPACE') or DEFAULT_ROOT).expanduser().resolve()
ENGINE_DIR = ROOT / 'engine'
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

import public_demo_bundle  # type: ignore
from govengine import __version__ as govengine_version  # type: ignore
from govengine.security_profile import assert_security_profile_boundary, security_profile_index  # type: ignore
from sclite import __version__ as sclite_version  # type: ignore
from sclite.bundles import review_bundle  # type: ignore
from sclite.artifacts import validate_artifact  # type: ignore
from sclite.integrity import verify_artifact_chain_manifest  # type: ignore


DEMO_SCENARIO_TRACE = (
    'intent -> policy decision -> execution contract -> scoped execution ticket -> '
    'dry-run execution receipt -> evidence contract -> artifact chain manifest -> review bundle'
)


def _load_json(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError(f'{path.name}: expected JSON object')
    return data


def _relative_artifact_paths(out_dir: Path) -> Dict[str, str]:
    names = [
        'demo_scenario_summary.json',
        'demo_scenario_summary.md',
        'bundle_summary.json',
        'bundle_summary.md',
        'intent_contract.json',
        'policy_decision.v0.2.json',
        'execution_contract.json',
        'execution_ticket.json',
        'execution_receipt.v0.2.json',
        'evidence_contract.json',
        'artifact_chain_manifest.json',
        'review_bundle/verification_receipt.json',
        'review_bundle/REVIEW.md',
    ]
    paths: Dict[str, str] = {}
    for name in names:
        path = out_dir / name
        try:
            paths[name] = path.relative_to(ROOT).as_posix()
        except ValueError:
            paths[name] = str(path)
    return paths


def _reviewer_commands(out_dir: Path) -> List[str]:
    try:
        manifest = (out_dir / 'artifact_chain_manifest.json').relative_to(ROOT).as_posix()
    except ValueError:
        manifest = str(out_dir / 'artifact_chain_manifest.json')
    return [
        './scripts/bootstrap_public_demo.sh scenario',
        f'sclite validate-chain {manifest}',
        f'sclite verify-lifecycle {manifest}',
        f'sclite review {out_dir / "review_bundle"} --format summary --fail-on review',
        'python scripts/validate_public_install.py --dev',
    ]


def run_demo_scenario(*, output_dir: str = 'demo-output/demo-scenario') -> Dict[str, Any]:
    """Generate and verify the reviewer-facing Ravenclaw/GovEngine/SCLite demo.

    The demo intentionally stays local and dry-run only. It shows that Ravenclaw
    can produce a public-safe contract trace, GovEngine exposes the reusable
    security-profile helper boundary, and SCLite validates/hash-links the
    lifecycle artifacts.
    """

    result = public_demo_bundle.generate_bundle(output_dir=output_dir)
    out_dir = Path(result['output_dir'])

    lifecycle_files = list(result['summary']['lifecycle_trace_files'])
    for filename in lifecycle_files:
        artifact = _load_json(out_dir / filename)
        validate_artifact(artifact, str(artifact['schema_ref']))

    chain_result = verify_artifact_chain_manifest(_load_json(out_dir / 'artifact_chain_manifest.json'), root=out_dir)
    review_record = review_bundle(out_dir / 'review_bundle')
    assert_security_profile_boundary()
    profile = security_profile_index()

    scenario_summary = {
        'demo': 'ravenclaw_demo_scenario',
        'status': 'passed' if chain_result.get('status') == 'passed' and review_record.get('verdict') == 'pass' else 'failed',
        'workspace_root': str(ROOT),
        'output_dir': str(out_dir),
        'trace': DEMO_SCENARIO_TRACE,
        'ravenclaw': {
            'runtime_mode': result['summary']['runtime_mode'],
            'engine_status': result['summary']['engine_status'],
            'execution_adapter': result['summary']['integration_adapters']['execution']['mode'],
            'lifecycle_trace_files': lifecycle_files,
        },
        'package_chain': {
            'version_source': 'executed_import_modules',
            'govengine': govengine_version,
            'sclite-core': sclite_version,
        },
        'govengine': {
            'entrypoint': profile['entrypoint'],
            'surface': profile['surface']['name'],
            'groups': [group['name'] for group in profile['groups']],
        },
        'sclite': {
            'validated_lifecycle_files': lifecycle_files,
            'artifact_chain_status': chain_result['status'],
            'checked_entries': chain_result['checked_entries'],
            'review_bundle_verdict': review_record['verdict'],
        },
        'reviewer_commands': _reviewer_commands(out_dir),
        'artifact_paths': _relative_artifact_paths(out_dir),
        'non_claims': [
            'no live target scanning',
            'no raw/private evidence publication',
            'no production deployment readiness claim',
            'no adapter authority expansion',
        ],
    }
    (out_dir / 'demo_scenario_summary.json').write_text(json.dumps(scenario_summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (out_dir / 'demo_scenario_summary.md').write_text(build_demo_scenario_markdown(scenario_summary), encoding='utf-8')
    return scenario_summary


def build_demo_scenario_markdown(summary: Dict[str, Any]) -> str:
    lines = [
        '# Ravenclaw Demo Scenario Summary',
        '',
        f"- status: `{summary['status']}`",
        f"- runtime_mode: `{summary['ravenclaw']['runtime_mode']}`",
        f"- engine_status: `{summary['ravenclaw']['engine_status']}`",
        f"- execution_adapter: `{summary['ravenclaw']['execution_adapter']}`",
        f"- govengine_version: `{summary.get('package_chain', {}).get('govengine', '')}`",
        f"- sclite_core_version: `{summary.get('package_chain', {}).get('sclite-core', '')}`",
        f"- govengine_surface: `{summary['govengine']['surface']}`",
        f"- sclite_chain_status: `{summary['sclite']['artifact_chain_status']}`",
        f"- sclite_review_bundle_verdict: `{summary['sclite']['review_bundle_verdict']}`",
        '',
        '## Trace',
        '',
        f"`{summary['trace']}`",
        '',
        '## Reviewer commands',
        '',
        *[f"```bash\n{command}\n```" for command in summary.get('reviewer_commands', [])],
        '',
        '## Generated artifacts',
        '',
        *[f"- `{name}` -> `{path}`" for name, path in sorted(summary.get('artifact_paths', {}).items())],
        '',
        '## GovEngine groups',
        '',
        *[f"- `{name}`" for name in summary['govengine']['groups']],
        '',
        '## SCLite checked entries',
        '',
        *[f"- `{name}`" for name in summary['sclite']['checked_entries']],
        '',
        '## Non-claims',
        '',
        *[f"- {claim}" for claim in summary['non_claims']],
    ]
    return '\n'.join(lines) + '\n'


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Run the public-safe Ravenclaw/GovEngine/SCLite demo scenario.')
    parser.add_argument('--output-dir', default='demo-output/demo-scenario')
    args = parser.parse_args(argv)
    summary = run_demo_scenario(output_dir=str(args.output_dir))
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
