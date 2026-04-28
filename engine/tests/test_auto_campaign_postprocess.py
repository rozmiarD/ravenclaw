from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from auto_campaign_postprocess import post_result_common  # type: ignore


def test_post_result_common_adds_reason_prefix_and_command_preview() -> None:
    host_family_owner_gate = {}
    host_cooldown_until = {}
    host_code000_streak = {}
    host_code000_total = {}
    host_403_streak = {}
    host_fail_streak = {}
    host_fail_count = {}
    host_success_count = {}

    result = {
        'reason_code': 'interesting_signal',
        'planned_command': ['curl', 'https://example.com'],
        'engine': {'stdout': '__RC_METRICS__ code=200', 'stderr': ''},
        'success_criteria': {'status': 'partial'},
    }
    post = post_result_common(
        task_ctx={'task_family': 'recon', 'task_success_criteria': 'x', 'campaign_success_criteria': 'y'},
        result=result,
        objective='Passive recon',
        target='https://example.com/',
        mode='fast',
        summary_text='Base summary',
        classification='low',
        auditor='approved',
        engine_status='ok',
        run_index=1,
        plan_name='Plan A',
        owner_override=False,
        owner_auth=False,
        aggression=3,
        inspect_json_signal_from_command=lambda _cmd: {'info': [], 'findings': [], 'signal': False},
        parse_rc_metrics=lambda _txt: {'code': 200},
        run_control_comparison=lambda _cmd, _timeout: {'performed': False, 'control_delta_observed': False, 'reason': 'n/a'},
        attack_family_fn=lambda objective, target, family: family or 'generic',
        host_family_owner_gate=host_family_owner_gate,
        host_cooldown_until=host_cooldown_until,
        host_code000_streak=host_code000_streak,
        host_code000_total=host_code000_total,
        host_403_streak=host_403_streak,
        host_fail_streak=host_fail_streak,
        host_fail_count=host_fail_count,
        host_success_count=host_success_count,
        code000_streak_threshold=3,
        code000_cooldown_sec=600,
        code000_session_cap=10,
    )
    assert post['reason_code'] == 'interesting_signal'
    assert post['success_eval_status'] == 'partial'
    assert post['summary_text'].startswith('[interesting_signal]')
    assert 'CMD: curl https://example.com' in post['summary_text']
    assert post['run_info']['command_preview'] == 'curl https://example.com'


def test_post_result_common_preserves_request_shape_hygiene() -> None:
    post = post_result_common(
        task_ctx={'task_family': 'recon'},
        result={
            'reason_code': 'policy_gate_block',
            'planned_command': ['curl', 'https://www.bitstamp.net'],
            'engine': {'stdout': '', 'stderr': ''},
            'success_criteria': {'status': 'failed'},
            'request_shape_hygiene': {
                'request_shape_hygiene_status': 'cross_host_mismatch',
                'target_host_match_status': 'mixed',
                'mismatched_hosts_detected': ['insight2.tradepmr.com'],
            },
        },
        objective='Probe',
        target='https://www.bitstamp.net/',
        mode='fast',
        summary_text='Mismatch blocked',
        classification='low',
        auditor='owner_approval_required',
        engine_status='failed',
        run_index=3,
        plan_name='Plan C',
        owner_override=False,
        owner_auth=False,
        aggression=2,
        inspect_json_signal_from_command=lambda _cmd: {'info': [], 'findings': [], 'signal': False},
        parse_rc_metrics=lambda _txt: {'code': 0},
        run_control_comparison=lambda _cmd, _timeout: {'performed': False, 'control_delta_observed': False, 'reason': 'n/a'},
        attack_family_fn=lambda objective, target, family: family or 'generic',
        host_family_owner_gate={},
        host_cooldown_until={},
        host_code000_streak={},
        host_code000_total={},
        host_403_streak={},
        host_fail_streak={},
        host_fail_count={},
        host_success_count={},
        code000_streak_threshold=3,
        code000_cooldown_sec=600,
        code000_session_cap=10,
    )
    assert post['run_info']['request_shape_hygiene']['request_shape_hygiene_status'] == 'cross_host_mismatch'
    assert post['run_info']['request_shape_hygiene']['target_host_match_status'] == 'mixed'


def test_post_result_common_surfaces_stdin_input_summary() -> None:
    post = post_result_common(
        task_ctx={'task_family': 'content_discovery'},
        result={
            'reason_code': 'interesting_signal',
            'planned_command': ['hakrawler', '-d', '2', '-u'],
            'engine': {'stdout': '', 'stderr': ''},
            'success_criteria': {'status': 'partial'},
            'execution_lineage': {
                'approved_command_input_summary': {
                    'target_delivery_mode': 'stdin',
                    'stdin_present': True,
                    'stdin_preview': 'https://example.com/app\n',
                    'stdin_line_count': 1,
                    'stdin_char_count': 24,
                    'stdin_preview_truncated': False,
                },
            },
        },
        objective='Crawl target',
        target='https://example.com/app',
        mode='fast',
        summary_text='Crawler summary',
        classification='low',
        auditor='approved',
        engine_status='ok',
        run_index=4,
        plan_name='Plan D',
        owner_override=False,
        owner_auth=False,
        aggression=2,
        inspect_json_signal_from_command=lambda _cmd: {'info': [], 'findings': [], 'signal': False},
        parse_rc_metrics=lambda _txt: {'code': 0},
        run_control_comparison=lambda _cmd, _timeout: {'performed': False, 'control_delta_observed': False, 'reason': 'n/a'},
        attack_family_fn=lambda objective, target, family: family or 'generic',
        host_family_owner_gate={},
        host_cooldown_until={},
        host_code000_streak={},
        host_code000_total={},
        host_403_streak={},
        host_fail_streak={},
        host_fail_count={},
        host_success_count={},
        code000_streak_threshold=3,
        code000_cooldown_sec=600,
        code000_session_cap=10,
    )
    assert 'CMD: hakrawler -d 2 -u' in post['summary_text']
    assert 'INPUT: stdin:https://example.com/app\\n' in post['summary_text']
    assert post['run_info']['command_preview'] == 'hakrawler -d 2 -u'
    assert post['run_info']['command_input_summary']['target_delivery_mode'] == 'stdin'


def test_post_result_common_updates_owner_gate_and_403_cooldown() -> None:
    host_family_owner_gate = {}
    host_cooldown_until = {}
    host_code000_streak = {}
    host_code000_total = {}
    host_403_streak = {}
    host_fail_streak = {}
    host_fail_count = {}
    host_success_count = {}

    result = {
        'reason_code': 'http_403',
        'planned_command': ['curl', 'https://auth.example.com'],
        'engine': {'stdout': '__RC_METRICS__ code=403', 'stderr': ''},
        'success_criteria': {'status': 'failed'},
    }
    post = post_result_common(
        task_ctx={'task_family': 'authz'},
        result=result,
        objective='Authz probe',
        target='https://auth.example.com/',
        mode='followup',
        summary_text='HTTP 403 observed',
        classification='mid',
        auditor='owner_approval_required',
        engine_status='failed',
        run_index=2,
        plan_name='Plan B',
        owner_override=False,
        owner_auth=False,
        aggression=4,
        inspect_json_signal_from_command=lambda _cmd: {'info': [], 'findings': [], 'signal': False},
        parse_rc_metrics=lambda _txt: {'code': 403},
        run_control_comparison=lambda _cmd, _timeout: {'performed': True, 'control_delta_observed': False, 'reason': 'control'},
        attack_family_fn=lambda objective, target, family: family or 'generic',
        host_family_owner_gate=host_family_owner_gate,
        host_cooldown_until=host_cooldown_until,
        host_code000_streak=host_code000_streak,
        host_code000_total=host_code000_total,
        host_403_streak=host_403_streak,
        host_fail_streak=host_fail_streak,
        host_fail_count=host_fail_count,
        host_success_count=host_success_count,
        code000_streak_threshold=3,
        code000_cooldown_sec=600,
        code000_session_cap=10,
    )
    assert post['run_info']['auditor_decision'] == 'owner_approval_required'
    assert any(k[0] == 'auth.example.com' for k in host_family_owner_gate.keys())
    assert host_403_streak['auth.example.com'] == 1
    assert host_fail_streak['auth.example.com'] == 1
    assert 'auth.example.com' in host_cooldown_until
