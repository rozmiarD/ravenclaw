#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
ENGINE_DIR = ROOT / 'engine'
SCRIPTS_DIR = ROOT / 'scripts'
for path in (ENGINE_DIR, SCRIPTS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import list_public_validation_surfaces as surface_index  # type: ignore
import security_contract_layer as scl  # type: ignore

MANIFEST_ARTIFACT_TYPE = 'public_snapshot_manifest'
MANIFEST_SCHEMA_VERSION = 'v0.1'
MANIFEST_SCHEMA_REF = 'schemas/public_snapshot_manifest.v0.1.schema.json'


def _path_status(snapshot_root: Path, rel: str) -> dict[str, Any]:
    return {
        'path': rel,
        'present': (snapshot_root / rel).exists(),
    }


def _snapshot_label(snapshot_root: Path) -> str:
    try:
        return snapshot_root.resolve().relative_to(ROOT.resolve()).as_posix() or '.'
    except ValueError:
        return '<external-snapshot>'


def _file_artifact_type(path: str) -> str:
    if path.startswith('schemas/'):
        return 'json_schema'
    if path.startswith('scripts/'):
        return 'validation_script'
    if path.startswith('examples/'):
        return 'example_fixture'
    if path.startswith('references/'):
        return 'reference_doc'
    if path.startswith('tests/') or path.startswith('engine/tests'):
        return 'test_surface'
    return 'public_file'


def _file_schema(path: str) -> str:
    return path if path.startswith('schemas/') and path.endswith('.json') else ''


def _manifest_files(index: Mapping[str, Any], snapshot_root: Path) -> tuple[list[dict[str, Any]], int]:
    seen: set[str] = set()
    files: list[dict[str, Any]] = []
    missing_path_count = 0
    for surface in index['surfaces']:
        for rel in surface['paths']:
            if rel in seen:
                continue
            seen.add(rel)
            if not (snapshot_root / rel).exists():
                missing_path_count += 1
            files.append({
                'path': rel,
                'artifact_type': _file_artifact_type(rel),
                'schema': _file_schema(rel),
                'public_safe': True,
            })
    return files, missing_path_count


def build_manifest(snapshot_root: Path = ROOT) -> dict[str, Any]:
    index = surface_index.build_index(snapshot_root)
    files, missing_path_count = _manifest_files(index, snapshot_root)
    manifest = {
        'artifact_type': MANIFEST_ARTIFACT_TYPE,
        'schema_version': MANIFEST_SCHEMA_VERSION,
        'snapshot_name': _snapshot_label(snapshot_root),
        'snapshot_version': MANIFEST_SCHEMA_VERSION,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'files': files,
        'summary': {
            'file_count': len(files),
            'hashed_file_count': 0,
            'public_safe_file_count': sum(1 for file in files if file['public_safe']),
        },
        'public_safety': {
            'live_target_execution': False,
            'protocol_adapter_work': False,
            'raw_live_evidence_included': False,
            'raw_stdout_stderr_included': False,
        },
        'non_claims': [
            'Does not authorize publication by itself.',
            'Does not prove production deployment readiness.',
            'Does not include raw live evidence or raw stdout/stderr artifacts.',
        ],
    }
    validate_manifest_schema(manifest)
    manifest['_missing_path_count'] = missing_path_count
    return manifest


def validate_manifest_schema(manifest: Mapping[str, Any], root: Path = ROOT) -> None:
    scl.validate_schema_ref(MANIFEST_SCHEMA_REF, manifest, root=root, allow_external_schema_refs=True)


def _status_label(missing_paths: Sequence[str]) -> str:
    return 'PASS' if not missing_paths else 'MISSING_PATHS'


def print_markdown(manifest: Mapping[str, Any]) -> None:
    print('# Public Snapshot Manifest')
    print('')
    print('This manifest maps public validation surfaces to the files present in this public snapshot. It is local/public-safe and does not authorize live target execution, protocol adapter work, or publication by itself.')
    print('')
    print(f"snapshot_root: `{manifest['snapshot_name']}`")
    print(f"schema: `{MANIFEST_SCHEMA_REF}`")
    print(f"files: `{manifest['summary']['file_count']}`")
    print(f"missing_paths: `{manifest.get('_missing_path_count', 0)}`")
    print('')
    print('## Files')
    print('')
    for file in manifest['files']:
        print(f"- `{file['path']}` — public_safe={file['public_safe']}")
    print('')


def print_reviewer_report(manifest: Mapping[str, Any]) -> None:
    print('# Ravenclaw Public Snapshot Reviewer Report')
    print('')
    print('Use this generated report with `REVIEWER_VALIDATION_GUIDE.md`, `VALIDATION.md`, and `QUALITY_SIGNALS.md`.')
    print('')
    print('## Summary')
    print('')
    print(f"- snapshot root: `{manifest['snapshot_name']}`")
    print(f"- schema: `{MANIFEST_SCHEMA_REF}`")
    print(f"- files: `{manifest['summary']['file_count']}`")
    print(f"- missing paths: `{manifest.get('_missing_path_count', 0)}`")
    print('')
    if manifest.get('_missing_path_count', 0):
        print('Result: `REVIEW_REQUIRED` — at least one validation-surface path is missing from this snapshot.')
    else:
        print('Result: `PASS` — every validation-surface path referenced by the manifest is present in this snapshot.')
    print('')
    print('## Review table')
    print('')
    print('| File | Public safe | Kind |')
    print('| --- | --- | --- |')
    for file in manifest['files']:
        print(f"| `{file['path']}` | `{file['public_safe']}` | {file['artifact_type']} |")
    print('')
    print('## Boundaries')
    print('')
    print('- public-safe/local validation only')
    print('- no live target execution authorization')
    print('- no protocol adapter work authorization')
    print('- no publication approval by itself')


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Build a public-safe manifest mapping validation surfaces to snapshot files.')
    parser.add_argument('snapshot_root', nargs='?', default='.', help='assembled public snapshot root to inspect')
    parser.add_argument('--format', choices=['json', 'markdown', 'reviewer-report'], default='json')
    parser.add_argument('--check', action='store_true', help='fail if any validation surface path is missing from the snapshot')
    args = parser.parse_args(argv)

    manifest = build_manifest(Path(args.snapshot_root).resolve())
    if args.format == 'markdown':
        print_markdown(manifest)
    elif args.format == 'reviewer-report':
        print_reviewer_report(manifest)
    else:
        public_manifest = {k: v for k, v in manifest.items() if not k.startswith('_')}
        print(json.dumps(public_manifest, indent=2, sort_keys=True))
    if args.check and manifest.get('_missing_path_count', 0):
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
