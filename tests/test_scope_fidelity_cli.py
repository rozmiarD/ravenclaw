from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / 'scripts'
ENGINE_DIR = ROOT / 'engine'
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

import build_scope_fidelity_report as builder  # type: ignore
import security_contract_layer as scl  # type: ignore


def test_report_from_local_spec_detects_cross_host_drift() -> None:
    report = builder.report_from_spec({
        'target': 'https://api.example.com/',
        'target_in_scope': True,
        'normalized_args': ['https://api.example.com/', '-H', 'Origin: https://static.example.net'],
        'execution_plan': [{'tool': 'curl', 'role': 'probe', 'args': ['https://cdn.example.org/app.js']}],
    })
    scl.validate_scope_fidelity_report(report, root=ROOT)
    assert report['verdict'] == 'fail'
    assert report['request_shape']['mismatched_hosts_detected'] == ['static.example.net', 'cdn.example.org']


def test_scope_fidelity_cli_builds_report_from_spec_file(tmp_path: Path) -> None:
    spec = tmp_path / 'approved_spec.json'
    spec.write_text(json.dumps({
        'target': 'https://api.example.com/',
        'target_in_scope': True,
        'normalized_args': ['-I', 'https://api.example.com/'],
        'execution_plan': [{'tool': 'curl', 'role': 'probe', 'args': ['https://api.example.com/health']}],
    }), encoding='utf-8')
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / 'build_scope_fidelity_report.py'), '--spec', str(spec)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    report = json.loads(proc.stdout)
    scl.validate_scope_fidelity_report(report, root=ROOT)
    assert report['verdict'] == 'pass'
    assert report['public_safety']['live_target_execution'] is False


def test_scope_fidelity_cli_builds_report_from_manual_args() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS_DIR / 'build_scope_fidelity_report.py'),
            '--target',
            'https://api.example.com/',
            '--arg',
            'https://api.example.com/',
            '--arg',
            'https://other.example.net/',
            '--compact',
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    report = json.loads(proc.stdout)
    assert report['verdict'] == 'fail'
    assert report['target_host'] == 'api.example.com'


def test_scope_fidelity_cli_fail_on_fail_returns_nonzero() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS_DIR / 'build_scope_fidelity_report.py'),
            '--target',
            'https://api.example.com/',
            '--arg',
            'https://other.example.net/',
            '--fail-on',
            'fail',
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2
    report = json.loads(proc.stdout)
    assert report['verdict'] == 'fail'


def test_scope_fidelity_cli_fail_on_review_returns_nonzero_for_ambiguous() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS_DIR / 'build_scope_fidelity_report.py'),
            '--target',
            'https://api.example.com/',
            '--arg',
            'max-time',
            '--arg',
            '5',
            '--fail-on',
            'review',
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2
    report = json.loads(proc.stdout)
    assert report['verdict'] == 'review'


def test_scope_fidelity_cli_fail_on_fail_allows_review_by_default_threshold() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS_DIR / 'build_scope_fidelity_report.py'),
            '--target',
            'https://api.example.com/',
            '--arg',
            'max-time',
            '--arg',
            '5',
            '--fail-on',
            'fail',
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    report = json.loads(proc.stdout)
    assert report['verdict'] == 'review'
