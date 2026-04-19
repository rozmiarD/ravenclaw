from __future__ import annotations

import sys
from pathlib import Path

from flask import Flask

ROOT = Path(__file__).resolve().parents[1] / 'logdash'
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import api_runtime  # type: ignore
import app as logdash_app  # type: ignore



def test_pipeline_config_loader_tolerates_invalid_json(tmp_path: Path, monkeypatch) -> None:
    cfg = tmp_path / 'pipeline_config.json'
    cfg.write_text('{bad json', encoding='utf-8')
    monkeypatch.setattr(logdash_app, 'PIPELINE_CONFIG_PATH', cfg)

    data = logdash_app.load_pipeline_config()

    assert isinstance(data, dict)



def test_load_agent_models_tolerates_invalid_config(tmp_path: Path, monkeypatch) -> None:
    cfg = tmp_path / 'openclaw.json'
    cfg.write_text('{bad json', encoding='utf-8')
    monkeypatch.setattr(logdash_app, 'OPENCLAW_CONFIG_PATH', cfg)

    assert logdash_app.load_agent_models() == {}



def test_pipeline_config_schema_manifest_tolerates_invalid_json(tmp_path: Path, monkeypatch) -> None:
    engine_dir = tmp_path / 'engine'
    engine_dir.mkdir(parents=True, exist_ok=True)
    (engine_dir / 'feature_flags_manifest.json').write_text('{bad json', encoding='utf-8')
    monkeypatch.setattr(api_runtime, '__file__', str(tmp_path / 'logdash' / 'api_runtime.py'))

    app = Flask(__name__)
    api_runtime.register_runtime_api(
        app,
        {
            'STATE': {},
            'refresh_runtime_state': lambda: None,
            'load_agent_models': lambda: {},
            'selected_campaign_key': lambda: '',
            'load_runtime_state': lambda: {},
            'load_runtime_snapshot': lambda: {},
            'load_pipeline_config': lambda: {},
            'save_pipeline_config': lambda data: data,
            'pipeline_config_meta': lambda: {},
            'selected_runtime_snapshot_view': lambda runtime=None, selected_key=None: {},
            'build_agents_status_payload': lambda **kwargs: {},
            'build_selected_campaign_projection': lambda runtime=None, selected_view=None, state=None: {},
            'load_pipeline_config_effective_posture': lambda: {},
        },
    )
    app.testing = True
    client = app.test_client()

    payload = client.get('/api/pipeline-config/schema').get_json()

    assert payload['manifest'] == {}
