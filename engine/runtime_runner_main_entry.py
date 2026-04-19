from __future__ import annotations

import json
from typing import Callable


def run_main_entry(*, build_runtime_session_state_fn: Callable[[], tuple], log_event_fn: Callable[..., None], build_main_session_setup_fn: Callable[..., object], build_main_skip_summary_flushers_fn: Callable[..., dict], build_main_runtime_callbacks_fn: Callable[..., dict], build_main_post_run_actions_callback_fn: Callable[..., Callable[..., tuple[int, dict]]], build_main_precheck_hooks_fn: Callable[..., dict], build_runtime_precheck_context_inputs_fn: Callable[..., object], build_main_prepare_callbacks_fn: Callable[..., dict], build_main_planner_callbacks_fn: Callable[..., dict], build_runtime_persist_services_fn: Callable[..., object], build_main_persist_callbacks_fn: Callable[..., dict], build_runtime_session_bundle_inputs_fn: Callable[..., object], build_runtime_session_bundles_fn: Callable[..., object], build_main_execute_runtime_task_callback_fn: Callable[..., Callable[..., tuple[float, int]]], run_main_execution_stage_fn: Callable[..., None], project_runtime_decision_to_run_info_fn: Callable[..., dict], maybe_reconsult_planner_fn: Callable[..., None], summarize_planner_feedback_fn: Callable[..., dict], build_execute_runtime_request_fn: Callable[..., dict], persist_recorded_run_fn: Callable[..., float], log_operation_fn: Callable[..., None], is_sensitive_host_fn: Callable[[str], bool], host_warmup_complete_fn: Callable[[dict, str], bool]):
    campaign_validation, state, run_started, max_runs, target_load_limit, time_budget_min, retry_policy, retry_limit = build_runtime_session_state_fn()
    if not campaign_validation.get('ok'):
        log_event_fn(
            'AUTO_CAMPAIGN',
            'campaign_validation',
            'failed',
            f"invalid campaign config: {campaign_validation.get('errors', [])[:2]}",
            actor='auto_campaign',
            row_type='service',
            highlight=True,
        )
        print(json.dumps({'error': 'invalid_campaign_configuration', 'campaign_validation': campaign_validation}, ensure_ascii=False, indent=2))
        return

    setup = build_main_session_setup_fn(state)
    flushers = build_main_skip_summary_flushers_fn(
        precheck_skip_count_ref=setup.precheck_skip_count_ref,
        precheck_skip_examples=setup.precheck_skip_examples,
        dns_skip_count=setup.dns_skip_count,
        host_cooldown_skip_count=setup.host_cooldown_skip_count,
        execution_gate_skip_count=setup.execution_gate_skip_count,
        execution_gate_skip_examples=setup.execution_gate_skip_examples,
    )
    runtime_callbacks = build_main_runtime_callbacks_fn(
        campaign_validation=campaign_validation,
        run_started=run_started,
        max_runs=max_runs,
        time_budget_min=time_budget_min,
        retry_policy=retry_policy,
        runs=setup.runs,
        followup_queue=setup.followup_queue,
        precision_queue=setup.precision_queue,
        precheck_skip_count_ref=setup.precheck_skip_count_ref,
        dns_skip_count=setup.dns_skip_count,
        host_cooldown_skip_count=setup.host_cooldown_skip_count,
        execution_gate_skip_count=setup.execution_gate_skip_count,
        quality_telemetry=setup.quality_telemetry,
        host_state=setup.host_state,
        queue_coordinator=setup.queue_coordinator,
    )
    apply_post_run_actions = build_main_post_run_actions_callback_fn(
        retry_counts=setup.retry_counts,
        retry_limit=retry_limit,
        followup_queue=setup.followup_queue,
        followup_counts=setup.followup_counts,
        followup_recent=setup.followup_recent,
        max_followups_per_target=setup.max_followups_per_target,
        scheduled_keys=setup.scheduled_keys,
        host_weak_count=setup.host_weak_count,
        host_family_owner_gate=setup.host_family_owner_gate,
        confirm_counts=setup.confirm_counts,
        confirm_recent=setup.confirm_recent,
        confirm_class_counts=setup.confirm_class_counts,
        max_confirm_jobs_per_target=setup.max_confirm_jobs_per_target,
        max_confirm_jobs_total=setup.max_confirm_jobs_total,
        max_confirm_jobs_per_class=setup.max_confirm_jobs_per_class,
        confirm_job_cooldown_sec=setup.confirm_job_cooldown_sec,
        quality_telemetry=setup.quality_telemetry,
        toggles=setup.toggles,
        enqueue_followup_task_fn=runtime_callbacks['enqueue_followup_task'],
    )
    precheck_hooks = build_main_precheck_hooks_fn(
        precheck_skip_count_ref=setup.precheck_skip_count_ref,
        flush_precheck_summary_fn=flushers['flush_precheck_summary'],
        flush_dns_skip_summary_fn=flushers['flush_dns_skip_summary'],
        flush_host_cooldown_summary_fn=flushers['flush_host_cooldown_summary'],
        flush_execution_gate_summary_fn=flushers['flush_execution_gate_summary'],
    )
    precheck_ctx = build_runtime_precheck_context_inputs_fn(
        unresolved_hosts=setup.unresolved_hosts,
        dns_skip_count=setup.dns_skip_count,
        host_dns_cache=setup.host_dns_cache,
        host_cooldown_until=setup.host_cooldown_until,
        host_cooldown_skip_count=setup.host_cooldown_skip_count,
        autodiscover_deep_skip=setup.autodiscover_deep_skip,
        executed_keys=setup.executed_keys,
        precheck_skip_examples=setup.precheck_skip_examples,
        host_precheck_burst=setup.host_precheck_burst,
        host_state=setup.host_state,
        deep_budget=setup.deep_budget,
        host_fail_streak=setup.host_fail_streak,
        host_success_count=setup.host_success_count,
        host_fail_count=setup.host_fail_count,
        gate_skip_count=setup.execution_gate_skip_count,
        gate_skip_examples=setup.execution_gate_skip_examples,
        increment_precheck_skip_fn=precheck_hooks['inc_precheck_skip'],
        on_executed_key_fn=precheck_hooks['on_executed_key'],
        is_sensitive_host_fn=is_sensitive_host_fn,
        host_warmup_complete_fn=host_warmup_complete_fn,
        host_health_cooldown_sec=int(setup.toggles.get('host_health_cooldown_sec', 900) or 900),
        deep_budget_cap_per_host_family=int(setup.toggles.get('deep_budget_cap_per_host_family', 2) or 2),
        precheck_burst_cooldown_threshold=int(setup.toggles.get('precheck_burst_cooldown_threshold', 10) or 10),
        precheck_burst_cooldown_sec=int(setup.toggles.get('precheck_burst_cooldown_sec', 300) or 300),
        host_fail_streak_backoff_step_sec=float(setup.toggles.get('host_fail_streak_backoff_step_sec', 0.4) if setup.toggles.get('host_fail_streak_backoff_step_sec', 0.4) is not None else 0.4),
        host_fail_streak_backoff_cap_sec=float(setup.toggles.get('host_fail_streak_backoff_cap_sec', 2.0) if setup.toggles.get('host_fail_streak_backoff_cap_sec', 2.0) is not None else 2.0),
    )
    prepare_callbacks = build_main_prepare_callbacks_fn(
        precheck_ctx=precheck_ctx,
        scheduled_keys=setup.scheduled_keys,
        toggles=setup.toggles,
        state=state,
        planner_hints_cache_ref=setup.planner_hints_cache_ref,
    )
    planner_callbacks = build_main_planner_callbacks_fn(
        state=state,
        toggles=setup.toggles,
        runs=setup.runs,
        followup_queue=setup.followup_queue,
        precision_queue=setup.precision_queue,
        planner_hints_cache_ref=setup.planner_hints_cache_ref,
        last_regen_run_index_ref=setup.last_regen_run_index_ref,
        curated_plan_ref=setup.curated_plan_ref,
        active_plan_revision_ref=setup.active_plan_revision_ref,
        active_plan_hash_ref=setup.active_plan_hash_ref,
        reprioritize_queues_fn=prepare_callbacks['reprioritize_queues'],
    )
    persist_services = build_runtime_persist_services_fn(
        reprioritize_queues_fn=prepare_callbacks['reprioritize_queues'],
        persist_recorded_run_fn=persist_recorded_run_fn,
        maybe_trigger_plan_regeneration_fn=planner_callbacks['maybe_trigger_plan_regeneration'],
    )
    persist_callbacks = build_main_persist_callbacks_fn(
        persist_services=persist_services,
        state=state,
        last_persist_ts_ref=setup.last_persist_ts_ref,
        persist_live_summary_fn=runtime_callbacks['persist_live_summary'],
    )
    bundle_inputs = build_runtime_session_bundle_inputs_fn(
        apply_post_run_actions_fn=apply_post_run_actions,
        project_runtime_decision_to_run_info_fn=project_runtime_decision_to_run_info_fn,
        maybe_reconsult_planner_fn=lambda toggles, runs, promising_count, host_state=None: maybe_reconsult_planner_fn(
            toggles,
            runs,
            promising_count,
            host_state,
            summarize_planner_feedback_fn=summarize_planner_feedback_fn,
        ),
        refresh_planner_hints_and_reprioritize_fn=planner_callbacks['refresh_planner_hints_and_reprioritize'],
        prepare_task_precheck_fn=prepare_callbacks['prepare_task_precheck'],
        prepare_curated_task_fn=prepare_callbacks['prepare_curated_task'],
        prepare_runtime_task_fn=prepare_callbacks['prepare_runtime_task'],
        build_execute_runtime_request_fn=build_execute_runtime_request_fn,
        reprioritize_queues_fn=prepare_callbacks['reprioritize_queues'],
        persist_recorded_run_fn=persist_recorded_run_fn,
        apply_runtime_adaptation_fn=persist_callbacks['apply_recorded_runtime_adaptation'],
        qualification_mode=setup.qualification_mode,
        qualification_promising_threshold=setup.qualification_promising_threshold,
    )
    bundles = build_runtime_session_bundles_fn(**vars(bundle_inputs))
    execute_runtime_task = build_main_execute_runtime_task_callback_fn(
        state=state,
        execution_deps=bundles.execution_deps,
        runner_deps=bundles.runner_deps,
        record_and_persist_run_fn=persist_callbacks['record_and_persist_run'],
        toggles=setup.toggles,
        host_family_owner_gate=setup.host_family_owner_gate,
        host_cooldown_until=setup.host_cooldown_until,
        host_code000_streak=setup.host_code000_streak,
        host_code000_total=setup.host_code000_total,
        host_403_streak=setup.host_403_streak,
        host_fail_streak=setup.host_fail_streak,
        host_fail_count=setup.host_fail_count,
        host_success_count=setup.host_success_count,
        code000_streak_threshold=setup.code000_streak_threshold,
        code000_cooldown_sec=setup.code000_cooldown_sec,
        code000_session_cap=setup.code000_session_cap,
        qualification_mode=setup.qualification_mode,
        qualification_promising_threshold=setup.qualification_promising_threshold,
    )
    run_main_execution_stage_fn(
        state=state,
        campaign_validation=campaign_validation,
        run_started=run_started,
        max_runs=max_runs,
        target_load_limit=target_load_limit,
        time_budget_min=time_budget_min,
        retry_policy=retry_policy,
        toggles=setup.toggles,
        queue_coordinator=setup.queue_coordinator,
        prepare_deps=bundles.prepare_deps,
        quality_telemetry=setup.quality_telemetry,
        execute_runtime_task_fn=execute_runtime_task,
        maybe_trigger_plan_regeneration_fn=planner_callbacks['maybe_trigger_plan_regeneration'],
        reconcile_active_plan_if_needed_fn=planner_callbacks['reconcile_active_plan_if_needed'],
        persist_live_summary_fn=runtime_callbacks['persist_live_summary'],
        flush_precheck_summary_fn=flushers['flush_precheck_summary'],
        flush_dns_skip_summary_fn=flushers['flush_dns_skip_summary'],
        flush_host_cooldown_summary_fn=flushers['flush_host_cooldown_summary'],
        flush_execution_gate_summary_fn=flushers['flush_execution_gate_summary'],
        log_operation_fn=log_operation_fn,
    )
