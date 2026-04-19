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
from services import build_campaign_info_payload, build_runtime_health_payload, selected_runtime_snapshot_view  # type: ignore


def _build_client(*, tmp_path: Path, state: dict, runtime: dict, campaign_store: dict, selected_key: str):
    app = Flask(__name__)
    planner_ui = {'selected_campaign_key': selected_key}
    orchestrator_state = {'selected_campaign_key': selected_key}

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
        return selected_key

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
            'RUNTIME_STDOUT_PATH': tmp_path / '.auto_campaign.stdout.log',
            'RUNTIME_STDERR_PATH': tmp_path / '.auto_campaign.stderr.log',
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
            'RUNTIME_STATE_PATH': tmp_path / '.auto_campaign.state.json',
            'RUNTIME_PID_PATH': tmp_path / '.auto_campaign.pid',
            'ENGINE_DIR': ROOT / 'engine',
            'WORKSPACE_DIR': ROOT,
            'PYTHON_BIN': sys.executable,
            'write_runtime_state_file': write_runtime_state_file,
        },
    )
    app.testing = True
    return app.test_client()


def test_campaign_settings_seed_program_specific_credentials_and_report_ready_status(tmp_path: Path) -> None:
    key = 'camp-cred'
    version_dir = tmp_path / 'campaign_registry' / key / 'versions' / 'v0001'
    version_dir.mkdir(parents=True)
    (tmp_path / 'campaign_registry' / key / 'latest.json').write_text(json.dumps({'path': 'versions/v0001'}), encoding='utf-8')
    (version_dir / 'blueprint.json').write_text(json.dumps({
        'credentials_policy': {
            'credentials_required': True,
            'allow_auth_header': False,
            'allow_cookie_header': True,
            'allow_basic_auth': False,
            'notes': [
                'Use researcher-controlled test accounts and hacker email alias.',
                'Add required header: X-HackerOne-Research: [H1 username].',
            ],
        }
    }), encoding='utf-8')
    state = {'selected_campaign_key': key, 'selected_campaign_name': key, 'state': 'idle', 'pid': '-'}
    runtime = {'runtime_plan': {'campaign_key': key, 'generated': 3, 'prepared_attacks': 3, 'target_count': 2}}
    campaign_store = {
        'global': {
            'credentials_owner_approved': True,
            'bug_bounty_username': '0x505badc0de',
            'test_account_email': '0x505badc0de@proton.me',
            'request_decoration': {'mode': 'operator_supplied', 'headers': [], 'cookies': [], 'basic_auth': {'enabled': False, 'username': '', 'password': '', 'password_ref': ''}, 'provenance_notes': []},
        },
        'by_campaign': {},
    }
    client = _build_client(tmp_path=tmp_path, state=state, runtime=runtime, campaign_store=campaign_store, selected_key=key)

    settings = client.get('/api/campaign/settings')
    assert settings.status_code == 200
    payload = settings.get_json()
    assert payload['credentials_required'] is True
    assert payload['allow_cookie_header'] is True
    assert payload['allow_auth_header'] is False
    assert payload['credentials_status'] == 'READY'
    assert payload['bug_bounty_username'] == '0x505badc0de'
    headers = payload['request_decoration']['headers']
    assert any(h['name'] == 'X-HackerOne-Research' and h['value'] == '0x505badc0de' for h in headers)
    assert any('X-HackerOne-Research' in note for note in payload['request_decoration']['provenance_notes'])

    info = client.get('/api/campaign-info')
    assert info.status_code == 200
    info_payload = info.get_json()
    assert info_payload['credentials_status'] == 'READY'
    assert 'configured for this campaign' in info_payload['credentials_status_detail']
