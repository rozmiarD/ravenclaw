from __future__ import annotations

import json
import os
import signal
import sys
from pathlib import Path

import pytest
from flask import Flask

ROOT = Path(__file__).resolve().parents[2]
LOGDASH_DIR = ROOT / 'logdash'
if str(LOGDASH_DIR) not in sys.path:
    sys.path.insert(0, str(LOGDASH_DIR))

import api_supplemental as supplemental  # type: ignore
from api_supplemental import register_supplemental_api  # type: ignore
from services import build_campaign_info_payload, build_runtime_health_payload, selected_runtime_snapshot_view  # type: ignore


class _Proc:
    def __init__(self, pid: int) -> None:
        self.pid = pid


def _build_client(tmp_path: Path, state: dict, runtime: dict):
    app = Flask(__name__)
    planner_ui = {'selected_campaign_key': state.get('selected_campaign_key', '')}

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
        return {'global': {'max_runs': 300}, 'by_campaign': {}}

    def save_campaign_settings(store: dict) -> None:
        return None

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
        planner_ui.clear()
        planner_ui.update(data)

    def load_planner_ui_state() -> dict:
        return planner_ui

    def save_orchestrator_state(data: dict) -> None:
        return None

    runtime_state_path = tmp_path / '.auto_campaign.state.json'
    runtime_pid_path = tmp_path / '.auto_campaign.pid'
    stdout_path = tmp_path / '.auto_campaign.stdout.log'
    stderr_path = tmp_path / '.auto_campaign.stderr.log'

    def write_runtime_state_file(local_state: dict, paused=None):
        current = {}
        if runtime_state_path.exists():
            current = json.loads(runtime_state_path.read_text(encoding='utf-8'))
        if paused is None:
            paused = str(local_state.get('state', 'idle')).lower() == 'paused'
        current['paused'] = bool(paused)
        current['stopped'] = str(local_state.get('state', 'idle')).lower() == 'stopped'
        current['owner_override'] = bool(local_state.get('owner_override', False))
        runtime_state_path.write_text(json.dumps(current), encoding='utf-8')

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
            'RUNTIME_STDOUT_PATH': stdout_path,
            'RUNTIME_STDERR_PATH': stderr_path,
            '_load_owner_approval_actions': _load_owner_approval_actions,
            '_save_owner_approval_actions': _save_owner_approval_actions,
            '_owner_approval_row_ids': _owner_approval_row_ids,
            'fetch_filtered_logs': fetch_filtered_logs,
            'save_planner_ui_state': save_planner_ui_state,
            'load_planner_ui_state': load_planner_ui_state,
            'HOST_STATE_PATH': tmp_path / '.host_state.json',
            'save_orchestrator_state': save_orchestrator_state,
            'RUNTIME_PLAN_META_PATH': tmp_path / '.runtime_plan.meta.json',
            'RUNTIME_PLAN_DELETE_PATHS': [tmp_path / 'state' / 'public_targets_plan.json'],
            'PLANNER_REGISTRY_ROOT': tmp_path / 'campaign_registry',
            'selected_runtime_snapshot_view': lambda runtime=None, selected_key=None: selected_runtime_snapshot_view(runtime, str(selected_key if selected_key is not None else selected_campaign_key())),
            'build_campaign_info_payload': build_campaign_info_payload,
            'build_runtime_health_payload': build_runtime_health_payload,
            'RUNTIME_SNAPSHOT_PATH': tmp_path / '.runtime_snapshot.json',
            'RUNTIME_STATE_PATH': runtime_state_path,
            'RUNTIME_PID_PATH': runtime_pid_path,
            'ENGINE_DIR': ROOT / 'engine',
            'WORKSPACE_DIR': ROOT,
            'PYTHON_BIN': sys.executable,
            'write_runtime_state_file': write_runtime_state_file,
        },
    )
    app.testing = True
    return app.test_client(), runtime_state_path, runtime_pid_path


@pytest.fixture
def fake_process_control(monkeypatch):
    state = {'terminated': False, 'spawned': []}

    def fake_popen(cmd, cwd=None, env=None, stdout=None, stderr=None, start_new_session=None):
        state['spawned'].append({'cmd': cmd, 'cwd': cwd, 'env': env, 'start_new_session': start_new_session})
        return _Proc(4242)

    def fake_kill(pid: int, sig: int):
        if sig == 0:
            if state['terminated']:
                raise OSError('terminated')
            return None
        state['terminated'] = True
        return None

    def fake_killpg(pid: int, sig: int):
        state['terminated'] = True
        return None

    monkeypatch.setattr(supplemental.subprocess, 'Popen', fake_popen)
    monkeypatch.setattr(supplemental.os, 'kill', fake_kill)
    monkeypatch.setattr(supplemental.os, 'killpg', fake_killpg)
    monkeypatch.setattr(supplemental.time, 'sleep', lambda _sec: None)
    return state


def test_campaign_control_start_pause_stop_manipulates_real_runtime_state(tmp_path: Path, fake_process_control) -> None:
    state = {'selected_campaign_key': 'camp-123', 'state': 'idle', 'owner_override': False, 'pid': '-'}
    runtime = {'runtime_plan': {'campaign_key': 'camp-123', 'generated': 4, 'prepared_attacks': 4}}
    client, runtime_state_path, runtime_pid_path = _build_client(tmp_path, state, runtime)

    start = client.post('/api/campaign/control', json={'action': 'start', 'owner_override': True})
    assert start.status_code == 200
    payload = start.get_json()
    assert payload['ok'] is True
    assert payload['started'] is True
    assert payload['selected_campaign_key'] == 'camp-123'
    assert runtime_pid_path.read_text(encoding='utf-8').strip() == '4242'
    control = json.loads(runtime_state_path.read_text(encoding='utf-8'))
    assert control['paused'] is False
    assert control['stopped'] is False
    assert control['owner_override'] is True

    state['pid'] = '4242'
    state['state'] = 'running'
    pause = client.post('/api/campaign/control', json={'action': 'pause', 'owner_override': True})
    assert pause.status_code == 200
    pause_payload = pause.get_json()
    assert pause_payload['paused'] is True
    control = json.loads(runtime_state_path.read_text(encoding='utf-8'))
    assert control['paused'] is True
    assert control['stopped'] is False

    stop = client.post('/api/campaign/control', json={'action': 'stop', 'owner_override': False})
    assert stop.status_code == 200
    stop_payload = stop.get_json()
    assert stop_payload['stopped'] is True
    assert stop_payload['terminated'] is True
    control = json.loads(runtime_state_path.read_text(encoding='utf-8'))
    assert control['paused'] is False
    assert control['stopped'] is True


def test_campaign_control_start_requires_runtime_plan_for_selected_campaign(tmp_path: Path, fake_process_control) -> None:
    state = {'selected_campaign_key': 'camp-123', 'state': 'idle', 'owner_override': False, 'pid': '-'}
    runtime = {'runtime_plan': {'campaign_key': 'other-camp', 'generated': 4}}
    client, _runtime_state_path, _runtime_pid_path = _build_client(tmp_path, state, runtime)

    start = client.post('/api/campaign/control', json={'action': 'start'})
    assert start.status_code == 400
    payload = start.get_json()
    assert payload['ok'] is False
    assert payload['error'] == 'runtime_plan_missing_for_selected_campaign'
