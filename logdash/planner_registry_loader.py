from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

_WORKSPACE_ROOT = Path(os.getenv('RAVENCLAW_WORKSPACE') or Path(__file__).resolve().parents[1]).expanduser().resolve()
ROOT = _WORKSPACE_ROOT / 'engine'
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from json_state_io import safe_load_json_object, safe_load_json_list



def load_json_file(path: Path, *, description: str) -> tuple[dict[str, Any], str]:
    data, meta = safe_load_json_object(
        path,
        {},
        description=description,
    )
    source = 'missing'
    if path.exists():
        source = 'normalized_json_file'
    if isinstance(meta, dict) and meta.get('error'):
        source = 'invalid_json_file'
    return (data if isinstance(data, dict) else {}, source)



def load_json_list_file(path: Path, *, description: str) -> tuple[list[dict[str, Any]], str]:
    def _normalize(raw: Any) -> list[dict[str, Any]]:
        if not isinstance(raw, list):
            raise TypeError('expected list')
        return [item for item in raw if isinstance(item, dict)]

    data, meta = safe_load_json_list(
        path,
        [],
        normalizer=_normalize,
        description=description,
    )
    source = 'missing'
    if path.exists():
        source = 'normalized_json_file'
    if isinstance(meta, dict) and meta.get('status') in {'invalid_json', 'invalid_shape'}:
        source = 'invalid_json_file'
    return data, source



def load_blueprint_json(version_dir: Path | str | None) -> tuple[dict[str, Any], str]:
    path = Path(str(version_dir or '')) / 'blueprint.json'
    return load_json_file(path, description='planner_blueprint')



def load_latest_registry_meta(registry_root: Path, campaign_key: str) -> tuple[dict[str, Any], str]:
    latest = registry_root / campaign_key / 'latest.json'
    return load_json_file(latest, description='planner_registry_latest')
