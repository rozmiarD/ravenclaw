from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass
class RuntimePrepareDeps:
    precheck_and_prepare_task_fn: Callable[..., dict]
    prepare_curated_task_fn: Callable[..., dict | None]
    prepare_runtime_task_fn: Callable[..., dict | None]
    build_execute_runtime_request_fn: Callable[..., dict] | None = None
