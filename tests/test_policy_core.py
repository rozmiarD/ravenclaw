from engine.policy_core import contains_banned_patterns, check_credentials_policy, parse_auth_usage


def test_contains_banned_patterns_detects_pattern():
    blocked, pattern = contains_banned_patterns(["-X", "GET", "--flood"])
    assert blocked is True
    assert pattern == "--flood"


def test_check_credentials_policy_blocks_auth_without_owner_approval():
    creds = {
        "allow_auth_header": True,
        "allow_cookie_header": False,
        "allow_basic_auth": False,
        "credentials_owner_approved": False,
        "credentials_required": False,
    }
    ok, reason = check_credentials_policy(
        ["-H", "Authorization: Bearer abc"],
        creds,
        owner_approved_auth=False,
        tool="curl",
    )
    assert ok is False
    assert reason == "credentials_require_owner_approval"


def test_parse_auth_usage_does_not_treat_httpx_url_flag_as_basic_auth():
    usage = parse_auth_usage(['-u', 'https://example.com/', '-tls-probe'], tool='httpx-pd')
    assert usage['uses_basic'] is False
    assert usage['uses_auth'] is False


def test_check_credentials_policy_allows_httpx_url_flag_without_basic_auth():
    creds = {
        "allow_auth_header": False,
        "allow_cookie_header": False,
        "allow_basic_auth": False,
        "credentials_owner_approved": False,
        "credentials_required": True,
        "bug_bounty_username": "hunter1",
        "test_account_email": "hunter1@example.com",
    }
    ok, reason = check_credentials_policy(
        ['-u', 'https://example.com/', '-tls-probe'],
        creds,
        owner_approved_auth=False,
        tool='httpx-pd',
    )
    assert ok is True
    assert reason == 'ok'
