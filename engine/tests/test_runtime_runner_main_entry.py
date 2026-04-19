from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_runner_main_entry as rrme  # type: ignore


def test_run_main_entry_invalid_campaign_prints_error(capsys) -> None:
    events = []
    rrme.run_main_entry(
        build_runtime_session_state_fn=lambda: ({'ok': False, 'errors': ['bad']}, None, None, 0, 0, 0, 'balanced', 0),
        log_event_fn=lambda *args, **kwargs: events.append((args, kwargs)),
        build_main_session_setup_fn=lambda state: None,
        build_main_skip_summary_flushers_fn=lambda **kwargs: {},
        build_main_runtime_callbacks_fn=lambda **kwargs: {},
        build_main_post_run_actions_callback_fn=lambda **kwargs: None,
        build_main_precheck_hooks_fn=lambda **kwargs: {},
        build_runtime_precheck_context_inputs_fn=lambda **kwargs: None,
        build_main_prepare_callbacks_fn=lambda **kwargs: {},
        build_main_planner_callbacks_fn=lambda **kwargs: {},
        build_runtime_persist_services_fn=lambda **kwargs: None,
        build_main_persist_callbacks_fn=lambda **kwargs: {},
        build_runtime_session_bundle_inputs_fn=lambda **kwargs: None,
        build_runtime_session_bundles_fn=lambda **kwargs: None,
        build_main_execute_runtime_task_callback_fn=lambda **kwargs: None,
        run_main_execution_stage_fn=lambda **kwargs: None,
        project_runtime_decision_to_run_info_fn=lambda **kwargs: {},
        maybe_reconsult_planner_fn=lambda *args, **kwargs: None,
        summarize_planner_feedback_fn=lambda *args, **kwargs: {},
        build_execute_runtime_request_fn=lambda *args, **kwargs: {},
        persist_recorded_run_fn=lambda **kwargs: 0.0,
        log_operation_fn=lambda *args, **kwargs: None,
        is_sensitive_host_fn=lambda host: False,
        host_warmup_complete_fn=lambda host_state, target: True,
    )
    out = capsys.readouterr().out
    assert 'invalid_campaign_configuration' in out
    assert events


def test_run_main_entry_wires_and_runs_execution_stage() -> None:
    calls = {}
    setup = SimpleNamespace(
        precheck_skip_count_ref=[0], precheck_skip_examples=[], dns_skip_count={}, host_cooldown_skip_count={}, execution_gate_skip_count={}, execution_gate_skip_examples={},
        runs=[], followup_queue=[], precision_queue=[], quality_telemetry={}, host_state={}, queue_coordinator=object(), retry_counts={}, followup_counts={}, followup_recent={}, max_followups_per_target=2,
        scheduled_keys=set(), host_weak_count={}, host_family_owner_gate={}, confirm_counts={}, confirm_recent={}, confirm_class_counts={}, max_confirm_jobs_per_target=1, max_confirm_jobs_total=2, max_confirm_jobs_per_class=1,
        confirm_job_cooldown_sec=60, toggles={}, unresolved_hosts=set(), host_dns_cache={}, autodiscover_deep_skip=False, executed_keys=set(), host_precheck_burst={}, deep_budget={}, host_fail_streak={}, host_success_count={}, host_fail_count={},
        planner_hints_cache_ref=[{}], last_regen_run_index_ref=[0], curated_plan_ref=[[]], active_plan_revision_ref=[0], active_plan_hash_ref=[''], last_persist_ts_ref=[0.0], qualification_mode='shadow', qualification_promising_threshold='probable',
        code000_streak_threshold=3, code000_cooldown_sec=900, code000_session_cap=5, host_cooldown_until={}, host_code000_streak={}, host_code000_total={}, host_403_streak={}
    )
    runtime_callbacks = {'persist_live_summary': lambda: None, 'enqueue_followup_task': lambda task, high_priority=False: None}
    prepare_callbacks = {'prepare_task_precheck': lambda **kwargs: {}, 'prepare_curated_task': lambda *args, **kwargs: None, 'prepare_runtime_task': lambda *args, **kwargs: None, 'reprioritize_queues': lambda: None}
    planner_callbacks = {'refresh_planner_hints_and_reprioritize': lambda **kwargs: None, 'maybe_trigger_plan_regeneration': lambda reason, force=False: None, 'reconcile_active_plan_if_needed': lambda reason: None}
    persist_callbacks = {'record_and_persist_run': lambda run_info: None, 'apply_recorded_runtime_adaptation': lambda run_info: None}
    bundles = SimpleNamespace(runner_deps=object(), execution_deps=object(), prepare_deps=object())

    rrme.run_main_entry(
        build_runtime_session_state_fn=lambda: ({'ok': True}, object(), 'started', 5, 9, 10, 'balanced', 1),
        log_event_fn=lambda *args, **kwargs: None,
        build_main_session_setup_fn=lambda state: setup,
        build_main_skip_summary_flushers_fn=lambda **kwargs: {'flush_precheck_summary': lambda force=False: None, 'flush_dns_skip_summary': lambda force=False: None, 'flush_host_cooldown_summary': lambda force=False: None, 'flush_execution_gate_summary': lambda force=False: None},
        build_main_runtime_callbacks_fn=lambda **kwargs: runtime_callbacks,
        build_main_post_run_actions_callback_fn=lambda **kwargs: (lambda *args, **kwargs2: (0, {})),
        build_main_precheck_hooks_fn=lambda **kwargs: {'inc_precheck_skip': lambda: None, 'on_executed_key': lambda: None},
        build_runtime_precheck_context_inputs_fn=lambda **kwargs: object(),
        build_main_prepare_callbacks_fn=lambda **kwargs: prepare_callbacks,
        build_main_planner_callbacks_fn=lambda **kwargs: planner_callbacks,
        build_runtime_persist_services_fn=lambda **kwargs: object(),
        build_main_persist_callbacks_fn=lambda **kwargs: persist_callbacks,
        build_runtime_session_bundle_inputs_fn=lambda **kwargs: SimpleNamespace(**kwargs),
        build_runtime_session_bundles_fn=lambda **kwargs: bundles,
        build_main_execute_runtime_task_callback_fn=lambda **kwargs: (lambda *args, **kwargs2: (0.0, 0)),
        run_main_execution_stage_fn=lambda **kwargs: calls.update(kwargs),
        project_runtime_decision_to_run_info_fn=lambda **kwargs: {},
        maybe_reconsult_planner_fn=lambda *args, **kwargs: None,
        summarize_planner_feedback_fn=lambda *args, **kwargs: {},
        build_execute_runtime_request_fn=lambda *args, **kwargs: {},
        persist_recorded_run_fn=lambda **kwargs: 0.0,
        log_operation_fn=lambda *args, **kwargs: None,
        is_sensitive_host_fn=lambda host: False,
        host_warmup_complete_fn=lambda host_state, target: True,
    )
    assert calls['max_runs'] == 5
    assert calls['retry_policy'] == 'balanced'
