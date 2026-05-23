from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import demo_entry  # type: ignore
from security_contract_layer import (  # type: ignore
    CURRENT_LIFECYCLE_TRACE_FILES,
    build_current_lifecycle_artifacts,
    repo_root,
    sanitize_public_artifact,
)
from sclite.bundles import REVIEW_BUNDLE_REQUIRED_FILES, materialize_review_bundle  # type: ignore
from sclite.integrity import verify_artifact_chain_manifest  # type: ignore


BUNDLE_VERSION = '2026-04-24.public-demo-bundle.v1'
DEFAULT_OUTPUT_DIR = 'demo-output'


def _parse_first_json_document(text: str) -> Dict[str, Any]:
    payload = str(text or '').lstrip()
    decoder = json.JSONDecoder()
    obj, _idx = decoder.raw_decode(payload)
    if not isinstance(obj, dict):
        raise ValueError('json_root_not_object')
    return obj


def _run_json_command(command: List[str], *, cwd: Path, env: Dict[str, str]) -> Dict[str, Any]:
    proc = subprocess.run(command, cwd=str(cwd), env=env, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f'command_failed:{proc.returncode}:{proc.stderr.strip()[:240]}')
    try:
        return _parse_first_json_document(proc.stdout)
    except Exception as exc:  # pragma: no cover - defensive parse context
        raise RuntimeError(f'command_stdout_not_json:{exc}') from exc


def build_bundle_summary(*, plan_data: Dict[str, Any], pipeline_data: Dict[str, Any], commands: List[List[str]]) -> Dict[str, Any]:
    delivery_profile = dict(pipeline_data.get('delivery_profile') or {}) if isinstance(pipeline_data.get('delivery_profile'), dict) else {}
    adapters = dict(pipeline_data.get('integration_adapters') or {}) if isinstance(pipeline_data.get('integration_adapters'), dict) else {}
    engine = dict(pipeline_data.get('engine') or {}) if isinstance(pipeline_data.get('engine'), dict) else {}
    plan_summary = {
        'scope_targets': int(plan_data.get('scope_targets', 0) or 0) if isinstance(plan_data, dict) else 0,
        'valid_targets': int(plan_data.get('valid_targets', 0) or 0) if isinstance(plan_data, dict) else 0,
    }
    return {
        'bundle_version': BUNDLE_VERSION,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'runtime_mode': str((pipeline_data.get('settings') or {}).get('runtime_mode') or delivery_profile.get('runtime_mode') or 'unknown'),
        'engine_status': str(engine.get('status') or 'unknown'),
        'final_status': str(pipeline_data.get('final_status') or 'unknown'),
        'delivery_profile': delivery_profile,
        'integration_adapters': adapters,
        'plan_summary': plan_summary,
        'planned_command': sanitize_public_artifact(list(pipeline_data.get('planned_command') or [])),
        'lifecycle_trace_files': list(CURRENT_LIFECYCLE_TRACE_FILES),
        'review_bundle_dir': 'review_bundle',
        'demo_commands': sanitize_public_artifact([list(cmd) for cmd in commands]),
    }


def build_bundle_markdown(summary: Dict[str, Any]) -> str:
    adapters = dict(summary.get('integration_adapters') or {}) if isinstance(summary.get('integration_adapters'), dict) else {}
    lines = [
        '# Ravenclaw Public Demo Bundle',
        '',
        f"- bundle_version: `{summary.get('bundle_version', '')}`",
        f"- runtime_mode: `{summary.get('runtime_mode', '')}`",
        f"- final_status: `{summary.get('final_status', '')}`",
        f"- engine_status: `{summary.get('engine_status', '')}`",
        f"- brain_adapter: `{((adapters.get('brain') or {}) if isinstance(adapters.get('brain'), dict) else {}).get('mode', '')}`",
        f"- auditor_adapter: `{((adapters.get('auditor') or {}) if isinstance(adapters.get('auditor'), dict) else {}).get('mode', '')}`",
        f"- execution_adapter: `{((adapters.get('execution') or {}) if isinstance(adapters.get('execution'), dict) else {}).get('mode', '')}`",
        '',
        '## Generated files',
        '',
        '- `plan_campaign.demo.json`',
        '- `run_pipeline.demo.json`',
        '- `intent_contract.json`',
        '- `policy_decision.v0.2.json`',
        '- `execution_contract.json`',
        '- `execution_ticket.json`',
        '- `execution_receipt.v0.2.json`',
        '- `evidence_contract.json`',
        '- `artifact_chain_manifest.json`',
        '- `review_bundle/verification_receipt.json`',
        '- `review_bundle/REVIEW.md`',
        '- `bundle_summary.json`',
        '- `bundle_summary.md`',
        '',
        '## SCLite current lifecycle and review bundle',
        '',
        '`intent -> policy decision -> execution contract -> scoped execution ticket -> execution receipt -> evidence contract -> artifact chain manifest -> review bundle`',
    ]
    return '\n'.join(lines) + '\n'


def generate_bundle(*, output_dir: str = DEFAULT_OUTPUT_DIR, python_bin: str | None = None) -> Dict[str, Any]:
    root = repo_root()
    out_dir = (root / output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    commands = demo_entry.build_demo_commands(python_bin=python_bin or sys.executable)
    env = dict(os.environ)
    env.setdefault('RAVENCLAW_MODE', 'demo')

    plan_data = _run_json_command(commands[0], cwd=root, env=env)
    pipeline_data = _run_json_command(commands[1], cwd=root, env=env)
    summary = build_bundle_summary(plan_data=plan_data, pipeline_data=pipeline_data, commands=commands)
    lifecycle_trace = build_current_lifecycle_artifacts(pipeline_data)
    markdown = build_bundle_markdown(summary)

    (out_dir / 'plan_campaign.demo.json').write_text(json.dumps(sanitize_public_artifact(plan_data), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (out_dir / 'run_pipeline.demo.json').write_text(json.dumps(sanitize_public_artifact(pipeline_data), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for filename, artifact in lifecycle_trace.items():
        (out_dir / filename).write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    verify_artifact_chain_manifest(lifecycle_trace['artifact_chain_manifest.json'], root=out_dir)
    review_record = materialize_review_bundle(
        out_dir / 'review_bundle',
        {
            'intent_contract': lifecycle_trace['intent_contract.json'],
            'policy_decision': lifecycle_trace['policy_decision.v0.2.json'],
            'execution_contract': lifecycle_trace['execution_contract.json'],
            'execution_ticket': lifecycle_trace['execution_ticket.json'],
            'execution_receipt': lifecycle_trace['execution_receipt.v0.2.json'],
            'evidence_contract': lifecycle_trace['evidence_contract.json'],
        },
        chain_id=str(pipeline_data.get('run_id') or 'ravenclaw-current-review-bundle'),
        generated_at=str(summary['generated_at']),
    )
    if review_record.get('verdict') != 'pass':
        raise RuntimeError(f"current_review_bundle_not_passed:{review_record.get('verdict')}")
    (out_dir / 'bundle_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (out_dir / 'bundle_summary.md').write_text(markdown, encoding='utf-8')
    files = [
        str(out_dir / 'plan_campaign.demo.json'),
        str(out_dir / 'run_pipeline.demo.json'),
        *[str(out_dir / name) for name in CURRENT_LIFECYCLE_TRACE_FILES],
        *[str(out_dir / 'review_bundle' / name) for name in (*REVIEW_BUNDLE_REQUIRED_FILES.values(), 'artifact_chain_manifest.json', 'verification_receipt.json', 'REVIEW.md')],
        str(out_dir / 'bundle_summary.json'),
        str(out_dir / 'bundle_summary.md'),
    ]
    return {
        'output_dir': str(out_dir),
        'summary': summary,
        'files': files,
    }


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description='Generate a reusable public demo bundle for Ravenclaw.')
    ap.add_argument('--output-dir', default=DEFAULT_OUTPUT_DIR)
    ap.add_argument('--print-summary', action='store_true', help='print only the compact summary JSON after generation')
    args = ap.parse_args(argv)

    result = generate_bundle(output_dir=str(args.output_dir))
    if args.print_summary:
        print(json.dumps(result['summary'], ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
