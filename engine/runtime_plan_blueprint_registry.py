from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable


def load_campaign_blueprint_for_key(key: str, *, planner_registry_root: Path) -> tuple[Path, Path, dict] | tuple[None, None, None]:
    latest = planner_registry_root / str(key).strip() / 'latest.json'
    if not latest.exists():
        return None, None, None
    meta = json.loads(latest.read_text(encoding='utf-8'))
    raw_path = Path(str(meta.get('path') or ''))
    version_dir = raw_path if raw_path.is_absolute() else (latest.parent / raw_path)
    bp_path = version_dir / 'blueprint.json'
    if not bp_path.exists():
        return None, None, None
    bp = json.loads(bp_path.read_text(encoding='utf-8'))
    return version_dir, bp_path, bp


def load_active_campaign_blueprint(*, selected_key: str | None = None, runtime_plan_meta: dict[str, Any] | None = None, resolve_runtime_campaign_key_fn: Callable[[str | None, dict[str, Any] | None], str], load_campaign_blueprint_for_key_fn: Callable[[str], tuple[Path, Path, dict] | tuple[None, None, None]]) -> tuple[str, Path | None, Path | None, dict | None]:
    key = resolve_runtime_campaign_key_fn(selected_key, runtime_plan_meta)
    if not key:
        return '', None, None, None
    version_dir, bp_path, bp = load_campaign_blueprint_for_key_fn(key)
    return key, version_dir, bp_path, bp
