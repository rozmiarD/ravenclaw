from __future__ import annotations

import json

from govengine import security_profile


def test_security_profile_index_is_json_safe() -> None:
    payload = security_profile.security_profile_index()

    assert payload['entrypoint'] == 'govengine.security_profile'
    assert payload['surface']['name'] == 'security_profile_helpers'
    assert payload['surface']['optional_profile'] is True
    assert [group['name'] for group in payload['groups']] == [
        'action_tooling',
        'policy_scope',
        'review_contracts',
    ]
    assert json.loads(json.dumps(payload)) == payload


def test_security_profile_modules_match_expected_optional_profile() -> None:
    modules = security_profile.security_profile_module_names()

    assert 'govengine.action_schema' in modules
    assert 'govengine.policy.gateway' in modules
    assert 'govengine.contracts.signal' in modules
    assert 'govengine.core' not in modules
    assert 'govengine.execution.gate' not in modules


def test_security_profile_lazy_import_is_allowlisted() -> None:
    module = security_profile.import_security_profile_module('govengine.action_schema')

    assert module.DEFAULT_ACTION_TYPE == 'single_probe'

    try:
        security_profile.import_security_profile_module('govengine.core')
    except KeyError as exc:
        assert exc.args == ('govengine.core',)
    else:  # pragma: no cover
        raise AssertionError('neutral core should not be imported through the security profile seam')


def test_security_profile_boundary_assertion() -> None:
    security_profile.assert_security_profile_boundary()
