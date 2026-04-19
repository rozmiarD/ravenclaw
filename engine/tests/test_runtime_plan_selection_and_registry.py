from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from runtime_plan_blueprint_registry import load_active_campaign_blueprint, load_campaign_blueprint_for_key  # type: ignore
from runtime_plan_selection import load_planner_ui_state, resolve_runtime_campaign_key, resolve_selected_campaign_key, save_planner_ui_state  # type: ignore


def test_planner_ui_state_roundtrip(tmp_path: Path) -> None:
    reports_dir = tmp_path / 'reports'
    state_path = reports_dir / '.planner.ui.state.json'
    save_planner_ui_state({'selected_campaign_key': 'camp-x'}, reports_dir=reports_dir, planner_ui_state_path=state_path)
    assert load_planner_ui_state(planner_ui_state_path=state_path) == {'selected_campaign_key': 'camp-x'}


def test_selection_resolution_prefers_explicit_then_meta_then_ui() -> None:
    assert resolve_selected_campaign_key(state_selected_key='camp-explicit', load_planner_ui_state_fn=lambda: {'selected_campaign_key': 'camp-ui'}) == 'camp-explicit'
    assert resolve_selected_campaign_key(state_selected_key='', load_planner_ui_state_fn=lambda: {'selected_campaign_key': 'camp-ui'}) == 'camp-ui'
    assert resolve_runtime_campaign_key(selected_key='camp-explicit', runtime_plan_meta={'campaign_key': 'camp-meta'}, load_runtime_plan_meta_fn=lambda: {'campaign_key': 'camp-meta'}, resolve_selected_campaign_key_fn=lambda _x: 'camp-ui') == 'camp-explicit'
    assert resolve_runtime_campaign_key(selected_key='', runtime_plan_meta={'campaign_key': 'camp-meta'}, load_runtime_plan_meta_fn=lambda: {}, resolve_selected_campaign_key_fn=lambda _x: 'camp-ui') == 'camp-meta'
    assert resolve_runtime_campaign_key(selected_key='', runtime_plan_meta=None, load_runtime_plan_meta_fn=lambda: {}, resolve_selected_campaign_key_fn=lambda _x: 'camp-ui') == 'camp-ui'


def test_blueprint_registry_helpers_resolve_relative_latest_path(tmp_path: Path) -> None:
    registry_root = tmp_path / 'campaign_registry'
    key = 'camp1'
    campaign_dir = registry_root / key
    version_dir = campaign_dir / 'versions' / 'v0001'
    version_dir.mkdir(parents=True)
    (campaign_dir / 'latest.json').write_text('{"path": "versions/v0001"}', encoding='utf-8')
    (version_dir / 'blueprint.json').write_text('{"structured_scope": {"domains": ["api.example.com"]}}', encoding='utf-8')

    resolved_version_dir, bp_path, bp = load_campaign_blueprint_for_key(key, planner_registry_root=registry_root)
    assert resolved_version_dir == version_dir
    assert bp_path == version_dir / 'blueprint.json'
    assert bp['structured_scope']['domains'] == ['api.example.com']

    active_key, active_version_dir, active_bp_path, active_bp = load_active_campaign_blueprint(
        selected_key='camp1',
        runtime_plan_meta={'campaign_key': 'other'},
        resolve_runtime_campaign_key_fn=lambda selected_key, runtime_plan_meta: str(selected_key or runtime_plan_meta.get('campaign_key') or ''),
        load_campaign_blueprint_for_key_fn=lambda key: load_campaign_blueprint_for_key(key, planner_registry_root=registry_root),
    )
    assert active_key == 'camp1'
    assert active_version_dir == version_dir
    assert active_bp_path == version_dir / 'blueprint.json'
    assert active_bp['structured_scope']['domains'] == ['api.example.com']
