from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

from flask import Flask

ROOT = Path(__file__).resolve().parents[2]
LOGDASH_DIR = ROOT / 'logdash'
if str(LOGDASH_DIR) not in sys.path:
    sys.path.insert(0, str(LOGDASH_DIR))

from api_supplemental import register_supplemental_api  # type: ignore
from services import build_campaign_info_payload, build_runtime_health_payload, build_selected_campaign_projection, projection_source_label, selected_runtime_snapshot_view  # type: ignore


def _build_client(*, state: dict, runtime: dict, campaign_store: dict, planner_ui: dict, orchestrator_state: dict, runtime_plan_meta_path: Path, runtime_plan_delete_paths: list[Path], planner_registry_root: Path, runtime_snapshot_path: Path):
    app = Flask(__name__)
    runtime_state_path = runtime_snapshot_path.parent / '.auto_campaign.state.json'
    runtime_pid_path = runtime_snapshot_path.parent / '.auto_campaign.pid'

    def fetch_logs(page: int = 1, per_page: int = 20):
        return [], 0

    def get_conn():
        raise AssertionError('db access not expected in this test')

    def refresh_runtime_state() -> None:
        return None

    def load_runtime_state() -> dict:
        return runtime

    def load_queue_state() -> dict:
        return {}

    def load_campaign_settings() -> dict:
        return campaign_store

    def save_campaign_settings(store: dict) -> None:
        snapshot = copy.deepcopy(store)
        campaign_store.clear()
        campaign_store.update(snapshot)

    def load_pipeline_config() -> dict:
        return {}

    def save_pipeline_config(payload: dict) -> dict:
        return payload

    def pipeline_config_meta() -> dict:
        return {}

    def load_latest_blueprint():
        return None

    def selected_campaign_key() -> str:
        return str(state.get('selected_campaign_key') or '')

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
        snapshot = copy.deepcopy(data)
        planner_ui.clear()
        planner_ui.update(snapshot)

    def load_planner_ui_state() -> dict:
        return planner_ui

    def save_orchestrator_state(data: dict) -> None:
        orchestrator_state.clear()
        orchestrator_state.update(data)

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
            'RUNTIME_PLAN_META_PATH': runtime_plan_meta_path,
            'RUNTIME_PLAN_DELETE_PATHS': runtime_plan_delete_paths,
            'PLANNER_REGISTRY_ROOT': planner_registry_root,
            'selected_runtime_snapshot_view': lambda runtime=None, selected_key=None: selected_runtime_snapshot_view(runtime, str(selected_key if selected_key is not None else selected_campaign_key())),
            'build_campaign_info_payload': build_campaign_info_payload,
            'build_runtime_health_payload': build_runtime_health_payload,
            'build_selected_campaign_projection': build_selected_campaign_projection,
            'projection_source_label': projection_source_label,
            'RUNTIME_SNAPSHOT_PATH': runtime_snapshot_path,
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


def test_delete_current_removes_campaign_registry_and_active_plan_artifacts_but_keeps_global_settings(tmp_path: Path) -> None:
    key = 'camp-delete-me'
    registry_root = tmp_path / 'campaign_registry'
    campaign_dir = registry_root / key / 'versions' / 'v0001'
    campaign_dir.mkdir(parents=True)
    (campaign_dir / 'blueprint.json').write_text('{}', encoding='utf-8')
    runtime_plan_path = tmp_path / 'state' / 'public_targets_plan.json'
    runtime_plan_path.parent.mkdir(parents=True)
    runtime_plan_path.write_text('[]', encoding='utf-8')
    legacy_plan_path = tmp_path / 'public_targets_plan.json'
    legacy_plan_path.write_text('[]', encoding='utf-8')
    runtime_plan_meta_path = tmp_path / '.runtime_plan.meta.json'
    runtime_plan_meta_path.write_text(json.dumps({'campaign_key': key}), encoding='utf-8')
    runtime_snapshot_path = tmp_path / '.runtime_snapshot.json'
    runtime_snapshot_path.write_text(json.dumps({'campaign': {'campaign_key': key}, 'plan': {'generated': 9}, 'latest_run': {'target': 'https://example.com/'}}), encoding='utf-8')

    state = {
        'selected_campaign_key': key,
        'selected_campaign_name': 'Delete Me',
        'state': 'running',
        'pid': '1234',
        'planner_scope_targets': 17,
        'prepared_attacks': 40,
        'runtime_plan_ok': True,
        'runtime_plan_error_preview': '-',
    }
    runtime = {'runtime_plan': {'campaign_key': key}, 'snapshot': {'campaign': {'campaign_key': key}, 'plan': {'generated': 9}, 'latest_run': {'target': 'https://example.com/'}}}
    campaign_store = {'global': {'max_runs': 300}, 'by_campaign': {key: {'aggression_override': 9}}}
    planner_ui = {'selected_campaign_key': key, 'scope_txt': 'scope/scope.txt'}
    orchestrator_state: dict = {}
    client = _build_client(
        state=state,
        runtime=runtime,
        campaign_store=campaign_store,
        planner_ui=planner_ui,
        orchestrator_state=orchestrator_state,
        runtime_plan_meta_path=runtime_plan_meta_path,
        runtime_plan_delete_paths=[runtime_plan_path, legacy_plan_path],
        planner_registry_root=registry_root,
        runtime_snapshot_path=runtime_snapshot_path,
    )

    res = client.post('/api/campaign/delete-current')
    assert res.status_code == 200
    payload = res.get_json()
    assert payload['ok'] is True
    assert payload['deleted_campaign_key'] == key
    assert payload['deleted_registry'] is True
    assert payload['deleted_runtime_plan'] is True
    assert payload['deleted_runtime_meta'] is True
    assert not (registry_root / key).exists()
    assert not runtime_plan_path.exists()
    assert not legacy_plan_path.exists()
    assert not runtime_plan_meta_path.exists()
    snapshot = json.loads(runtime_snapshot_path.read_text(encoding='utf-8'))
    assert snapshot['campaign'] == {}
    assert snapshot['plan'] == {}
    assert snapshot['latest_run'] == {}
    assert campaign_store['global']['max_runs'] == 300
    assert key not in campaign_store.get('by_campaign', {})
    assert planner_ui['selected_campaign_key'] == ''
    assert orchestrator_state['selected_campaign_key'] == ''
    assert state['selected_campaign_key'] == ''
    assert state['selected_campaign_name'] == '-'
    assert state['state'] == 'idle'
    assert state['pid'] == '-'
    assert state['planner_scope_targets'] == 0
    assert state['prepared_attacks'] == 0
    assert state['runtime_plan_ok'] is False


def test_campaign_info_and_planner_info_prefer_current_runtime_plan_when_snapshot_belongs_to_other_campaign(tmp_path: Path) -> None:
    state = {
        'selected_campaign_key': 'camp-current',
        'selected_campaign_name': 'Current Campaign',
        'state': 'idle',
        'pid': '-',
        'runtime_plan_error_preview': '-',
        'aggression_effective': 3,
    }
    runtime = {
        'runtime_plan': {
            'campaign_key': 'camp-current',
            'generated': 40,
            'prepared_attacks': 40,
            'target_count': 17,
            'input_total': 17,
            'plan_hash': 'newhash1234567890',
            'plan_revision': 7,
            'generated_at': '2026-04-02T15:20:19+00:00',
        },
        'snapshot': {
            'campaign': {'campaign_key': 'camp-old', 'executed': 1, 'started_at': '2026-03-27T17:58:28+00:00'},
            'plan': {'generated': 10, 'prepared_attacks': 10, 'target_count': 3, 'input_total': 3, 'plan_hash': 'oldhash', 'plan_revision': 2},
            'latest_run': {'target': 'https://old.example/', 'mode': 'runtime'},
        },
    }
    campaign_store = {'global': {'max_runs': 300}}
    planner_ui = {'selected_campaign_key': 'camp-current', 'scope_txt': 'scope/scope.txt', 'llm_interpret': False}
    orchestrator_state: dict = {}
    client = _build_client(
        state=state,
        runtime=runtime,
        campaign_store=campaign_store,
        planner_ui=planner_ui,
        orchestrator_state=orchestrator_state,
        runtime_plan_meta_path=tmp_path / '.runtime_plan.meta.json',
        runtime_plan_delete_paths=[tmp_path / 'state' / 'public_targets_plan.json'],
        planner_registry_root=tmp_path / 'campaign_registry',
        runtime_snapshot_path=tmp_path / '.runtime_snapshot.json',
    )

    campaign_info = client.get('/api/campaign-info')
    assert campaign_info.status_code == 200
    campaign_payload = campaign_info.get_json()
    assert campaign_payload['planner_scope_targets'] == 17
    assert campaign_payload['prepared_attacks'] == 40
    assert campaign_payload['blueprint_hash'] == 'newhash123456789'
    assert campaign_payload['started_at'] == '2026-04-02T15:20:19+00:00'
    assert campaign_payload['current_target'] == '-'
    assert campaign_payload['runtime_plan_ok'] is True
