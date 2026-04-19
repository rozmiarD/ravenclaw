from __future__ import annotations

from typing import Callable


def build_main_post_run_actions_callback(*, build_main_post_run_actions_callback_fn: Callable[..., Callable[..., tuple[int, dict]]], handle_post_run_actions_fn: Callable[..., tuple[int, dict]], retry_counts: dict, retry_limit: int, followup_queue: list, followup_counts: dict, followup_recent: dict, max_followups_per_target: int, scheduled_keys: set, host_weak_count: dict, host_family_owner_gate: dict, confirm_counts: dict, confirm_recent: dict, confirm_class_counts: dict, max_confirm_jobs_per_target: int, max_confirm_jobs_total: int, max_confirm_jobs_per_class: int, confirm_job_cooldown_sec: int, quality_telemetry: dict, toggles: dict, enqueue_followup_task_fn: Callable[[dict, bool], None]) -> Callable[..., tuple[int, dict]]:
    return build_main_post_run_actions_callback_fn(
        handle_post_run_actions_fn=handle_post_run_actions_fn,
        retry_counts=retry_counts,
        retry_limit=retry_limit,
        followup_queue=followup_queue,
        followup_counts=followup_counts,
        followup_recent=followup_recent,
        max_followups_per_target=max_followups_per_target,
        scheduled_keys=scheduled_keys,
        host_weak_count=host_weak_count,
        host_family_owner_gate=host_family_owner_gate,
        confirm_counts=confirm_counts,
        confirm_recent=confirm_recent,
        confirm_class_counts=confirm_class_counts,
        max_confirm_jobs_per_target=max_confirm_jobs_per_target,
        max_confirm_jobs_total=max_confirm_jobs_total,
        max_confirm_jobs_per_class=max_confirm_jobs_per_class,
        confirm_job_cooldown_sec=confirm_job_cooldown_sec,
        quality_telemetry=quality_telemetry,
        toggles=toggles,
        enqueue_followup_task_fn=enqueue_followup_task_fn,
    )
