#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
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


def build_manifest(snapshot_root: Path = ROOT) -> dict[str, Any]:
    index = surface_index.build_index(snapshot_root)
    surfaces: list[dict[str, Any]] = []
    path_count = 0
    missing_path_count = 0
    for surface in index['surfaces']:
        path_entries = [_path_status(snapshot_root, rel) for rel in surface['paths']]
        missing_paths = [entry['path'] for entry in path_entries if not entry['present']]
        path_count += len(path_entries)
        missing_path_count += len(missing_paths)
        surfaces.append({
            'id': surface['id'],
            'title': surface['title'],
            'claim': surface['claim'],
            'non_claim': surface['non_claim'],
            'boundaries': dict(surface['boundaries']),
            'paths': path_entries,
            'missing_paths': missing_paths,
        })
    manifest = {
        'artifact_type': MANIFEST_ARTIFACT_TYPE,
        'schema_version': MANIFEST_SCHEMA_VERSION,
        'schema_ref': MANIFEST_SCHEMA_REF,
        'snapshot_root_label': _snapshot_label(snapshot_root),
        'generated_by': 'scripts/build_public_snapshot_manifest.py',
        'summary': {
            'surface_count': len(surfaces),
            'path_count': path_count,
            'missing_path_count': missing_path_count,
        },
        'surfaces': surfaces,
    }
    validate_manifest_schema(manifest)
    return manifest


def validate_manifest_schema(manifest: Mapping[str, Any], root: Path = ROOT) -> None:
    scl.validate_schema_ref(MANIFEST_SCHEMA_REF, manifest, root=root)


def _status_label(missing_paths: Sequence[str]) -> str:
    return 'PASS' if not missing_paths else 'MISSING_PATHS'


def print_markdown(manifest: Mapping[str, Any]) -> None:
    print('# Public Snapshot Manifest')
    print('')
    print('This manifest maps public validation surfaces to the files present in this public snapshot. It is local/public-safe and does not authorize live target execution, protocol adapter work, or publication by itself.')
    print('')
    print(f"snapshot_root: `{manifest['snapshot_root_label']}`")
    print(f"schema_ref: `{manifest['schema_ref']}`")
    print(f"surface_count: `{manifest['summary']['surface_count']}`")
    print(f"path_count: `{manifest['summary']['path_count']}`")
    print(f"missing_paths: `{manifest['summary']['missing_path_count']}`")
    print('')
    for surface in manifest['surfaces']:
        print(f"## {surface['title']}")
        print('')
        print(f"- id: `{surface['id']}`")
        print(f"- status: `{_status_label(surface['missing_paths'])}`")
        print(f"- validates: {surface['claim']}")
        print(f"- does not claim: {surface['non_claim']}")
        print('- paths:')
        for path in surface['paths']:
            marker = 'present' if path['present'] else 'missing'
            print(f"  - `{path['path']}` — {marker}")
        if surface['missing_paths']:
            print(f"- missing paths: {', '.join(surface['missing_paths'])}")
        else:
            print('- missing paths: none')
        print('')


def print_reviewer_report(manifest: Mapping[str, Any]) -> None:
    print('# Ravenclaw Public Snapshot Reviewer Report')
    print('')
    print('Use this generated report with `REVIEWER_VALIDATION_GUIDE.md`, `VALIDATION.md`, and `QUALITY_SIGNALS.md`.')
    print('')
    print('## Summary')
    print('')
    print(f"- snapshot root: `{manifest['snapshot_root_label']}`")
    print(f"- schema: `{manifest['schema_ref']}`")
    print(f"- surfaces: `{manifest['summary']['surface_count']}`")
    print(f"- referenced paths: `{manifest['summary']['path_count']}`")
    print(f"- missing paths: `{manifest['summary']['missing_path_count']}`")
    print('')
    if manifest['summary']['missing_path_count']:
        print('Result: `REVIEW_REQUIRED` — at least one validation-surface path is missing from this snapshot.')
    else:
        print('Result: `PASS` — every validation-surface path referenced by the manifest is present in this snapshot.')
    print('')
    print('## Review table')
    print('')
    print('| Surface | Status | Evidence paths | Non-claim |')
    print('| --- | --- | --- | --- |')
    for surface in manifest['surfaces']:
        status = _status_label(surface['missing_paths'])
        paths = '<br>'.join(f"`{path['path']}`" for path in surface['paths'])
        print(f"| {surface['title']} | `{status}` | {paths} | {surface['non_claim']} |")
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
        print(json.dumps(manifest, indent=2, sort_keys=True))
    if args.check and manifest['summary']['missing_path_count']:
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
