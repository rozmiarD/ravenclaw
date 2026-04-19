from __future__ import annotations

import json
import sys
from pathlib import Path

from flask import Flask

ROOT = Path(__file__).resolve().parents[1] / 'logdash'
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api_planner import register_planner_api  # type: ignore
from services import build_selected_campaign_projection, projection_source_label, selected_runtime_snapshot_view  # type: ignore


def _build_planner_client(tmp_path: Path, runtime: dict, runtime_plan_meta: dict | None = None) -> Flask:
    app = Flask(__name__)
    runtime_plan_path = tmp_path / 'reports' / 'state' / 'public_targets_plan.json'
    runtime_plan_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_plan_path.write_text('[]', encoding='utf-8')
    runtime_plan_meta_path = tmp_path / 'reports' / '.runtime_plan.meta.json'
    runtime_plan_meta_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_plan_meta_path.write_text(json.dumps(runtime_plan_meta or {}), encoding='utf-8')

    register_planner_api(
        app,
        {
            'STATE': {'selected_campaign_key': 'camp-current', 'planner_scope_targets': 17, 'prepared_attacks': 40},
            'selected_campaign_key': lambda: 'camp-current',
            'load_campaign_blueprint_for_key': lambda key: (None, None, None),
            'runtime_plan_entries_from_blueprint': lambda bp: [],
            'write_runtime_plan': lambda entries, key, reason='manual_or_ui': {'ok': True, 'target_count': len(entries)},
            'load_runtime_plan_meta': lambda: dict(runtime_plan_meta or {}),
            'load_runtime_state': lambda: runtime,
            'load_runtime_snapshot': lambda: (runtime.get('snapshot') if isinstance(runtime.get('snapshot'), dict) else {}),
            'selected_runtime_snapshot_view': lambda runtime=None, selected_key=None: selected_runtime_snapshot_view(runtime, str(selected_key if selected_key is not None else 'camp-current')),
            'build_selected_campaign_projection': build_selected_campaign_projection,
            'projection_source_label': projection_source_label,
            'load_planner_ui_state': lambda: {'scope_txt': 'scope/scope.txt', 'llm_interpret': False, 'selected_campaign_key': 'camp-current'},
            'load_latest_blueprint': lambda: None,
            '_list_campaign_registry_items': lambda: [],
            'save_planner_ui_state': lambda data: None,
            'activate_campaign_key': lambda key: {'ok': True},
            'RUNTIME_PLAN_PATH': runtime_plan_path,
            'ENGINE_DIR': tmp_path / 'engine',
            'WORKSPACE_DIR': tmp_path,
            'SCOPE_DIR': tmp_path / 'scope',
            'BUDGETS_PATH': tmp_path / 'budgets.yaml',
            'PLAN_CAMPAIGN_SCRIPT': tmp_path / 'engine' / 'plan_campaign.py',
            'PLANNER_REGISTRY_ROOT': tmp_path / 'reports' / 'campaign_registry',
        },
    )
    app.testing = True
    return app.test_client()


def test_planner_info_prefers_current_runtime_plan_when_snapshot_belongs_to_other_campaign(tmp_path: Path) -> None:
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
        },
    }
    client = _build_planner_client(tmp_path, runtime, runtime_plan_meta=runtime['runtime_plan'])

    payload = client.get('/api/planner-info').get_json()

    assert payload['runtime_snapshot_source'] == 'legacy'
    assert payload['plan_revision'] == 0
    assert payload['prepared_attacks'] == 40
    assert payload['planner_scope_targets'] == 17
    assert payload['campaign_started_at'] == ''


def test_runtime_plan_view_ignores_mismatched_snapshot_plan_meta(tmp_path: Path) -> None:
    runtime = {
        'runtime_plan': {
            'campaign_key': 'camp-current',
            'generated': 40,
            'prepared_attacks': 40,
            'target_count': 17,
            'input_total': 17,
            'plan_hash': 'newhash1234567890',
            'plan_revision': 7,
        },
        'snapshot': {
            'campaign': {'campaign_key': 'camp-old'},
            'plan': {'generated': 10, 'target_count': 3, 'plan_hash': 'oldhash', 'plan_revision': 2},
        },
    }
    runtime_meta = {'campaign_key': 'camp-current', 'generated': 40, 'target_count': 17, 'plan_hash': 'newhash1234567890', 'plan_revision': 7}
    client = _build_planner_client(tmp_path, runtime, runtime_plan_meta=runtime_meta)

    payload = client.get('/api/planner/runtime-plan-view').get_json()

    assert payload['meta']['source'] == 'normalized_runtime_plan_meta'
    assert payload['meta']['plan_revision'] == 7
    assert payload['meta']['plan_hash'] == 'newhash1234567890'
    assert payload['meta']['target_count'] == 17


def test_planner_info_reports_blueprint_source_for_invalid_blueprint_json(tmp_path: Path) -> None:
    runtime = {
        'runtime_plan': {'campaign_key': 'camp-current', 'generated': 1, 'target_count': 1},
        'snapshot': {},
    }
    app = Flask(__name__)
    runtime_plan_path = tmp_path / 'reports' / 'state' / 'public_targets_plan.json'
    runtime_plan_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_plan_path.write_text('[]', encoding='utf-8')
    version_dir = tmp_path / 'reports' / 'campaign_registry' / 'camp-current' / 'v1'
    version_dir.mkdir(parents=True, exist_ok=True)
    (version_dir / 'blueprint.json').write_text('{bad json', encoding='utf-8')

    register_planner_api(
        app,
        {
            'STATE': {'selected_campaign_key': 'camp-current', 'planner_scope_targets': 1, 'prepared_attacks': 1},
            'selected_campaign_key': lambda: 'camp-current',
            'load_campaign_blueprint_for_key': lambda key: (None, None, None),
            'runtime_plan_entries_from_blueprint': lambda bp: [],
            'write_runtime_plan': lambda entries, key, reason='manual_or_ui': {'ok': True, 'target_count': len(entries)},
            'load_runtime_plan_meta': lambda: {'campaign_key': 'camp-current'},
            'load_runtime_state': lambda: runtime,
            'load_runtime_snapshot': lambda: {},
            'selected_runtime_snapshot_view': lambda runtime=None, selected_key=None: selected_runtime_snapshot_view(runtime, str(selected_key if selected_key is not None else 'camp-current')),
            'build_selected_campaign_projection': build_selected_campaign_projection,
            'projection_source_label': projection_source_label,
            'load_planner_ui_state': lambda: {'scope_txt': 'scope/scope.txt', 'llm_interpret': False, 'selected_campaign_key': 'camp-current'},
            'load_latest_blueprint': lambda: {'path': str(version_dir)},
            '_list_campaign_registry_items': lambda: [],
            'save_planner_ui_state': lambda data: None,
            'activate_campaign_key': lambda key: {'ok': True},
            'RUNTIME_PLAN_PATH': runtime_plan_path,
            'ENGINE_DIR': tmp_path / 'engine',
            'WORKSPACE_DIR': tmp_path,
            'SCOPE_DIR': tmp_path / 'scope',
            'BUDGETS_PATH': tmp_path / 'budgets.yaml',
            'PLAN_CAMPAIGN_SCRIPT': tmp_path / 'engine' / 'plan_campaign.py',
            'PLANNER_REGISTRY_ROOT': tmp_path / 'reports' / 'campaign_registry',
        },
    )
    app.testing = True
    client = app.test_client()

    payload = client.get('/api/planner-info').get_json()

    assert payload['status'] == 'ok'
    assert payload['blueprint_source'] == 'invalid_json_file'
