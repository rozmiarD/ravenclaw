from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Callable


def load_planner_ui_state(*, planner_ui_state_path: Path) -> Dict[str, object]:
    if not planner_ui_state_path.exists():
        return {}
    try:
        data = json.loads(planner_ui_state_path.read_text(encoding='utf-8'))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_planner_ui_state(data: Dict[str, object], *, reports_dir: Path, planner_ui_state_path: Path) -> None:
    reports_dir.mkdir(parents=True, exist_ok=True)
    planner_ui_state_path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding='utf-8')


def resolve_selected_campaign_key(*, state_selected_key: str | None = None, load_planner_ui_state_fn: Callable[[], Dict[str, object]]) -> str:
    key = str(state_selected_key or '').strip()
    if key:
        return key
    ui = load_planner_ui_state_fn()
    return str(ui.get('selected_campaign_key') or '').strip()


def resolve_runtime_campaign_key(*, selected_key: str | None = None, runtime_plan_meta: Dict[str, Any] | None = None, load_runtime_plan_meta_fn: Callable[[], Dict[str, Any]], resolve_selected_campaign_key_fn: Callable[[str | None], str]) -> str:
    key = str(selected_key or '').strip()
    if key:
        return key
    meta = runtime_plan_meta if isinstance(runtime_plan_meta, dict) else load_runtime_plan_meta_fn()
    key = str((meta or {}).get('campaign_key') or '').strip()
    if key:
        return key
    return resolve_selected_campaign_key_fn('')
