from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class RuntimeRunnerDeps:
    apply_post_run_actions_fn: Callable[..., tuple[int, dict]]
    project_runtime_decision_to_run_info_fn: Callable[..., dict]
    maybe_reconsult_planner_fn: Callable[..., str | None]
    refresh_planner_hints_and_reprioritize_fn: Callable[[str, str], None]
    precheck_and_prepare_task_fn: Callable[..., dict]
    prepare_curated_task_fn: Callable[..., dict | None]
    prepare_runtime_task_fn: Callable[..., dict | None]
    reprioritize_queues_fn: Callable[[], None]
    persist_recorded_run_fn: Callable[..., float]
    apply_runtime_adaptation_fn: Callable[[dict], None]
