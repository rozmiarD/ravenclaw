from __future__ import annotations

from typing import Callable, Any


def build_post_run_action_inputs(*, post_run_action_inputs_cls, task: dict, result: dict, qual: dict, classification: str, auditor: str, engine_status: str, success_eval_status: str, summary_text: str, reason_code: str, target: str, objective: str, aggression: int, owner_auth: bool, owner_override: bool, mode: str, retry_counts: dict, retry_limit: int, followup_queue: list, followup_counts: dict, followup_recent: dict, max_followups_per_target: int, scheduled_keys: set, host_weak_count: dict, host_family_owner_gate: dict, confirm_counts: dict, confirm_recent: dict, confirm_total: int, confirm_class_counts: dict, max_confirm_jobs_per_target: int, max_confirm_jobs_total: int, max_confirm_jobs_per_class: int, confirm_job_cooldown_sec: int, quality_telemetry: dict, toggles: dict, promising: bool, signal_contract: dict | None = None, runtime_decision: dict | None = None, enqueue_followup_task_fn: Callable[[dict, bool], None] | None = None, dedup_key_fn: Callable[..., str] | None = None, attack_family_fn: Callable[..., str] | None = None, host_from_target_fn: Callable[..., str] | None = None, next_followup_family_fn: Callable[..., str] | None = None, clamp_aggression_fn: Callable[[int], int] | None = None, capped_aggression_fn: Callable[[str, str, int], int] | None = None, adaptive_aggression_fn: Callable[..., int] | None = None, post_run_decision_fn: Callable[..., dict] | None = None, log_event_fn: Callable[..., None] | None = None):
    task_local = dict(task or {})
    task_local['mode'] = str(mode)
    return post_run_action_inputs_cls(
        task=task_local,
        result=result if isinstance(result, dict) else {},
        qual=qual if isinstance(qual, dict) else {},
        classification=str(classification),
        auditor=str(auditor),
        engine_status=str(engine_status),
        success_eval_status=str(success_eval_status),
        summary_text=str(summary_text),
        reason_code=str(reason_code),
        target=str(target),
        objective=str(objective),
        aggression=int(aggression),
        owner_auth=bool(owner_auth),
        owner_override=bool(owner_override),
        retry_counts=retry_counts,
        retry_limit=int(retry_limit),
        followup_queue=followup_queue,
        followup_counts=followup_counts,
        followup_recent=followup_recent,
        max_followups_per_target=int(max_followups_per_target),
        scheduled_keys=scheduled_keys,
        host_weak_count=host_weak_count,
        host_family_owner_gate=host_family_owner_gate,
        confirm_counts=confirm_counts,
        confirm_recent=confirm_recent,
        confirm_total=int(confirm_total),
        confirm_class_counts=confirm_class_counts,
        max_confirm_jobs_per_target=int(max_confirm_jobs_per_target),
        max_confirm_jobs_total=int(max_confirm_jobs_total),
        max_confirm_jobs_per_class=int(max_confirm_jobs_per_class),
        confirm_job_cooldown_sec=int(confirm_job_cooldown_sec),
        quality_telemetry=quality_telemetry,
        toggles=toggles if isinstance(toggles, dict) else {},
        promising=bool(promising),
        signal_contract=signal_contract if isinstance(signal_contract, dict) else {},
        runtime_decision=runtime_decision,
        dedup_key_fn=dedup_key_fn,
        attack_family_fn=attack_family_fn,
        host_from_target_fn=host_from_target_fn,
        next_followup_family_fn=next_followup_family_fn,
        clamp_aggression_fn=clamp_aggression_fn,
        capped_aggression_fn=capped_aggression_fn,
        adaptive_aggression_fn=adaptive_aggression_fn,
        enqueue_followup_task_fn=enqueue_followup_task_fn or (lambda task, high_priority=False: None),
        post_run_decision_fn=post_run_decision_fn,
        log_event_fn=log_event_fn,
    )


def build_execute_runtime_task_inputs(*, execute_runtime_task_inputs_cls, task_ctx: dict, objective: str, target: str, mode: str, aggression: int, owner_auth: bool, owner_override: bool, plan_name: str | None, run_index: int, last_heartbeat_ts: float, state: Any, execution_deps: Any, host_family_owner_gate: dict, host_cooldown_until: dict, host_code000_streak: dict, host_code000_total: dict, host_403_streak: dict, host_fail_streak: dict, host_fail_count: dict, host_success_count: dict, code000_streak_threshold: int, code000_cooldown_sec: int, code000_session_cap: int, toggles: dict, qualification_mode: str, qualification_promising_threshold: str):
    return execute_runtime_task_inputs_cls(
        task_ctx=task_ctx,
        objective=str(objective),
        target=str(target),
        mode=str(mode),
        aggression=int(aggression),
        owner_auth=bool(owner_auth),
        owner_override=bool(owner_override),
        plan_name=plan_name,
        run_index=int(run_index),
        last_heartbeat_ts=float(last_heartbeat_ts),
        runs_count=len(state.runs),
        followup_queue_len=len(state.followup_queue),
        precision_queue_len=len(state.precision_queue),
        deps=execution_deps,
        host_family_owner_gate=host_family_owner_gate,
        host_cooldown_until=host_cooldown_until,
        host_code000_streak=host_code000_streak,
        host_code000_total=host_code000_total,
        host_403_streak=host_403_streak,
        host_fail_streak=host_fail_streak,
        host_fail_count=host_fail_count,
        host_success_count=host_success_count,
        code000_streak_threshold=int(code000_streak_threshold),
        code000_cooldown_sec=int(code000_cooldown_sec),
        code000_session_cap=int(code000_session_cap),
        runs=state.runs,
        toggles=toggles,
        host_weak_count=state.host_weak_count,
        quality_telemetry=state.quality_telemetry,
        qualification_mode=qualification_mode,
        qualification_promising_threshold=qualification_promising_threshold,
    )


def run_record_and_persist_stage(*, build_record_and_persist_run_inputs_fn: Callable[..., Any], record_and_persist_runtime_run_fn: Callable[..., float], services: Any, state: Any, run_info: dict, last_persist_ts: float, persist_live_summary_fn: Callable[[], None], update_learning_fn: Callable[..., None], save_host_state_fn: Callable[..., None], attack_family_fn: Callable[[str, str, str], str]) -> float:
    persist_inputs = build_record_and_persist_run_inputs_fn(
        services=services,
        state=state,
        run_info=run_info,
        last_persist_ts=last_persist_ts,
        persist_live_summary_fn=persist_live_summary_fn,
        update_learning_fn=update_learning_fn,
        save_host_state_fn=save_host_state_fn,
        attack_family_fn=attack_family_fn,
    )
    return record_and_persist_runtime_run_fn(**vars(persist_inputs))
