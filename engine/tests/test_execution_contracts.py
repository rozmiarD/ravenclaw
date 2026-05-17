from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from govengine.contracts.execution import (
    apply_request_decoration_to_args,
    build_execution_input_summaries_from_execution_spec,
    build_execution_input_summary_from_execution_spec,
    build_approved_execution_spec,
    build_prepared_execution_spec,
    redact_prepared_execution_spec_for_auditor,
    summarize_request_decoration,
    summarize_request_shape_hygiene,
)


def test_summarize_request_decoration_classifies_campaign_headers_and_cookies() -> None:
    action_spec = {
        'tool': 'curl',
        'args': [
            '-H', 'X-Bug-Bounty: hunter1',
            '-H', 'X-Test-Account-Email: hunter1@example.com',
            '-H', 'X-Canary: rc',
            '-b', 'session=abc123; csrftoken=def456',
        ],
    }
    creds = {
        'bug_bounty_username': 'hunter1',
        'test_account_email': 'hunter1@example.com',
        'allow_cookie_header': True,
        'credentials_required': True,
        'credentials_owner_approved': False,
        'request_decoration': {'mode': 'none', 'headers': [], 'cookies': [], 'basic_auth': {'enabled': False, 'username': '', 'password': '', 'password_ref': ''}, 'provenance_notes': []},
    }
    out = summarize_request_decoration(action_spec, creds)
    assert out['mode'] == 'mixed'
    assert any(h['source'] == 'campaign_required' for h in out['headers'])
    assert any(h['name'] == 'X-Canary' and h['source'] == 'operator_supplied' for h in out['headers'])
    assert out['cookies'][0]['name'] == 'session'
    assert out['cookies'][0]['value'] == '<redacted>'
    assert out['owner_approval_required'] is True


def test_apply_request_decoration_to_args_adds_campaign_and_operator_context() -> None:
    creds = {
        'bug_bounty_username': 'hunter1',
        'test_account_email': 'hunter1@example.com',
        'request_decoration': {
            'mode': 'operator_supplied',
            'headers': [{'name': 'X-Canary', 'value': 'rc'}],
            'cookies': [{'name': 'session', 'value': 'abc'}],
            'basic_auth': {'enabled': True, 'username': 'user', 'password': 'pass', 'password_ref': ''},
            'provenance_notes': ['manual'],
        },
    }
    out = apply_request_decoration_to_args('curl', ['-I', 'https://api.example.com/'], creds)
    joined = ' '.join(out)
    assert 'X-Bug-Bounty: hunter1' in joined
    assert 'X-Test-Account-Email: hunter1@example.com' in joined
    assert 'X-Canary: rc' in joined
    assert 'session=abc' in joined
    assert '-u user:pass' in joined


def test_apply_request_decoration_to_args_adds_campaign_headers_for_runtime_toolchain() -> None:
    creds = {
        'bug_bounty_username': 'hunter1',
        'test_account_email': 'hunter1@example.com',
        'request_decoration': {
            'mode': 'campaign_required',
            'headers': [],
            'cookies': [],
            'basic_auth': {'enabled': False, 'username': '', 'password': '', 'password_ref': ''},
            'provenance_notes': ['campaign'],
        },
    }
    httpx_args = apply_request_decoration_to_args('httpx', ['https://api.example.com/'], creds)
    assert '--headers' in httpx_args
    assert 'X-Bug-Bounty' in httpx_args
    assert 'hunter1' in httpx_args
    assert 'X-Test-Account-Email' in httpx_args
    assert 'hunter1@example.com' in httpx_args

    for tool in ('httpx-pd', 'katana', 'feroxbuster', 'gobuster'):
        out = apply_request_decoration_to_args(tool, ['https://api.example.com/'], creds)
        joined = ' '.join(out)
        assert 'X-Bug-Bounty: hunter1' in joined
        assert 'X-Test-Account-Email: hunter1@example.com' in joined


def test_redact_prepared_execution_spec_for_auditor_masks_cookie_and_basic_auth() -> None:
    prepared = {
        'normalized_args': ['-b', 'session=abc', '-u', 'user:pass', '-H', 'X-Canary: rc'],
        'stdin': 'https://example.com/secret?token=abc\n',
        'execution_plan': [{'tool': 'curl', 'args': ['-b', 'session=abc', '-u', 'user:pass', '-H', 'X-Canary: rc'], 'stdin': 'https://example.com/secret?token=abc\n'}],
        'request_decoration': {
            'cookies': [{'name': 'session', 'value': 'abc', 'source': 'operator_supplied'}],
            'basic_auth': {'enabled': True, 'username': 'user', 'password_ref': ''},
        },
    }
    redacted = redact_prepared_execution_spec_for_auditor(prepared)
    assert '<cookie_redacted>' in redacted['normalized_args']
    assert 'user:<redacted>' in redacted['normalized_args']
    assert 'stdin' not in redacted
    assert redacted['stdin_present'] is True
    assert redacted['stdin_line_count'] == 1
    assert 'token=abc' in redacted['stdin_preview']
    assert 'stdin' not in redacted['execution_plan'][0]
    assert redacted['execution_plan'][0]['stdin_present'] is True
    assert redacted['request_decoration']['cookies'][0]['value'] == '<redacted>'
    assert redacted['request_decoration']['basic_auth']['password_ref'] == '<redacted>'


def test_summarize_request_shape_hygiene_classifies_exact_and_mixed_hosts() -> None:
    clean = summarize_request_shape_hygiene(
        target='https://api.example.com/',
        normalized_args=['-I', 'https://api.example.com/', '-H', 'Host: api.example.com'],
        execution_plan=[{'tool': 'curl', 'args': ['-I', 'https://api.example.com/']}],
    )
    assert clean['arg_hosts_detected'] == ['api.example.com']
    assert clean['execution_plan_hosts_detected'] == ['api.example.com']
    assert clean['target_host_match_status'] == 'exact'
    assert clean['request_shape_hygiene_status'] == 'clean'
    assert clean['mismatched_hosts_detected'] == []

    mixed = summarize_request_shape_hygiene(
        target='https://www.bitstamp.net/',
        normalized_args=['curl', 'https://insight2.tradepmr.com/'],
        execution_plan=[{'tool': 'curl', 'args': ['https://insight2.tradepmr.com/']}],
    )
    assert mixed['arg_hosts_detected'] == ['insight2.tradepmr.com']
    assert mixed['execution_plan_hosts_detected'] == ['insight2.tradepmr.com']
    assert mixed['target_host_match_status'] == 'mixed'
    assert mixed['request_shape_hygiene_status'] == 'cross_host_mismatch'
    assert mixed['mismatched_hosts_detected'] == ['insight2.tradepmr.com']
    assert mixed['request_shape_hygiene_source'] == 'normalized_args+execution_plan'


def test_summarize_request_shape_hygiene_detects_execution_plan_only_mismatch() -> None:
    out = summarize_request_shape_hygiene(
        target='https://www.bitstamp.net/',
        normalized_args=['curl', '--max-time', '5'],
        execution_plan=[{'tool': 'curl', 'args': ['https://insight2.tradepmr.com/health']}],
    )
    assert out['arg_hosts_detected'] == []
    assert out['execution_plan_hosts_detected'] == ['insight2.tradepmr.com']
    assert out['mismatched_hosts_detected'] == ['insight2.tradepmr.com']
    assert out['target_host_match_status'] == 'mixed'
    assert out['request_shape_hygiene_status'] == 'cross_host_mismatch'
    assert out['request_shape_hygiene_source'] == 'execution_plan'


def test_summarize_request_shape_hygiene_does_not_false_positive_on_non_host_args() -> None:
    out = summarize_request_shape_hygiene(
        target='https://api.example.com/',
        normalized_args=['--max-time', '5', '--retry', '2', '/tmp/report.txt', 'user@example'],
        execution_plan=[{'tool': 'curl', 'args': ['--max-time', '5', '--retry', '2']}],
    )
    assert out['arg_hosts_detected'] == []
    assert out['execution_plan_hosts_detected'] == []
    assert out['mismatched_hosts_detected'] == []
    assert out['target_host_match_status'] == 'none_detected'
    assert out['request_shape_hygiene_status'] == 'ambiguous'
    assert out['request_shape_hygiene_source'] == 'none'


def test_summarize_request_shape_hygiene_keeps_same_host_variants_clean() -> None:
    out = summarize_request_shape_hygiene(
        target='https://api.example.com/',
        normalized_args=['-H', 'Host: api.example.com', 'https://api.example.com/login?next=%2Fdashboard'],
        execution_plan=[
            {'tool': 'curl', 'args': ['https://api.example.com/login']},
            {'tool': 'curl', 'args': ['-H', 'Origin: https://api.example.com', 'https://api.example.com/api/session']},
        ],
    )
    assert out['arg_hosts_detected'] == ['api.example.com']
    assert out['execution_plan_hosts_detected'] == ['api.example.com']
    assert out['mismatched_hosts_detected'] == []
    assert out['target_host_match_status'] == 'exact'
    assert out['request_shape_hygiene_status'] == 'clean'


def test_summarize_request_shape_hygiene_detects_stdin_target_hosts() -> None:
    out = summarize_request_shape_hygiene(
        target='https://api.example.com/',
        normalized_args=['-d', '2', '-u'],
        execution_plan=[{'tool': 'hakrawler', 'args': ['-d', '2', '-u'], 'stdin': 'https://api.example.com/app\n'}],
    )
    assert out['arg_hosts_detected'] == []
    assert out['execution_plan_hosts_detected'] == ['api.example.com']
    assert out['mismatched_hosts_detected'] == []
    assert out['target_host_match_status'] == 'exact'
    assert out['request_shape_hygiene_status'] == 'clean'


def test_build_execution_input_summary_detects_stdin_delivery_mode() -> None:
    summary = build_execution_input_summary_from_execution_spec({
        'resolved_tool': 'hakrawler',
        'execution_plan': [{'tool': 'hakrawler', 'role': 'probe', 'args': ['-d', '2', '-u'], 'stdin': 'https://example.com/app\n'}],
    })
    assert summary['preview_source'] == 'execution_plan_first_step'
    assert summary['target_delivery_mode'] == 'stdin'
    assert summary['tool'] == 'hakrawler'
    assert summary['stdin_present'] is True
    assert summary['stdin_line_count'] == 1


def test_build_execution_input_summaries_marks_mixed_delivery_modes() -> None:
    summaries = build_execution_input_summaries_from_execution_spec({
        'execution_plan': [
            {'tool': 'hakrawler', 'role': 'probe', 'args': ['-d', '2', '-u'], 'stdin': 'https://example.com/app\n'},
            {'tool': 'curl', 'role': 'validate', 'args': ['https://example.com/robots.txt']},
        ],
    })
    assert summaries[0]['target_delivery_mode'] == 'stdin'
    assert summaries[1]['target_delivery_mode'] == 'argv'


def test_build_prepared_and_approved_execution_spec_capture_core_contract() -> None:
    raw_action = {
        'action_type': 'single_probe',
        'capability': 'http_probe',
        'task_family': 'authz',
        'tool': 'curl',
        'args': ['-I', 'https://api.example.com/'],
        'resolved_planner_profiles': ['core'],
    }
    prepared_action = {
        'action_type': 'single_probe',
        'capability': 'http_probe',
        'task_family': 'authz',
        'tool': 'curl',
        'args': ['-I', 'https://api.example.com/'],
        'tool_chain': [{'tool': 'curl', 'args': ['-I', 'https://api.example.com/'], 'role': 'probe'}],
        'resolved_planner_profiles': ['core'],
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
        'request_decoration': {'mode': 'none', 'headers': [], 'cookies': [], 'basic_auth': {'enabled': False, 'username': '', 'password': '', 'password_ref': ''}, 'provenance_notes': []},
        'resolved_campaign_key': 'camp1',
    }
    prepared = build_prepared_execution_spec(
        raw_action_spec=raw_action,
        prepared_action_spec=prepared_action,
        compiled_action=compiled,
        creds_policy=creds,
        target='https://api.example.com/',
        target_in_scope=True,
    )
    assert prepared['resolved_tool'] == 'curl'
    assert prepared['target_in_scope'] is True
    assert prepared['stdin'] == ''
    assert prepared['credentials_policy_snapshot']['resolved_campaign_key'] == 'camp1'
    assert prepared['compiler']['semantic_loss_detected'] is False
    assert prepared['compiler']['semantic_loss_policy']['loss_class'] == 'none'
    assert prepared['arg_hosts_detected'] == ['api.example.com']
    assert prepared['execution_plan_hosts_detected'] == ['api.example.com']
    assert prepared['target_host_match_status'] == 'exact'
    assert prepared['request_shape_hygiene_status'] == 'clean'
    approved = build_approved_execution_spec(
        prepared,
        auditor={'decision': 'approve', 'reason': 'ok', 'reason_code': 'approve_in_scope', 'constraints': {'aggression': 3}},
        approval_source='auditor',
        approval_transform_chain=[],
        owner_override_applied=False,
    )
    assert approved['approval']['decision'] == 'approve'
    assert approved['approval']['reason_code'] == 'approve_in_scope'
    assert approved['approval']['approval_source'] == 'auditor'
    assert approved['resolved_tool'] == 'curl'
    assert approved['execution_truth']['command_input_summary']['target_delivery_mode'] == 'argv'
    assert approved['execution_truth']['execution_input_summaries'][0]['target_delivery_mode'] == 'argv'
    assert approved['execution_truth']['target_host_match_status'] == 'exact'
    assert approved['execution_truth']['request_shape_hygiene_status'] == 'clean'


def test_build_approved_execution_spec_carries_stdin_input_summary() -> None:
    prepared = {
        'resolved_tool': 'hakrawler',
        'normalized_args': ['-d', '2', '-u'],
        'execution_plan': [{'tool': 'hakrawler', 'role': 'probe', 'args': ['-d', '2', '-u'], 'stdin': 'https://example.com/app\n'}],
        'arg_hosts_detected': [],
        'execution_plan_hosts_detected': ['example.com'],
        'all_hosts_detected': ['example.com'],
        'mismatched_hosts_detected': [],
        'target_host_match_status': 'exact',
        'request_shape_hygiene_status': 'clean',
        'request_shape_hygiene_reason': 'all_detected_hosts_match_target',
        'request_shape_hygiene_source': 'execution_plan',
        'compiler': {'semantic_loss_policy': {'policy_response': 'proceed'}},
    }
    approved = build_approved_execution_spec(
        prepared,
        auditor={'decision': 'approve', 'reason': 'ok', 'reason_code': 'approve_in_scope', 'constraints': {}},
        approval_source='auditor',
        approval_transform_chain=[],
        owner_override_applied=False,
    )
    assert approved['execution_truth']['command_input_summary']['target_delivery_mode'] == 'stdin'
    assert approved['execution_truth']['command_input_summary']['stdin_present'] is True
    assert approved['execution_truth']['execution_input_summaries'][0]['tool'] == 'hakrawler'


def test_build_approved_execution_spec_does_not_fallback_preview_without_execution_plan() -> None:
    prepared = {
        'resolved_tool': 'hakrawler',
        'normalized_args': ['-d', '2', '-u'],
        'stdin': 'https://example.com/app\n',
        'execution_plan': [],
        'compiler': {'semantic_loss_policy': {'policy_response': 'proceed'}},
    }
    approved = build_approved_execution_spec(
        prepared,
        auditor={'decision': 'approve', 'reason': 'ok', 'reason_code': 'approve_in_scope', 'constraints': {}},
        approval_source='auditor',
        approval_transform_chain=[],
        owner_override_applied=False,
    )
    assert approved['execution_truth']['command_preview'] == []
    assert approved['execution_truth']['command_input_summary']['preview_source'] == 'none'
    assert approved['execution_truth']['command_input_summary']['stdin_present'] is False
    assert approved['execution_truth']['execution_input_summaries'] == []
