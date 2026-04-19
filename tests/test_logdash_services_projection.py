from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1] / 'logdash'
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services import build_agents_status_payload, build_campaign_info_payload, build_runtime_health_payload, load_host_state, load_runtime_state  # type: ignore
from runtime_economics_aggregate import aggregate_runtime_economics  # type: ignore


def test_build_agents_status_payload_prefers_snapshot_counts_and_marks_sources() -> None:
    payload = build_agents_status_payload(
        state={'state': 'running', 'prepared_attacks': 4, 'planner_scope_targets': 2},
        runtime={'auto_campaign': {'executed': 1}, 'runtime_plan': {'target_count': 1}},
        selected_campaign_key='camp-1',
        model_map={'planner': 'planner-x'},
        snap_campaign={'executed': 9},
        snap_plan={'target_count': 7},
        snap_latest={'mode': 'followup'},
    )
    assert payload['orchestrator']['items_processed'] == 9
    assert payload['planner']['items_processed'] == 7
    assert payload['orchestrator']['source'] == 'snapshot'
    assert payload['planner']['source'] == 'snapshot'
    assert payload['planner']['model'] == 'planner-x'


def test_build_campaign_info_payload_projects_runtime_and_campaign_fields() -> None:
    payload = build_campaign_info_payload(
        state={'selected_campaign_name': 'Camp A', 'aggression_effective': 4, 'runtime_plan_error_preview': 'runtime_plan_missing', 'request_decoration': {'mode': 'operator_supplied'}},
        current={
            'selected_campaign_key': 'camp-a',
            'snapshot': {'campaign': {'updated_at': 'snap-ts'}},
            'snap_campaign': {'executed': 5, 'max_runs': 111, 'started_at': 'start-ts', 'updated_at': 'snap-ts'},
            'snap_plan': {'plan_hash': 'feedfacecafebeef', 'plan_revision': 'r2'},
            'snap_latest': {'target': 'https://api.example.com/', 'mode': 'followup'},
            'runtime_plan': {'quality': {'grade': 'B', 'score': 66}, 'generated_at': 'plan-ts', 'plan_revision': 'r1'},
            'generated': 7,
            'target_count': 3,
        },
        settings={'max_runs': 111, 'aggression_override': 6, 'request_decoration': {'mode': 'operator_supplied', 'headers': [{'name': 'X-Canary', 'value': 'rc'}]}},
        cred_status='ready',
        cred_status_detail='owner approved',
        latest_payload={'run_id': 'run-1', 'executed': 4},
        latest_vectors=[{'target': 'https://api.example.com/', 'mode': 'followup'}],
    )
    assert payload['campaign_name'] == 'Camp A'
    assert payload['executed'] == 5
    assert payload['planner_scope_targets'] == 3
    assert payload['prepared_attacks'] == 7
    assert payload['runtime_plan_ok'] is True
    assert payload['runtime_snapshot_source'] == 'snapshot'
    assert payload['runtime_plan_revision'] == 'r2'
    assert payload['blueprint_hash'] == 'feedfacecafebeef'[:16]
    assert payload['credentials_status'] == 'ready'
    assert payload['request_decoration']['headers'][0]['name'] == 'X-Canary'



def test_build_runtime_health_payload_projects_snapshot_and_lineage_fields() -> None:
    payload = build_runtime_health_payload(
        runtime={'runtime_plan': {'plan_revision': 'r1', 'plan_hash': 'abcdef1234567890'}, 'auto_campaign': {'updated_at': 'auto-ts'}},
        snapshot={'campaign': {'updated_at': 'snap-ts'}},
        snap_campaign={'updated_at': 'snap-ts'},
        snap_plan={'plan_revision': 'r2', 'plan_hash': 'feedfacecafebeef'},
        snap_queues={'followup_count': 3, 'precision_count': 1},
        snap_telemetry={'execution_gate_skip_total': 5, 'dns_skip_total': 2, 'host_cooldown_skip_total': 1, 'precheck_skip_count': 4},
        snap_latest={
            'target': 'https://api.example.com/',
            'mode': 'followup',
            'decision_effective_status': 'ran',
            'semantic_lineage_summary': {'lineage_sha256': 'hash-1', 'current_stage': 'validation', 'next_stage': 'bounded_exploit_proof', 'action_type': 'single_probe', 'capability': 'http_probe'},
            'runtime_task': {'experiment_intent_id': 'intent-1', 'capability_lane': 'http'},
            'success_semantics': {'success_model': 'surface_expansion'},
            'adaptation_signal': {'reason': 'new-signal'},
        },
        stdout_bytes=12,
        stderr_bytes=8,
    )
    assert payload['runtime_snapshot_source'] == 'snapshot'
    assert payload['queue_followups'] == 3
    assert payload['queue_precision'] == 1
    assert payload['execution_gate_skip_total'] == 5
    assert payload['latest_target'] == 'https://api.example.com/'
    assert payload['latest_lineage_hash'] == 'hash-1'
    assert payload['latest_experiment_intent_id'] == 'intent-1'
    assert payload['runtime_plan_revision'] == 'r2'
    assert payload['runtime_plan_hash'] == 'feedfacecafebeef'[:16]


def test_load_runtime_state_and_host_state_expose_provenance_sources(tmp_path: Path) -> None:
    reports = tmp_path / 'reports'
    reports.mkdir()
    (reports / '.auto_campaign.state.json').write_text('{"updated_at": "auto-ts"}', encoding='utf-8')
    (reports / '.runtime_plan.meta.json').write_text('{"generated": 4, "target_count": 2}', encoding='utf-8')
    (reports / '.runtime_snapshot.json').write_text('{"latest_run": {"target": "https://example.com"}}', encoding='utf-8')
    host_state_path = reports / 'host-state.json'
    host_state_path.write_text('{"hosts": {"legacy.example.com": {"state": "active"}}}', encoding='utf-8')

    runtime = load_runtime_state(reports, reports / '.runtime_snapshot.json')
    host_state = load_host_state(host_state_path)

    assert runtime['sources']['auto_campaign'] == 'normalized_auto_campaign_state'
    assert runtime['sources']['runtime_plan'] == 'normalized_runtime_plan_meta'
    assert runtime['sources']['runtime_plan_quality'] == 'computed_fallback'
    assert runtime['sources']['snapshot'] == 'normalized_snapshot_file'
    assert runtime['sources']['snapshot_latest_run_lineage'] == 'normalized_lineage_summary'
    assert host_state['_source'] == 'normalized_host_state_file'


def test_aggregate_runtime_economics_includes_explainability_summary() -> None:
    econ = aggregate_runtime_economics([
        {
            'decision_explain': {'why': ['followup_selected_from_threshold'], 'blockers': ['confirm_precedence']},
            'decision_effective_status': 'applied',
            'decision_quality': {'decision_quality_score': 0.8},
            'runtime_utility': {'net_utility_score': 0.7},
            'decision_economics': {'cost_weight': 0.2, 'value_estimate': 0.9, 'priority_score': 0.7},
            'qualification': {'verdict': 'probable'},
            'signal_contract': {'success_outcome': {'status': 'partial'}},
            'task_family': 'recon',
            'target': 'https://a.example.com/',
        },
        {
            'decision_explain': {'why': ['followup_selected_from_threshold'], 'blockers': ['cooldown_active']},
            'decision_effective_status': 'blocked',
            'decision_quality': {'decision_quality_score': 0.2},
            'runtime_utility': {'net_utility_score': 0.1},
            'decision_economics': {'cost_weight': 0.3, 'value_estimate': 0.4, 'priority_score': 0.2},
            'qualification': {'verdict': 'none'},
            'signal_contract': {'success_outcome': {'status': 'none'}},
            'task_family': 'recon',
            'target': 'https://b.example.com/',
        },
    ])
    explain = econ['explainability']
    assert explain['top_why'][0]['key'] == 'followup_selected_from_threshold'
    assert explain['top_why'][0]['count'] == 2
    assert explain['effective_status_top'][0]['key'] in {'applied', 'blocked'}
    assert explain['avg_decision_quality'] == 0.5
    assert explain['avg_net_utility'] == 0.4
    assert 'explain' in econ['family_efficiency'][0]
