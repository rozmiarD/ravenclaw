from __future__ import annotations

import copy
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Protocol, Tuple


StateMeta = Dict[str, Any]


class GovStateStore(Protocol):
    """Port for state persistence supplied by a host application."""

    def read_json(self, key: str) -> dict[str, Any]:
        ...

    def write_json(self, key: str, value: dict[str, Any]) -> None:
        ...


def atomic_write_text(path: Path, content: str, *, encoding: str = 'utf-8') -> None:
    """Atomically write text without depending on Ravenclaw engine helpers."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f'.{path.name}.', suffix='.tmp', dir=str(path.parent))
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, 'w', encoding=encoding) as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                pass


def atomic_write_json(path: Path, data: Any, *, ensure_ascii: bool = False, indent: int = 2, sort_keys: bool = False) -> None:
    atomic_write_text(
        Path(path),
        json.dumps(data, ensure_ascii=ensure_ascii, indent=indent, sort_keys=sort_keys),
    )


def _clone_default(default: Any) -> Any:
    return copy.deepcopy(default)


def safe_load_json(
    path: Path,
    default: Any,
    *,
    normalizer: Callable[[Any], Any] | None = None,
    description: str = 'json_state',
) -> Tuple[Any, StateMeta]:
    p = Path(path)
    if not p.exists():
        return _clone_default(default), {'status': 'missing', 'path': str(p), 'description': description}
    try:
        raw = json.loads(p.read_text(encoding='utf-8'))
    except Exception as exc:
        return _clone_default(default), {
            'status': 'invalid_json',
            'path': str(p),
            'description': description,
            'error': str(exc),
        }
    if normalizer is None:
        return raw, {'status': 'ok', 'path': str(p), 'description': description}
    try:
        normalized = normalizer(raw)
        return normalized, {'status': 'ok', 'path': str(p), 'description': description}
    except Exception as exc:
        return _clone_default(default), {
            'status': 'invalid_shape',
            'path': str(p),
            'description': description,
            'error': str(exc),
        }


def safe_load_json_object(
    path: Path,
    default: Dict[str, Any] | None = None,
    *,
    normalizer: Callable[[Any], Dict[str, Any]] | None = None,
    description: str = 'json_object_state',
) -> Tuple[Dict[str, Any], StateMeta]:
    base = dict(default or {})
    return safe_load_json(path, base, normalizer=normalizer, description=description)


def safe_load_json_list(
    path: Path,
    default: List[Any] | None = None,
    *,
    normalizer: Callable[[Any], List[Any]] | None = None,
    description: str = 'json_list_state',
) -> Tuple[List[Any], StateMeta]:
    base = list(default or [])
    return safe_load_json(path, base, normalizer=normalizer, description=description)
