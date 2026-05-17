from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any, Dict

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
ROOT = Path(__file__).resolve().parents[2]
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from govengine.contracts.execution import build_approved_execution_spec, build_prepared_execution_spec

SCHEMA_PATH = ROOT / 'schemas' / 'approved_execution_spec.v0.1.schema.json'


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
    if 'type' in schema:
        _assert_type(value, schema['type'], path)
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


def _load_schema() -> Dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding='utf-8'))


def _valid_approved_spec() -> Dict[str, Any]:
    raw_action = {
        'action_type': 'single_probe',
        'capability': 'http_probe',
        'task_family': 'demo',
        'tool': 'curl',
        'args': ['-I', 'https://example.com/'],
    }
    prepared_action = {
        'action_type': 'single_probe',
        'capability': 'http_probe',
        'task_family': 'demo',
        'tool': 'curl',
        'args': ['-I', 'https://example.com/'],
        'tool_chain': [{'tool': 'curl', 'role': 'probe', 'args': ['-I', 'https://example.com/']}],
        'resolved_planner_profiles': ['demo'],
        'tool_candidates': ['curl'],
    }
    compiled = {
        'action_type': 'single_probe',
        'capability': 'http_probe',
        'compiler_strategy': 'passthrough',
        'compiler_tool_choice': 'curl',
        'compiler_tool_choice_source': 'explicit_tool',
        'compiler_variant_count': 1,
        'recipe_name': '',
        'semantic_loss_detected': False,
        'normalization_reason': '',
        'semantic_loss_policy': {'loss_class': 'none', 'policy_response': 'proceed', 'approved_under_degradation': False},
        'execution_mode': 'normalized',
        'tool_candidates': ['curl'],
    }
    creds = {
        'credentials_required': False,
        'allow_auth_header': False,
        'allow_cookie_header': False,
        'allow_basic_auth': False,
        'credentials_owner_approved': False,
        'request_decoration': {'mode': 'none', 'headers': [], 'cookies': [], 'basic_auth': {'enabled': False, 'username': '', 'password_ref': ''}, 'provenance_notes': []},
        'resolved_campaign_key': '',
    }
    prepared = build_prepared_execution_spec(
        raw_action_spec=raw_action,
        prepared_action_spec=prepared_action,
        compiled_action=compiled,
        creds_policy=creds,
        target='https://example.com/',
        target_in_scope=True,
    )
    return build_approved_execution_spec(
        prepared,
        auditor={'decision': 'approve', 'reason': 'ok', 'reason_code': 'approve_in_scope', 'constraints': {'aggression': 3}},
        approval_source='auditor',
        approval_transform_chain=[],
        owner_override_applied=False,
    )


def test_current_generated_approved_execution_spec_matches_schema() -> None:
    _validate(_load_schema(), _valid_approved_spec())


def test_schema_rejects_missing_critical_field() -> None:
    spec = _valid_approved_spec()
    spec.pop('approval')
    try:
        _validate(_load_schema(), spec)
    except SchemaValidationError as exc:
        assert 'approval' in str(exc)
    else:  # pragma: no cover - assertion guard
        raise AssertionError('missing approval should fail schema validation')


def test_schema_rejects_wrong_spec_version() -> None:
    spec = _valid_approved_spec()
    spec['spec_version'] = 'wrong'
    try:
        _validate(_load_schema(), spec)
    except SchemaValidationError as exc:
        assert '2026-03-18.approved.v1' in str(exc)
    else:  # pragma: no cover - assertion guard
        raise AssertionError('wrong spec_version should fail schema validation')


def test_executor_critical_fields_are_required_by_schema() -> None:
    schema = _load_schema()
    for field in ('resolved_tool', 'normalized_args', 'execution_plan', 'approval', 'execution_truth'):
        assert field in schema['required']
    assert 'resolved_tool' in schema['properties']
    assert 'execution_plan' in schema['properties']
    assert 'command_input_summary' in schema['properties']['execution_truth']['required']


def test_schema_does_not_require_raw_secret_fields() -> None:
    spec = copy.deepcopy(_valid_approved_spec())
    spec['request_decoration'] = {
        'headers': [{'name': 'X-Test', 'value': '<redacted>', 'raw': 'X-Test: <redacted>'}],
        'cookies': [{'name': 'session', 'value': '<redacted>'}],
        'basic_auth': {'enabled': True, 'username': 'user', 'password_ref': '<redacted>'},
    }
    _validate(_load_schema(), spec)
    serialized_schema = json.dumps(_load_schema())
    assert 'password"' not in serialized_schema
    assert 'token"' not in serialized_schema
