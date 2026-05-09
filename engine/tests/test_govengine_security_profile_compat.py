from __future__ import annotations

import json
import sys
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parents[1]
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

import govengine_security_profile as compat


def test_security_profile_compat_index_is_json_safe() -> None:
    payload = compat.security_profile_index()

    assert payload['surface']['name'] == 'security_profile_helpers'
    assert payload['surface']['optional_profile'] is True
    assert [group['name'] for group in payload['groups']] == [
        'action_tooling',
        'policy_scope',
        'review_contracts',
    ]
    assert json.loads(json.dumps(payload)) == payload


def test_security_profile_compat_modules_match_expected_optional_profile() -> None:
    modules = compat.security_profile_module_names()

    assert 'govengine.action_schema' in modules
    assert 'govengine.policy.gateway' in modules
    assert 'govengine.contracts.signal' in modules
    assert 'govengine.core' not in modules
    assert 'govengine.execution.gate' not in modules


def test_security_profile_compat_lazy_import_is_allowlisted() -> None:
    module = compat.import_security_profile_module('govengine.action_schema')

    assert module.DEFAULT_ACTION_TYPE == 'single_probe'

    try:
        compat.import_security_profile_module('govengine.core')
    except KeyError as exc:
        assert exc.args == ('govengine.core',)
    else:  # pragma: no cover
        raise AssertionError('neutral core should not be imported through the security profile seam')


def test_security_profile_compat_boundary_assertion() -> None:
    compat.assert_security_profile_boundary()
