from __future__ import annotations

from typing import Callable


def build_main_post_run_actions_callback(*, handle_post_run_actions_fn: Callable[..., tuple[int, dict]], retry_counts: dict, retry_limit: int, followup_queue: list, followup_counts: dict, followup_recent: dict, max_followups_per_target: int, scheduled_keys: set, host_weak_count: dict, host_family_owner_gate: dict, confirm_counts: dict, confirm_recent: dict, confirm_class_counts: dict, max_confirm_jobs_per_target: int, max_confirm_jobs_total: int, max_confirm_jobs_per_class: int, confirm_job_cooldown_sec: int, quality_telemetry: dict, toggles: dict, enqueue_followup_task_fn: Callable[[dict, bool], None]) -> Callable[..., tuple[int, dict]]:
    def apply_post_run_actions_cb(task_ctx: dict, result: dict, qual: dict, classification: str, auditor: str, engine_status: str, success_eval_status: str, summary_text: str, reason_code: str, target: str, objective: str, aggression: int, owner_auth: bool, owner_override: bool, mode: str, confirm_total: int, promising: bool, signal_contract: dict | None = None, runtime_decision: dict | None = None) -> tuple[int, dict]:
        return handle_post_run_actions_fn(
            task=task_ctx,
            result=(result if isinstance(result, dict) else {}),
            qual=qual,
            classification=classification,
            auditor=auditor,
            engine_status=engine_status,
            success_eval_status=success_eval_status,
            summary_text=summary_text,
            reason_code=reason_code,
            target=target,
            objective=objective,
            aggression=aggression,
            owner_auth=owner_auth,
            owner_override=owner_override,
            mode=str(mode),
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
            confirm_total=confirm_total,
            confirm_class_counts=confirm_class_counts,
            max_confirm_jobs_per_target=max_confirm_jobs_per_target,
            max_confirm_jobs_total=max_confirm_jobs_total,
            max_confirm_jobs_per_class=max_confirm_jobs_per_class,
            confirm_job_cooldown_sec=confirm_job_cooldown_sec,
            quality_telemetry=quality_telemetry,
            toggles=toggles,
            promising=bool(promising),
            signal_contract=(signal_contract if isinstance(signal_contract, dict) else {}),
            runtime_decision=(runtime_decision if isinstance(runtime_decision, dict) else {}),
            enqueue_followup_task_fn=enqueue_followup_task_fn,
        )

    return apply_post_run_actions_cb
