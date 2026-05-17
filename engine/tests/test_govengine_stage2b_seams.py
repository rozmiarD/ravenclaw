from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parents[1]
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

import tool_registry as engine_registry  # type: ignore
from govengine import tool_registry as gov_registry


def test_tool_registry_wrapper_aliases_govengine_module() -> None:
    assert engine_registry is gov_registry
    assert engine_registry.get_tool_catalog is gov_registry.get_tool_catalog
    assert engine_registry.REGISTRY_PATH == gov_registry.REGISTRY_PATH


def test_tool_registry_state_monkeypatch_compatibility(tmp_path: Path, monkeypatch) -> None:
    state_path = tmp_path / '.tool_registry.state.json'
    monkeypatch.setattr(engine_registry, 'TOOL_REGISTRY_STATE_PATH', state_path)

    saved = engine_registry.save_tool_registry_state('extended')
    state = gov_registry.get_active_planner_profile_state()

    assert saved['selected_profile'] == 'extended'
    assert state['active_profile'] == 'extended'
    assert state_path.exists()
