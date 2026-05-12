#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
ROOT = Path(os.getenv('RAVENCLAW_WORKSPACE') or DEFAULT_ROOT).expanduser().resolve()
ENGINE_DIR = ROOT / 'engine'
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

import public_demo_bundle  # type: ignore
from govengine.security_profile import assert_security_profile_boundary, security_profile_index  # type: ignore
from sclite.artifacts import validate_artifact  # type: ignore
from sclite.integrity import verify_artifact_chain_manifest  # type: ignore


DEMO_SCENARIO_TRACE = (
    'scope/input -> policy decision -> prepared execution spec -> approved execution spec -> '
    'dry-run execution receipt -> evidence contract -> artifact chain manifest'
)


def _load_json(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError(f'{path.name}: expected JSON object')
    return data


def run_demo_scenario(*, output_dir: str = 'demo-output/demo-scenario') -> Dict[str, Any]:
    """Generate and verify the reviewer-facing Ravenclaw/GovEngine/SCLite demo.

    The demo intentionally stays local and dry-run only. It proves that Ravenclaw
    can produce a public-safe contract trace, GovEngine exposes the reusable
    security-profile helper boundary, and SCLite validates/hash-links the
    lifecycle artifacts.
    """

    result = public_demo_bundle.generate_bundle(output_dir=output_dir)
    out_dir = Path(result['output_dir'])

    lifecycle_files = list(result['summary']['lifecycle_trace_files_v0_2'])
    for filename in lifecycle_files:
        artifact = _load_json(out_dir / filename)
        validate_artifact(artifact, str(artifact['schema_ref']))

    chain_result = verify_artifact_chain_manifest(_load_json(out_dir / 'artifact_chain_manifest.json'), root=out_dir)
    assert_security_profile_boundary()
    profile = security_profile_index()

    scenario_summary = {
        'demo': 'ravenclaw_demo_scenario',
        'status': 'passed' if chain_result.get('status') == 'passed' else 'failed',
        'workspace_root': str(ROOT),
        'output_dir': str(out_dir),
        'trace': DEMO_SCENARIO_TRACE,
        'ravenclaw': {
            'runtime_mode': result['summary']['runtime_mode'],
            'engine_status': result['summary']['engine_status'],
            'execution_adapter': result['summary']['integration_adapters']['execution']['mode'],
            'proof_trace_files': result['summary']['proof_trace_files'],
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
        },
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
        f"- govengine_surface: `{summary['govengine']['surface']}`",
        f"- sclite_chain_status: `{summary['sclite']['artifact_chain_status']}`",
        '',
        '## Trace',
        '',
        f"`{summary['trace']}`",
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
