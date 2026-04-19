from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from runtime_runner_finalize import finalize_runner_outputs  # type: ignore


def test_finalize_runner_outputs_writes_summary_and_flushes(tmp_path: Path) -> None:
    out_path = tmp_path / 'summary.json'
    calls = []
    summary = finalize_runner_outputs(
        runs=[{'target': 'https://a.example.com/'}],
        campaign_validation={'ok': True},
        run_started=datetime.now(timezone.utc),
        max_runs=5,
        time_budget_min=10,
        retry_policy='balanced',
        out_path=str(out_path),
        reports_dir=tmp_path,
        archive_root=tmp_path / 'archive',
        output_quality_telemetry={'probable': 1},
        finalize_outputs_fn=lambda **kwargs: {'executed': 1},
        flush_precheck_summary_fn=lambda force=False: calls.append(('precheck', force)),
        flush_dns_skip_summary_fn=lambda force=False: calls.append(('dns', force)),
        flush_host_cooldown_summary_fn=lambda force=False: calls.append(('cooldown', force)),
        flush_execution_gate_summary_fn=lambda force=False: calls.append(('gate', force)),
        log_operation_fn=lambda *args, **kwargs: calls.append(('log', kwargs.get('success'))),
        success=True,
    )
    assert summary['quality_telemetry']['probable'] == 1
    assert json.loads(out_path.read_text())['quality_telemetry']['probable'] == 1
    assert ('gate', True) in calls
    assert ('log', True) in calls


def test_finalize_runner_outputs_logs_failure_path(tmp_path: Path) -> None:
    calls = []
    out = finalize_runner_outputs(
        runs=[],
        campaign_validation={},
        run_started=datetime.now(timezone.utc),
        max_runs=1,
        time_budget_min=1,
        retry_policy='balanced',
        out_path=str(tmp_path / 'summary.json'),
        reports_dir=tmp_path,
        archive_root=tmp_path / 'archive',
        output_quality_telemetry={},
        finalize_outputs_fn=lambda **kwargs: {'executed': 0},
        flush_precheck_summary_fn=lambda force=False: calls.append(('precheck', force)),
        flush_dns_skip_summary_fn=lambda force=False: calls.append(('dns', force)),
        flush_host_cooldown_summary_fn=lambda force=False: calls.append(('cooldown', force)),
        flush_execution_gate_summary_fn=lambda force=False: calls.append(('gate', force)),
        log_operation_fn=lambda *args, **kwargs: calls.append(('log', kwargs.get('success'))),
        success=False,
        error=RuntimeError('boom'),
    )
    assert out is None
    assert ('gate', True) in calls
    assert ('log', False) in calls
