from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from auto_campaign_state import flush_skip_summaries, persist_live_snapshot  # type: ignore


def test_flush_skip_summaries_emits_execution_gate_summary_and_clears_counts() -> None:
    events = []
    gate_counts = {'warmup_gate_skip': 2, 'deep_budget_skip': 1}
    gate_examples = {'warmup_gate_skip': ['https://auth.example.com/;family=authz;state=warmup']}

    flush_skip_summaries(
        precheck_skip_count_ref=[0],
        precheck_skip_examples_ref=[],
        dns_skip_count_ref={},
        host_cooldown_skip_count_ref={},
        execution_gate_skip_count_ref=gate_counts,
        execution_gate_skip_examples_ref=gate_examples,
        log_event_fn=lambda *args, **kwargs: events.append((args, kwargs)),
        force=True,
    )

    assert gate_counts == {}
    assert gate_examples == {}
    assert any(args[1] == 'execution_gate_summary' for args, _kwargs in events)


def test_persist_live_snapshot_writes_gate_skip_counts_into_queue_state(tmp_path: Path) -> None:
    out_path = tmp_path / 'live.json'
    snapshot_path = tmp_path / 'snapshot.json'
    captured = {}

    persist_live_snapshot(
        out_path=str(out_path),
        save_queue_state_fn=lambda state: captured.update(state),
        campaign_key='demo',
        campaign_validation={'ok': True},
        run_started=datetime.now(timezone.utc),
        max_runs=10,
        time_budget_min=60,
        retry_policy='balanced',
        runs=[{
            'index': 1,
            'objective': 'Recon',
            'target': 'https://a.example.com/',
            'mode': 'fast',
            'engine_status': 'ok',
            'decision_effective_status': 'applied',
            'task_family': 'recon',
            'promising': True,
            'qualification': {'verdict': 'probable'},
            'brain': {'capability': 'content_discovery'},
            'brain_reasoning_summary': {'capability': 'content_discovery'},
            'runtime_task': {'capability_lane': 'content_discovery', 'experiment_intent_id': 'intent-recon-1'},
            'adaptation_signal': {'reason': 'capability_lane_stalled:content_discovery', 'source': 'capability_lane'},
            'signal_contract': {'success_outcome': {'status': 'partial'}},
            'success_semantics': {'success_model': 'surface_expansion'},
            'decision_economics': {'priority_score': 1.2, 'value_estimate': 0.8, 'cost_weight': 0.2},
            'runtime_utility': {'net_utility_score': 0.7, 'contamination_status': 'clean'},
            'run_contamination': {'status': 'clean', 'learning_excluded': False, 'tags': []},
            'request_shape_hygiene': {'request_shape_hygiene_status': 'clean', 'target_host_match_status': 'exact'},
            'engine_compiler': {'semantic_loss_detected': True, 'semantic_loss_policy': {'loss_class': 'bounded_lowering', 'policy_response': 'auditor_rereview', 'approved_under_degradation': True}},
            'semantic_loss_policy': {'loss_class': 'bounded_lowering', 'policy_response': 'auditor_rereview', 'approved_under_degradation': True},
            'semantic_loss_rereview_required': True,
            'semantic_loss_rereview_completed': True,
            'semantic_loss_rereview_decision': 'approve',
        }],
        followup_queue=[{'target': 'https://a.example.com/', 'task_family': 'recon', 'capability_lane': 'content_discovery', 'experiment_intent_id': 'intent-recon-1', 'success_semantics': {'success_model': 'surface_expansion'}}],
        precision_queue=[],
        precheck_skip_count=2,
        dns_skip_count={'a.example.com': 3},
        host_cooldown_skip_count={'b.example.com': 1},
        execution_gate_skip_count={'warmup_gate_skip': 4},
        quality_telemetry={'probable': 1, 'confirmed': 0},
        runtime_snapshot_path=str(snapshot_path),
        runtime_plan_meta={'plan_revision': 7, 'plan_hash': 'abc123', 'generated': 4, 'target_count': 2, 'generated_at': '2026-03-11T18:00:00+00:00'},
        host_state={'hosts': {'a.example.com': {'state': 'promising', 'state_band': 'promising', 'promise_score': 1.2, 'noise_score': 0.9, 'evidence_density': 0.7, 'novelty_score': 0.6, 'preferred_families': ['recon'], 'suppressed_families': [], 'last_success_family': 'recon', 'last_transition_reason': 'transition:active->promising', 'last_transition_at_runs': 1}}},
    )

    payload = json.loads(out_path.read_text(encoding='utf-8'))
    snapshot = json.loads(snapshot_path.read_text(encoding='utf-8'))
    assert payload['executed'] == 1
    assert captured['followup_queue'][0]['queue_lane'] == 'followup'
    assert '_queue_lane' not in captured['followup_queue'][0]
    assert captured['precheck_skip_count'] == 2
    assert captured['dns_skip_count']['a.example.com'] == 3
    assert captured['host_cooldown_skip_count']['b.example.com'] == 1
    assert captured['execution_gate_skip_count']['warmup_gate_skip'] == 4
    assert snapshot['campaign']['campaign_key'] == 'demo'
    assert snapshot['plan']['plan_revision'] == 7
    assert snapshot['plan']['generated'] == 4
    assert snapshot['queues']['followup_count'] == 1
    assert snapshot['queues']['followup_queue'][0]['queue_lane'] == 'followup'
    assert '_queue_lane' not in snapshot['queues']['followup_queue'][0]
    assert snapshot['queues']['followup_preview'][0]['queue_lane'] == 'followup'
    assert snapshot['queues']['followup_preview'][0]['capability_lane'] == 'content_discovery'
    assert snapshot['queues']['followup_preview'][0]['experiment_intent_id'] == 'intent-recon-1'
    assert snapshot['telemetry']['execution_gate_skip_total'] == 4
    assert snapshot['telemetry']['semantic_loss_total'] == 1
    assert snapshot['telemetry']['semantic_loss_by_class']['bounded_lowering'] == 1
    assert snapshot['telemetry']['semantic_rereview_total'] == 1
    assert snapshot['telemetry']['contamination']['status_count']['clean'] == 1
    assert snapshot['telemetry']['contamination']['request_shape_hygiene_count']['clean'] == 1
    assert snapshot['hosts']['count'] == 1
    assert snapshot['hosts']['items'][0]['host'] == 'a.example.com'
    assert snapshot['economics']['family_efficiency'][0]['key'] == 'recon'
    assert snapshot['latest_run']['target'] == 'https://a.example.com/'
    assert snapshot['latest_run']['capability'] == 'content_discovery'
    assert snapshot['latest_run']['capability_lane'] == 'content_discovery'
    assert snapshot['latest_run']['runtime_task']['queue_lane'] == 'followup'
    assert '_queue_lane' not in snapshot['latest_run']['runtime_task']
    assert snapshot['latest_run']['experiment_intent_id'] == 'intent-recon-1'
    assert snapshot['latest_run']['success_semantics']['success_model'] == 'surface_expansion'
    assert snapshot['latest_run']['adaptation_signal']['reason'] == 'capability_lane_stalled:content_discovery'
    assert snapshot['latest_run']['run_contamination']['status'] == 'clean'
    assert snapshot['latest_run']['request_shape_hygiene']['request_shape_hygiene_status'] == 'clean'
    assert snapshot['latest_run']['semantic_loss_policy']['loss_class'] == 'bounded_lowering'
    assert snapshot['latest_run']['semantic_loss_rereview_required'] is True
    assert snapshot['latest_run']['semantic_loss_rereview_completed'] is True
    assert snapshot['latest_run']['semantic_lineage']['artifact_boundaries']['lineage_sha256']
    assert snapshot['latest_run']['semantic_lineage_summary']['lineage_sha256'] == snapshot['latest_run']['semantic_lineage']['artifact_boundaries']['lineage_sha256']
