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


class SchemaValidationError(AssertionError):
    pass


def _type_name(value: Any) -> str:
    if isinstance(value, bool):
        return 'boolean'
    if isinstance(value, dict):
        return 'object'
    if isinstance(value, list):
        return 'array'
    if isinstance(value, int) and not isinstance(value, bool):
        return 'integer'
    if isinstance(value, str):
        return 'string'
    if value is None:
        return 'null'
    return type(value).__name__


def _assert_type(value: Any, expected: Any, path: str) -> None:
    expected_types = expected if isinstance(expected, list) else [expected]
    actual = _type_name(value)
    if actual not in expected_types:
        raise SchemaValidationError(f'{path}: expected {expected_types}, got {actual}')


def _validate(schema: Dict[str, Any], value: Any, path: str = '$') -> None:
    if 'const' in schema and value != schema['const']:
        raise SchemaValidationError(f'{path}: expected const {schema["const"]!r}, got {value!r}')
    if 'enum' in schema and value not in schema['enum']:
        raise SchemaValidationError(f'{path}: expected one of {schema["enum"]!r}, got {value!r}')
    if 'type' in schema:
        _assert_type(value, schema['type'], path)
    if isinstance(value, str) and 'minLength' in schema and len(value) < int(schema['minLength']):
        raise SchemaValidationError(f'{path}: expected minLength {schema["minLength"]}')
    if isinstance(value, int) and 'minimum' in schema and value < int(schema['minimum']):
        raise SchemaValidationError(f'{path}: expected minimum {schema["minimum"]}')
    if schema.get('type') == 'object':
        assert isinstance(value, dict)
        for key in schema.get('required', []):
            if key not in value:
                raise SchemaValidationError(f'{path}: missing required field {key!r}')
        properties = schema.get('properties') if isinstance(schema.get('properties'), dict) else {}
        for key, subschema in properties.items():
            if key in value and isinstance(subschema, dict):
                _validate(subschema, value[key], f'{path}.{key}')
    if schema.get('type') == 'array':
        assert isinstance(value, list)
        item_schema = schema.get('items')
        if isinstance(item_schema, dict):
            for idx, item in enumerate(value):
                _validate(item_schema, item, f'{path}[{idx}]')


def _load_json(path: Path) -> Dict[str, Any]:
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise SchemaValidationError(f'{path}: JSON root is not an object')
    return value


def _load_schema(schema_ref: str) -> Dict[str, Any]:
    return _load_json(ROOT / schema_ref)


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
            _validate(_load_schema(schema_ref), artifacts[filename])
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
