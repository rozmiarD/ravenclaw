from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
ROOT = Path(__file__).resolve().parents[2]
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import security_contract_layer as scl  # type: ignore


def _validate(report: dict) -> None:
    scl.validate_scope_fidelity_report(report, root=ROOT)


def test_scope_fidelity_report_passes_exact_host_binding() -> None:
    report = scl.build_scope_fidelity_report(
        target='https://api.example.com/',
        target_in_scope=True,
        normalized_args=['-I', 'https://api.example.com/', '-H', 'Origin: https://api.example.com'],
        execution_plan=[{'tool': 'curl', 'role': 'probe', 'args': ['https://api.example.com/health']}],
    )
    _validate(report)
    assert report['artifact_type'] == 'scope_fidelity_report'
    assert report['verdict'] == 'pass'
    assert report['request_shape']['target_host_match_status'] == 'exact'
    assert report['request_shape']['request_shape_hygiene_status'] == 'clean'
    assert report['request_shape']['mismatched_hosts_detected'] == []
    assert report['public_safety']['live_target_execution'] is False


def test_scope_fidelity_report_fails_cross_host_drift() -> None:
    report = scl.build_scope_fidelity_report(
        target='https://api.example.com/',
        target_in_scope=True,
        normalized_args=['curl', 'https://api.example.com/', '-H', 'Origin: https://evil.example'],
        execution_plan=[{'tool': 'curl', 'role': 'probe', 'args': ['https://static.example.net/script.js']}],
    )
    _validate(report)
    assert report['verdict'] == 'fail'
    assert report['request_shape']['target_host_match_status'] == 'mixed'
    assert report['request_shape']['request_shape_hygiene_status'] == 'cross_host_mismatch'
    assert report['request_shape']['mismatched_hosts_detected'] == ['evil.example', 'static.example.net']
    assert report['request_shape']['request_shape_hygiene_source'] == 'normalized_args+execution_plan'


def test_scope_fidelity_report_marks_missing_hosts_for_review() -> None:
    report = scl.build_scope_fidelity_report(
        target='https://api.example.com/',
        target_in_scope=True,
        normalized_args=['--max-time', '5', '--retry', '2'],
        execution_plan=[{'tool': 'curl', 'role': 'probe', 'args': ['--max-time', '5']}],
    )
    _validate(report)
    assert report['verdict'] == 'review'
    assert report['request_shape']['target_host_match_status'] == 'none_detected'
    assert report['request_shape']['request_shape_hygiene_status'] == 'ambiguous'


def test_scope_fidelity_schema_rejects_non_public_safety_claim() -> None:
    report = scl.build_scope_fidelity_report(
        target='https://api.example.com/',
        normalized_args=['https://api.example.com/'],
        execution_plan=[],
    )
    report['public_safety']['live_target_execution'] = True
    try:
        _validate(report)
    except scl.JsonSchemaValidationError as exc:
        assert 'expected const False' in str(exc)
    else:  # pragma: no cover - assertion guard
        raise AssertionError('scope fidelity reports must stay local/public-safe')
