from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'logdash'
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import app as logdash_app  # type: ignore
from services import load_queue_state, load_runtime_state  # type: ignore


def test_snapshot_and_logdash_views_stay_consistent(tmp_path: Path) -> None:
    reports = tmp_path / 'reports'
    reports.mkdir()
    snapshot_path = reports / '.runtime_snapshot.json'
    auto_path = reports / '.auto_campaign.state.json'
    plan_meta = reports / '.runtime_plan.meta.json'
    queue_state = reports / '.auto_campaign.queues.json'

    snapshot = {
        'campaign': {'updated_at': '2026-03-12T17:00:00+00:00', 'executed': 3},
        'plan': {'plan_revision': 9, 'plan_hash': 'abc123456789', 'generated': 6, 'target_count': 2},
        'queues': {'followup_count': 2, 'precision_count': 1, 'followup_queue': [{'target': 'https://a.example.com/'}], 'precision_queue': []},
        'telemetry': {'execution_gate_skip_total': 5, 'execution_gate_skip_count': {'warmup_gate_skip': 5}, 'action_type_count': {'differential_probe': 2}, 'semantic_loss_total': 1},
        'latest_run': {'target': 'https://a.example.com/', 'decision_effective_status': 'blocked', 'brain_reasoning_summary': {'action_type': 'single_probe'}, 'analysis_contract': {'expected_signal_observed': 'partial'}, 'semantic_lineage': {'artifact_boundaries': {'lineage_sha256': 'abc123'}, 'planner_contract': {'planning_ladder': {'current_stage': 'validation', 'next_stage': 'bounded_exploit_proof'}}, 'runtime_contract': {'action_type': 'differential_probe', 'capability': 'http_probe'}}, 'semantic_lineage_summary': {'lineage_sha256': 'abc123', 'current_stage': 'validation', 'next_stage': 'bounded_exploit_proof', 'action_type': 'differential_probe', 'capability': 'http_probe'}},
    }
    snapshot_path.write_text(json.dumps(snapshot), encoding='utf-8')
    auto_path.write_text(json.dumps({'updated_at': '2026-03-12T17:00:00+00:00'}), encoding='utf-8')
    plan_meta.write_text(json.dumps({'plan_revision': 9, 'plan_hash': 'abc123456789', 'generated': 6, 'target_count': 2}), encoding='utf-8')
    queue_state.write_text(json.dumps({'followup_queue': [], 'precision_queue': []}), encoding='utf-8')

    runtime = load_runtime_state(reports, snapshot_path)
    queue = load_queue_state(queue_state, snapshot_path)
    assert runtime['snapshot']['telemetry']['execution_gate_skip_total'] == 5
    assert runtime['snapshot']['telemetry']['action_type_count']['differential_probe'] == 2
    assert runtime['snapshot']['latest_run']['semantic_lineage_summary']['lineage_sha256'] == 'abc123'
    assert queue['source'] == 'runtime_snapshot'
    assert queue['execution_gate_skip_count']['warmup_gate_skip'] == 5


def test_logdash_runtime_health_exposes_snapshot_contract() -> None:
    client = logdash_app.app.test_client()
    data = client.get('/api/runtime-health').get_json()
    assert 'execution_gate_skip_total' in data
    assert 'action_type_count' in data
    assert 'semantic_loss_total' in data
    assert 'latest_expected_signal_observed' in data
    assert 'latest_lineage_hash' in data
    assert 'latest_lineage_stage' in data
    assert 'latest_action_type' in data
    assert 'latest_lineage_action_type' in data
    assert 'latest_lineage_capability' in data
    if data['latest_lineage_action_type'] not in {'', '-'}:
        assert data['latest_action_type'] == data['latest_lineage_action_type']
    assert 'runtime_snapshot_source' in data
    assert 'runtime_plan_revision' in data
