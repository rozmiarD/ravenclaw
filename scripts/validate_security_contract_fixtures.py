#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
ENGINE_DIR = ROOT / 'engine'
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

import security_contract_layer as scl  # type: ignore


def _load_json(path: Path) -> Dict[str, Any]:
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise scl.JsonSchemaValidationError(f'{path}: JSON root is not an object')
    return value


def load_fixture_artifacts(fixture_dir: Path) -> Dict[str, Any]:
    artifacts: Dict[str, Any] = {}
    for filename in scl.PROOF_TRACE_FILES:
        path = fixture_dir / filename
        if not path.exists():
            raise FileNotFoundError(f'missing fixture artifact: {path}')
        if filename.endswith('.md'):
            artifacts[filename] = path.read_text(encoding='utf-8')
        else:
            artifacts[filename] = _load_json(path)
    return artifacts


def validate_fixture_dir(fixture_dir: Path) -> List[str]:
    errors: List[str] = []
    try:
        artifacts = load_fixture_artifacts(fixture_dir)
    except Exception as exc:
        return [f'load_failed:{exc}']

    errors.extend(scl.validate_public_proof_trace_artifacts(artifacts))

    manifest = scl.proof_trace_manifest()
    for filename in scl.PROOF_TRACE_FILES:
        metadata = manifest.get(filename) or {}
        schema_ref = str(metadata.get('schema') or '')
        if not schema_ref:
            continue
        try:
            scl.validate_schema_ref(schema_ref, artifacts[filename], root=ROOT)
        except Exception as exc:
            errors.append(f'{filename}:schema_validation:{exc}')

    serialized = '\n'.join(
        value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, sort_keys=True)
        for value in artifacts.values()
    )
    forbidden = [str(ROOT), str(Path.home()), 'private-researcher-handle', 'session=abc', 'private.txt']
    for needle in forbidden:
        if needle and needle in serialized:
            errors.append(f'forbidden_value_present:{needle}')
    return errors


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Validate public Security Contract Layer fixtures.')
    parser.add_argument('fixture_dir', nargs='?', default='examples/security-contract-proof')
    args = parser.parse_args(argv)
    fixture_dir = (ROOT / str(args.fixture_dir)).resolve()
    errors = validate_fixture_dir(fixture_dir)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f'security_contract_fixtures_ok:{fixture_dir}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
