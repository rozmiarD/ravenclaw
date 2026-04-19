from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1] / 'logdash'
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import app as logdash_app  # type: ignore


def test_logdash_pages_render():
    client = logdash_app.app.test_client()
    for path in ['/', '/findings', '/campaign-setup', '/system-settings', '/owner-actions']:
        resp = client.get(path)
        assert resp.status_code == 200, path
    settings_html = client.get('/system-settings').get_data(as_text=True)
    assert 'plannerProfileSelect' in settings_html
    assert 'plannerProfileActiveBadge' in settings_html
    index_html = client.get('/').get_data(as_text=True)
    assert 'Exploit Ladder / Evidence Truth' in index_html
    assert 'Evaluation / Governance Summary' in index_html
    findings_html = client.get('/findings').get_data(as_text=True)
    assert 'Exploit Ladder / Evidence Truth' in findings_html
    assert 'Evaluation / Governance Summary' in findings_html


def test_logdash_core_api_surface():
    client = logdash_app.app.test_client()
    for path in [
        '/api/agents-status',
        '/api/campaign-info',
        '/api/metrics',
        '/api/runtime-state',
        '/api/queue-state',
        '/api/runtime-health',
        '/api/runtime-trace',
        '/api/evaluation-summary',
        '/api/logs',
        '/api/pipeline-config',
        '/api/pipeline-config/meta',
        '/api/planner-info',
        '/api/planner/campaigns',
        '/api/planner/selection',
        '/api/planner/budgets-view',
    ]:
        resp = client.get(path)
        assert resp.status_code == 200, path
        assert resp.is_json, path

    scope_view = client.get('/api/planner/scope-view')
    assert scope_view.status_code in {200, 404}
    assert scope_view.is_json

    runtime_plan_view_resp = client.get('/api/planner/runtime-plan-view')
    assert runtime_plan_view_resp.status_code in {200, 404}
    assert runtime_plan_view_resp.is_json

    runtime = client.get('/api/runtime-state').get_json()
    assert 'snapshot' in runtime

    pipeline_meta = client.get('/api/pipeline-config/meta').get_json()
    assert 'effective_posture' in pipeline_meta
    assert 'preset_key' in pipeline_meta['effective_posture']
    assert 'is_custom' in pipeline_meta['effective_posture']

    campaign_info = client.get('/api/campaign-info').get_json()
    assert 'runtime_snapshot_source' in campaign_info
    assert 'runtime_snapshot_updated' in campaign_info

    planner_info = client.get('/api/planner-info').get_json()
    for key in ['runtime_snapshot_source', 'plan_revision', 'prepared_attacks', 'planner_scope_targets']:
        assert key in planner_info

    runtime_plan_view_resp = client.get('/api/planner/runtime-plan-view')
    runtime_plan_view = runtime_plan_view_resp.get_json()
    if runtime_plan_view_resp.status_code == 200:
        assert 'meta' in runtime_plan_view
        assert 'source' in runtime_plan_view['meta']
    else:
        assert runtime_plan_view['ok'] is False
        assert runtime_plan_view['error'] == 'runtime_plan_missing'

    runtime_health = client.get('/api/runtime-health').get_json()
    for key in ['runtime_snapshot_source', 'queue_followups', 'queue_precision', 'execution_gate_skip_total', 'runtime_plan_revision', 'runtime_plan_hash']:
        assert key in runtime_health

    runtime_trace = client.get('/api/runtime-trace').get_json()
    for key in ['ok', 'run_identity', 'ladder', 'prerequisites', 'signal_status', 'decision', 'governance', 'lineage', 'replay', 'trace_sources']:
        assert key in runtime_trace
    assert runtime_trace['source'] in {'latest_trace_row', 'latest_run_payload_fallback'}
    if runtime_trace['ok']:
        assert 'ladder' in runtime_trace['trace_sources']
        assert 'decision' in runtime_trace['trace_sources']

    evaluation_summary = client.get('/api/evaluation-summary').get_json()
    for key in ['ok', 'yield_metrics', 'governance_metrics', 'auth_state_metrics', 'semantic_class_metrics', 'queue_metrics']:
        assert key in evaluation_summary

    metrics = client.get('/api/metrics').get_json()
    for key in ['runtime_snapshot_source', 'queue_followups', 'queue_precision', 'execution_gate_skip_total']:
        assert key in metrics

    host_state = client.get('/api/host-state').get_json()
    assert host_state['ok'] is True
    if host_state.get('items'):
        assert 'explain' in host_state['items'][0]
    assert 'source' in host_state
    assert host_state['source'] in {'snapshot', 'normalized_host_state_file', 'missing_host_state', 'invalid_host_state'}

    host_yield = client.get('/api/host-yield').get_json()
    assert host_yield['ok'] is True
    assert 'source' in host_yield
    assert host_yield['source'] in {'snapshot', 'legacy_runtime_vectors'}

    capability_yield = client.get('/api/capability-yield').get_json()
    assert capability_yield['ok'] is True

    family_yield = client.get('/api/family-yield').get_json()
    assert family_yield['ok'] is True
    assert 'source' in family_yield
    assert family_yield['source'] in {'snapshot', 'legacy_runtime_vectors'}

    queue = client.get('/api/queue-state').get_json()
    assert 'source' in queue or ('followup_queue' in queue and 'precision_queue' in queue)


def test_logdash_post_flows():
    client = logdash_app.app.test_client()

    resp = client.post('/api/planner/selection', json={'selected_campaign_key': 'test-campaign'})
    assert resp.status_code == 200
    assert resp.get_json()['selected_campaign_key'] == 'test-campaign'

    resp = client.post('/api/campaign/settings', json={'max_runs': 111, 'owner_override': True, 'request_decoration': {'mode': 'operator_supplied', 'headers': [{'name': 'X-Canary', 'value': 'rc'}], 'cookies': [{'name': 'session', 'value': 'abc'}], 'basic_auth': {'enabled': False, 'username': '', 'password': '', 'password_ref': ''}, 'provenance_notes': ['test']}})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['ok'] is True
    assert data['max_runs'] == 111
    assert data['request_decoration']['headers'][0]['name'] == 'X-Canary'

    campaign_settings = client.get('/api/campaign/settings')
    assert campaign_settings.status_code == 200
    rd = campaign_settings.get_json()['request_decoration']
    assert rd['cookies'][0]['name'] == 'session'

    campaign_info = client.get('/api/campaign-info')
    assert campaign_info.status_code == 200
    payload = campaign_info.get_json()
    assert payload['request_decoration']['headers'][0]['name'] == 'X-Canary'
    assert payload['request_decoration']['cookies'][0]['name'] == 'session'
    assert payload['request_decoration']['mode'] == 'operator_supplied'

    for action in ['start', 'pause', 'stop']:
        resp = client.post('/api/campaign/control', json={'action': action})
        assert resp.status_code in {200, 400}
        assert resp.is_json
        payload = resp.get_json()
        assert 'ok' in payload
        if resp.status_code == 400:
            assert 'error' in payload

    resp = client.post('/api/campaign/owner-override', json={'enabled': True})
    assert resp.status_code == 200
    assert resp.get_json()['owner_override'] is True


def test_agents_status_has_expected_roles():
    client = logdash_app.app.test_client()
    data = client.get('/api/agents-status').get_json()
    for role in ['orchestrator', 'planner', 'brain', 'auditor', 'execution', 'analysis', 'light']:
        assert role in data
    assert 'source' in data['orchestrator']
    assert 'source' in data['planner']


def test_logdash_decision_consistency_api_fields_exist():
    client = logdash_app.app.test_client()

    quality = client.get('/api/finding-quality')
    assert quality.status_code == 200
    q = quality.get_json()
    assert q['ok'] is True
    for key in ['quality_telemetry', 'lifecycle', 'decision_intent_totals', 'decision_effective_totals', 'effective_status_counts', 'runtime_snapshot_source', 'queue_followups', 'queue_precision', 'skip_telemetry', 'latest_run', 'explainability']:
        assert key in q

    findings = client.get('/api/findings-table')
    assert findings.status_code == 200
    payload = findings.get_json()
    assert 'items' in payload
    if payload['items']:
        item = payload['items'][0]
        for key in ['decision_intent_flags', 'decision_effective_flags', 'decision_effective_status', 'decision_effective_summary', 'decision_effective_reasons', 'decision_effective_blockers', 'execution_gate', 'host_state_band', 'host_transition', 'host_regeneration_reason', 'runtime_task', 'semantic_lineage_summary', 'signal_contract', 'success_semantics', 'workflow_promotion_status', 'finding_signal_status', 'success_outcome_status', 'adaptation_feedback_status']:
            assert key in item


def test_logdash_tool_registry_summary_exposes_runtime_tool_policy():
    client = logdash_app.app.test_client()
    resp = client.get('/api/tool-registry/summary')
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'planner_visible_tools' in data
    assert 'execution_allowed_tools' in data
    assert 'planner_visible_count' in data
    assert 'execution_allowed_count' in data
    assert isinstance(data['planner_visible_tools'], list)
    assert isinstance(data['execution_allowed_tools'], list)
    assert data['planner_visible_count'] == len(data['planner_visible_tools'])
    assert data['execution_allowed_count'] == len(data['execution_allowed_tools'])


def test_logdash_host_explain_returns_explanations_list():
    client = logdash_app.app.test_client()
    resp = client.get('/api/host-explain?host=nonexistent.example.com')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['ok'] is True
    assert isinstance(data['explanations'], list)
