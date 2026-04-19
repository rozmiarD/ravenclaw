from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_runner_result_summary as rrrs  # type: ignore



def test_summarize_result_reports_output_file_success() -> None:
    out = rrrs.summarize_result(
        {
            'engine': {
                'status': 'success',
                'command': 'curl https://api.example.com/ -o out.json',
                'stdout': '',
                'stderr': '',
            },
            'auditor': {'decision': 'approve'},
        },
        classify_fn=lambda result: 'unknown',
        parse_rc_metrics_fn=lambda text: {},
    )
    assert out == (
        'unknown',
        'approve',
        'success',
        'Success — request completed and response was saved to output file (-o).',
        False,
    )



def test_summarize_result_applies_metric_override_for_403() -> None:
    out = rrrs.summarize_result(
        {
            'engine': {
                'status': 'failed',
                'stdout': '__RC_METRICS__ code=403',
                'stderr': '',
            },
            'auditor': {'decision': 'approve'},
        },
        classify_fn=lambda result: 'unknown',
        parse_rc_metrics_fn=lambda text: {'code': '403'},
    )
    assert out == (
        'blocked',
        'approve',
        'failed',
        'Blocked by origin/WAF policy (HTTP 403).',
        False,
    )



def test_summarize_result_uses_auditor_block_summary() -> None:
    out = rrrs.summarize_result(
        {
            'engine': {'status': 'blocked', 'stdout': '', 'stderr': ''},
            'auditor': {'decision': 'reject', 'reason': 'out of scope', 'reason_code': 'scope'},
        },
        classify_fn=lambda result: 'unknown',
        parse_rc_metrics_fn=lambda text: {},
    )
    assert out == (
        'unknown',
        'reject',
        'unknown',
        'Blocked by auditor/policy: [scope] out of scope',
        False,
    )
