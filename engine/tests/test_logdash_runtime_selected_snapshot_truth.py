from __future__ import annotations

import sys
from pathlib import Path

from flask import Flask

ROOT = Path(__file__).resolve().parents[2]
LOGDASH_DIR = ROOT / 'logdash'
if str(LOGDASH_DIR) not in sys.path:
    sys.path.insert(0, str(LOGDASH_DIR))

from api_runtime import register_runtime_api  # type: ignore
from api_supplemental import register_supplemental_api  # type: ignore
from services import build_agents_status_payload, build_campaign_info_payload, build_runtime_health_payload, build_selected_campaign_projection, load_pipeline_config_effective_posture, projection_source_label, selected_runtime_snapshot_view  # type: ignore


def _build_app(*, state: dict, runtime: dict):
    app = Flask(__name__)
    runtime_state_path = ROOT / 'reports' / '.auto_campaign.state.json'
    runtime_pid_path = ROOT / 'reports' / '.auto_campaign.pid'

    def refresh_runtime_state() -> None:
        return None

    def load_runtime_state() -> dict:
        return runtime

    def load_runtime_snapshot() -> dict:
        snap = runtime.get('snapshot') if isinstance(runtime.get('snapshot'), dict) else {}
        return snap if isinstance(snap, dict) else {}

    def load_agent_models() -> dict:
        return {'planner': 'planner-model'}

    def selected_campaign_key() -> str:
        return str(state.get('selected_campaign_key') or '')

    def load_pipeline_config() -> dict:
        return {}

    def save_pipeline_config(payload: dict) -> dict:
        return payload

    def pipeline_config_meta() -> dict:
        return {}

    register_runtime_api(
        app,
        {
            'STATE': state,
            'refresh_runtime_state': refresh_runtime_state,
            'load_agent_models': load_agent_models,
            'selected_campaign_key': selected_campaign_key,
            'load_runtime_state': load_runtime_state,
            'load_runtime_snapshot': load_runtime_snapshot,
            'selected_runtime_snapshot_view': lambda runtime=None, selected_key=None: selected_runtime_snapshot_view(runtime, str(selected_key if selected_key is not None else selected_campaign_key())),
            'build_agents_status_payload': build_agents_status_payload,
            'build_selected_campaign_projection': build_selected_campaign_projection,
            'load_pipeline_config': load_pipeline_config,
            'save_pipeline_config': save_pipeline_config,
            'pipeline_config_meta': pipeline_config_meta,
            'load_pipeline_config_effective_posture': lambda: load_pipeline_config_effective_posture(load_pipeline_config()),
        },
    )

    def fetch_logs(page: int = 1, per_page: int = 20):
        return [], 0

    def get_conn():
        raise AssertionError('db access not expected in this test')

    def load_queue_state() -> dict:
        return {'followup_count': 99, 'precision_count': 77, 'followup_queue': ['old'], 'precision_queue': ['old']}

    def load_campaign_settings() -> dict:
        return {'global': {'max_runs': 300}}

    def save_campaign_settings(store: dict) -> None:
        return None

    def load_latest_blueprint():
        return None

    def _list_campaign_registry_items() -> list[dict]:
        return []

    def load_host_state() -> dict:
        return {'hosts': {}}

    def read_tail(path: Path, lines: int = 120) -> str:
        return ''

    def _load_owner_approval_actions() -> dict:
        return {'approved_ids': [], 'deleted_ids': []}

    def _save_owner_approval_actions(data: dict) -> None:
        return None

    def _owner_approval_row_ids() -> list[int]:
        return []

    def fetch_filtered_logs(page: int, per_page: int, keywords: list[str], exclude_ids: list[int] | None = None) -> dict:
        return {'items': [], 'total': 0, 'page': page, 'per_page': per_page}

    def save_planner_ui_state(data: dict) -> None:
        return None

    def load_planner_ui_state() -> dict:
        return {'selected_campaign_key': selected_campaign_key()}

    def save_orchestrator_state(data: dict) -> None:
        return None

    def write_runtime_state_file(local_state: dict, paused=None) -> None:
        return None

    register_supplemental_api(
        app,
        {
            'STATE': state,
            'STATUS_CLASSES': {},
            'fetch_logs': fetch_logs,
            'get_conn': get_conn,
            'refresh_runtime_state': refresh_runtime_state,
            'load_runtime_state': load_runtime_state,
            'load_queue_state': load_queue_state,
            'load_campaign_settings': load_campaign_settings,
            'save_campaign_settings': save_campaign_settings,
            'load_pipeline_config': load_pipeline_config,
            'save_pipeline_config': save_pipeline_config,
            'pipeline_config_meta': pipeline_config_meta,
            'load_latest_blueprint': load_latest_blueprint,
            'selected_campaign_key': selected_campaign_key,
            '_list_campaign_registry_items': _list_campaign_registry_items,
            'load_host_state': load_host_state,
            'read_tail': read_tail,
            'RUNTIME_STDOUT_PATH': ROOT / 'reports' / '.auto_campaign.stdout.log',
            'RUNTIME_STDERR_PATH': ROOT / 'reports' / '.auto_campaign.stderr.log',
            '_load_owner_approval_actions': _load_owner_approval_actions,
            '_save_owner_approval_actions': _save_owner_approval_actions,
            '_owner_approval_row_ids': _owner_approval_row_ids,
            'fetch_filtered_logs': fetch_filtered_logs,
            'save_planner_ui_state': save_planner_ui_state,
            'load_planner_ui_state': load_planner_ui_state,
            'HOST_STATE_PATH': ROOT / 'reports' / '.host_state.json',
            'save_orchestrator_state': save_orchestrator_state,
            'RUNTIME_PLAN_META_PATH': ROOT / 'reports' / '.runtime_plan.meta.json',
            'RUNTIME_PLAN_DELETE_PATHS': [ROOT / 'reports' / 'state' / 'public_targets_plan.json'],
            'PLANNER_REGISTRY_ROOT': ROOT / 'reports' / 'campaign_registry',
            'selected_runtime_snapshot_view': lambda runtime=None, selected_key=None: selected_runtime_snapshot_view(runtime, str(selected_key if selected_key is not None else selected_campaign_key())),
            'build_campaign_info_payload': build_campaign_info_payload,
            'build_runtime_health_payload': build_runtime_health_payload,
            'build_selected_campaign_projection': build_selected_campaign_projection,
            'projection_source_label': projection_source_label,
            'RUNTIME_SNAPSHOT_PATH': ROOT / 'reports' / '.runtime_snapshot.json',
            'RUNTIME_STATE_PATH': runtime_state_path,
            'RUNTIME_PID_PATH': runtime_pid_path,
            'ENGINE_DIR': ROOT / 'engine',
            'WORKSPACE_DIR': ROOT,
            'PYTHON_BIN': sys.executable,
            'write_runtime_state_file': write_runtime_state_file,
        },
    )

    app.testing = True
    return app.test_client()


def test_agents_status_ignores_snapshot_counts_from_other_campaign() -> None:
    state = {'selected_campaign_key': 'camp-new', 'planner_scope_targets': 19, 'prepared_attacks': 57, 'state': 'idle'}
    runtime = {
        'runtime_plan': {'campaign_key': 'camp-new', 'target_count': 19, 'generated': 57},
        'snapshot': {
            'campaign': {'campaign_key': 'camp-old', 'executed': 1},
            'plan': {'target_count': 3, 'generated': 10},
            'latest_run': {'mode': 'runtime'},
        },
    }
    client = _build_app(state=state, runtime=runtime)
    res = client.get('/api/agents-status')
    assert res.status_code == 200
    payload = res.get_json()
    assert payload['planner']['items_processed'] == 19
    assert payload['planner']['source'] == 'selected_campaign_runtime'
    assert payload['orchestrator']['items_processed'] == 57


def test_runtime_state_and_queue_state_hide_snapshot_from_other_campaign() -> None:
    state = {'selected_campaign_key': 'camp-new', 'planner_scope_targets': 19, 'prepared_attacks': 57, 'state': 'idle'}
    runtime = {
        'runtime_plan': {'campaign_key': 'camp-new', 'target_count': 19, 'generated': 57},
        'snapshot': {
            'campaign': {'campaign_key': 'camp-old', 'executed': 1, 'updated_at': '2026-03-27T17:59:42+00:00'},
            'plan': {'target_count': 3, 'generated': 10},
            'latest_run': {'target': 'https://old.example/'},
            'queues': {'followup_count': 5, 'precision_count': 2},
            'telemetry': {'semantic_loss_total': 9},
        },
    }
    client = _build_app(state=state, runtime=runtime)

    res = client.get('/api/runtime-state')
    assert res.status_code == 200
    payload = res.get_json()
    assert payload['runtime_plan']['target_count'] == 19
    assert payload['snapshot']['campaign'] == {}
    assert payload['snapshot']['plan'] == {}
    assert payload['snapshot']['latest_run'] == {}
    assert payload['snapshot']['queues'] == {}
    assert payload['snapshot']['telemetry'] == {}

    q = client.get('/api/queue-state')
    assert q.status_code == 200
    queue_payload = q.get_json()
    assert queue_payload['followup_count'] == 0
    assert queue_payload['precision_count'] == 0
    assert queue_payload['source'] == 'empty_selected_campaign_queue'


def test_runtime_trace_exposes_canonical_lineage_join_keys_and_decision_aliases() -> None:
    state = {'selected_campaign_key': 'camp-new', 'state': 'idle'}
    runtime = {
        'snapshot': {
            'campaign': {'campaign_key': 'camp-new', 'updated_at': '2026-04-10T18:00:00+00:00'},
            'latest_run': {
                'target': 'https://api.example.com/v1/users/123',
                'objective': 'Confirm bounded exploit proof',
                'task_family': 'authz',
                'mode': 'precision',
                'classification': 'candidate',
                'host_state_band': 'warm',
                'decision_requested_reason': 'strong_candidate_signal',
                'decision_selected_action': 'confirm',
                'decision_selected_secondary_action': 'followup',
                'decision_effective_action': 'confirm',
                'decision_effective_secondary_action': 'followup',
                'decision_effective_status': 'applied',
                'decision_effective_summary': 'selected=confirm;secondary=followup',
                'runtime_task': {
                    'action_type': 'differential_probe',
                    'capability': 'http_probe',
                    'experiment_intent_id': 'intent-123',
                },
                'semantic_lineage_summary': {
                    'lineage_sha256': 'lineage-123',
                    'planner_contract_sha256': 'planner-123',
                    'runtime_contract_sha256': 'runtime-123',
                    'experiment_intent_id': 'intent-123',
                    'task_family': 'authz',
                    'target': 'https://api.example.com/v1/users/123',
                    'current_stage': 'bounded_exploit_proof',
                    'next_stage': 'report_artifact_capture',
                    'action_type': 'differential_probe',
                    'capability': 'http_probe',
                },
            },
        },
    }
    client = _build_app(state=state, runtime=runtime)

    res = client.get('/api/runtime-trace')
    assert res.status_code == 200
    payload = res.get_json()
    assert payload['ok'] is True
    assert payload['decision']['requested_reason'] == 'strong_candidate_signal'
    assert payload['decision']['selected_secondary_action'] == 'followup'
    assert payload['decision']['effective_secondary_action'] == 'followup'
    assert payload['lineage']['lineage_sha256'] == 'lineage-123'
    assert payload['lineage']['planner_contract_sha256'] == 'planner-123'
    assert payload['lineage']['runtime_contract_sha256'] == 'runtime-123'
    assert payload['lineage']['experiment_intent_id'] == 'intent-123'
