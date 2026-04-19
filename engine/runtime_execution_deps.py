from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class RuntimeExecutionDeps:
    summarize_result_fn: Callable[[dict], tuple[str, str, str, str, bool]]
    post_result_common_fn: Callable[..., dict]
    qualify_and_finalize_run_fn: Callable[..., tuple[dict, bool, dict]]
    inspect_json_signal_from_command_fn: Callable[..., Any]
    parse_rc_metrics_fn: Callable[..., Any]
    run_control_comparison_fn: Callable[..., Any]
    attack_family_fn: Callable[..., Any]
    repeated_consistency_ok_fn: Callable[[list[dict], str, str], bool]
    qualify_fn: Callable[[dict], dict]
    can_be_confirmed_fn: Callable[[dict], bool]
    compute_promising_fn: Callable[[dict, str, str], bool]
    finding_lifecycle_fn: Callable[[str, dict], str]
    adaptive_aggression_fn: Callable[[int, str, str, bool], int]
    normalize_pipeline_status_fn: Callable[[str, str, bool], str]
    log_event_fn: Callable[..., None]
    run_pipeline_fn: Callable[..., dict]
