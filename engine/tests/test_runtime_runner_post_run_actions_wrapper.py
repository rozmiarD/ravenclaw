from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_runner_post_run_actions_wrapper as rrpraw  # type: ignore


def test_build_main_post_run_actions_callback_delegates() -> None:
    captured = {}

    def fake_build_main_post_run_actions_callback(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return lambda *args, **kwargs2: (0, {})

    out = rrpraw.build_main_post_run_actions_callback(
        build_main_post_run_actions_callback_fn=fake_build_main_post_run_actions_callback,
        handle_post_run_actions_fn=lambda **kwargs: (0, {}),
        retry_counts={},
        retry_limit=1,
        followup_queue=[],
        followup_counts={},
        followup_recent={},
        max_followups_per_target=2,
        scheduled_keys=set(),
        host_weak_count={},
        host_family_owner_gate={},
        confirm_counts={},
        confirm_recent={},
        confirm_class_counts={},
        max_confirm_jobs_per_target=1,
        max_confirm_jobs_total=2,
        max_confirm_jobs_per_class=1,
        confirm_job_cooldown_sec=60,
        quality_telemetry={},
        toggles={},
        enqueue_followup_task_fn=lambda task, high_priority=False: None,
    )
    assert callable(out)
    assert captured['retry_limit'] == 1
