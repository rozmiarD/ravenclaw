from __future__ import annotations

import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from runtime_loop_control import run_curated_loop, run_main_loop, time_budget_reached  # type: ignore


def test_time_budget_reached_detects_expiry() -> None:
    started = datetime.now(timezone.utc) - timedelta(minutes=11)
    assert time_budget_reached(run_started=started, time_budget_min=10) is True


def test_run_curated_loop_executes_prepared_entries() -> None:
    calls = []
    hb, confirm_total, idx, budget_hit = run_curated_loop(
        curated_plan=[{'objective': 'Recon', 'target': 'https://a.example.com/'}],
        max_runs=3,
        run_started=datetime.now(timezone.utc),
        time_budget_min=10,
        target_load_limit=5,
        runs=[],
        normalize_runtime_task_fn=lambda entry: entry,
        reconcile_active_plan_if_needed_fn=lambda reason: calls.append(('reconcile', reason)),
        log_event_fn=lambda *args, **kwargs: calls.append(('log', args[1])),
        refresh_runtime_overrides_fn=lambda *args: (False, False, None, None),
        owner_override_global=False,
        last_override_state=False,
        aggression_override_global=None,
        last_aggression_override=None,
        preempt_in_curated=True,
        precision_queue=[],
        followup_queue=[],
        maybe_preempt_curated_entry_fn=lambda entry, **kwargs: (entry, False),
        dequeue_next_task_fn=lambda: None,
        requeue_task_fn=lambda task: calls.append(('requeue', task.get('target'))),
        prepare_curated_task_fn=lambda entry, aggression_override: {'task_ctx': {}, 'objective': 'Recon', 'target': 'https://a.example.com/', 'mode': 'fast', 'aggression': 3, 'owner_auth': False, 'owner_override': False, 'plan_name': 'Plan'},
        build_execute_runtime_request_fn=lambda prepared, **kwargs: {'task_ctx': prepared['task_ctx'], **kwargs, 'objective': prepared['objective'], 'target': prepared['target'], 'mode': prepared['mode'], 'aggression': prepared['aggression'], 'owner_auth': prepared['owner_auth'], 'owner_override': prepared['owner_override'], 'plan_name': prepared['plan_name']},
        execute_runtime_task_fn=lambda task_ctx, **kwargs: (1.0, 2),
        last_heartbeat_ts=0.0,
        confirm_total=0,
        idx=0,
        build_deduped_target_plan_fn=lambda raw_plan, dedup_key_fn: raw_plan,
        dedup_key_fn=lambda *args: ('k',),
    )
    assert hb == 1.0
    assert confirm_total == 2
    assert idx == 1
    assert budget_hit is False
    assert ('reconcile', 'safe_boundary_curated_loop') in calls


def test_run_curated_loop_requeues_preempted_task_when_prepare_fails() -> None:
    requeued = []
    queued = {'objective': 'Follow-up', 'target': 'https://queued.example.com/', 'mode': 'followup', '_queue_lane': 'followup'}
    hb, confirm_total, idx, budget_hit = run_curated_loop(
        curated_plan=[{'objective': 'Recon', 'target': 'https://a.example.com/'}],
        max_runs=3,
        run_started=datetime.now(timezone.utc),
        time_budget_min=10,
        target_load_limit=5,
        runs=[],
        normalize_runtime_task_fn=lambda entry: entry,
        reconcile_active_plan_if_needed_fn=lambda reason: None,
        log_event_fn=lambda *args, **kwargs: None,
        refresh_runtime_overrides_fn=lambda *args: (False, False, None, None),
        owner_override_global=False,
        last_override_state=False,
        aggression_override_global=None,
        last_aggression_override=None,
        preempt_in_curated=True,
        precision_queue=[],
        followup_queue=[queued],
        maybe_preempt_curated_entry_fn=lambda entry, **kwargs: (queued, True),
        dequeue_next_task_fn=lambda: queued,
        requeue_task_fn=lambda task: requeued.append(task),
        prepare_curated_task_fn=lambda entry, aggression_override: None,
        build_execute_runtime_request_fn=lambda prepared, **kwargs: {},
        execute_runtime_task_fn=lambda **kwargs: (0.0, 0),
        last_heartbeat_ts=0.0,
        confirm_total=0,
        idx=0,
        build_deduped_target_plan_fn=lambda raw_plan, dedup_key_fn: raw_plan,
        dedup_key_fn=lambda *args: ('k',),
    )
    assert hb == 0.0
    assert confirm_total == 0
    assert idx == 0
    assert budget_hit is False
    assert requeued == [queued]


def test_run_main_loop_breaks_on_fatal_selection() -> None:
    recorded = []
    hb, confirm_total, budget_hit = run_main_loop(
        max_runs=3,
        runs=[],
        run_started=datetime.now(timezone.utc),
        time_budget_min=10,
        reconcile_active_plan_if_needed_fn=lambda reason: None,
        log_event_fn=lambda *args, **kwargs: None,
        refresh_runtime_overrides_fn=lambda *args: (False, False, None, None),
        owner_override_global=False,
        last_override_state=False,
        aggression_override_global=None,
        last_aggression_override=None,
        dequeue_next_task_fn=lambda: None,
        requeue_task_fn=lambda task: recorded.append(task),
        history=[],
        scope_targets=['a.example.com'],
        normalize_runtime_task_fn=lambda task: task,
        unpack_queued_task_fn=lambda task, **kwargs: task,
        clamp_aggression_fn=lambda n: n,
        capped_aggression_fn=lambda family, target, aggression: aggression,
        propose_next_vector_fn=lambda history: ('Probe', 'https://a.example.com/'),
        prepare_runtime_task_fn=lambda *args, **kwargs: None,
        build_execute_runtime_request_fn=lambda prepared, **kwargs: {'task_ctx': prepared.get('task_ctx', {}), **kwargs},
        execute_runtime_task_fn=lambda *args, **kwargs: (0.0, 0),
        last_heartbeat_ts=0.0,
        confirm_total=0,
        selected_error_record_fn=lambda *args: {'status': 'fatal', 'error_msg': 'brain_proposal_failed'},
    )
    assert hb == 0.0
    assert confirm_total == 0
    assert budget_hit is False


def test_run_main_loop_requeues_queue_task_when_prepare_fails() -> None:
    queued = {'objective': 'Queued', 'target': 'https://queued.example.com/', 'task_family': 'recon', '_queue_lane': 'followup'}
    requeued = []
    selected_calls = {'count': 0}

    def _selected(*_args):
        if selected_calls['count'] == 0:
            selected_calls['count'] += 1
            return {'status': 'ok', 'source': 'queue', 'task': queued, 'objective': queued['objective'], 'target': queued['target'], 'aggression': 5, 'mode': 'followup', 'owner_auth': False, 'owner_override': False, 'plan_name': 'Queued'}
        return {'status': 'fatal', 'error_msg': 'stop_after_requeue'}

    hb, confirm_total, budget_hit = run_main_loop(
        max_runs=3,
        runs=[],
        run_started=datetime.now(timezone.utc),
        time_budget_min=10,
        reconcile_active_plan_if_needed_fn=lambda reason: None,
        log_event_fn=lambda *args, **kwargs: None,
        refresh_runtime_overrides_fn=lambda *args: (False, False, None, None),
        owner_override_global=False,
        last_override_state=False,
        aggression_override_global=None,
        last_aggression_override=None,
        dequeue_next_task_fn=lambda: None,
        requeue_task_fn=lambda task: requeued.append(task),
        history=[],
        scope_targets=['a.example.com'],
        normalize_runtime_task_fn=lambda task: task,
        unpack_queued_task_fn=lambda task, **kwargs: {'task': task, 'objective': task['objective'], 'target': task['target'], 'aggression': 5, 'mode': 'followup', 'owner_auth': False, 'owner_override': False, 'plan_name': 'Queued'},
        clamp_aggression_fn=lambda n: n,
        capped_aggression_fn=lambda family, target, aggression: aggression,
        propose_next_vector_fn=lambda history: ('Probe', 'https://a.example.com/'),
        prepare_runtime_task_fn=lambda *args, **kwargs: None,
        build_execute_runtime_request_fn=lambda prepared, **kwargs: {'task_ctx': prepared.get('task_ctx', {}), **kwargs},
        execute_runtime_task_fn=lambda *args, **kwargs: (0.0, 0),
        last_heartbeat_ts=0.0,
        confirm_total=0,
        selected_error_record_fn=_selected,
    )
    assert hb == 0.0
    assert confirm_total == 0
    assert budget_hit is False
    assert requeued == [queued]


def test_run_curated_loop_stops_when_runtime_stop_requested() -> None:
    executed = []
    hb, confirm_total, idx, budget_hit = run_curated_loop(
        curated_plan=[{'objective': 'Recon', 'target': 'https://a.example.com/'}],
        max_runs=3,
        run_started=datetime.now(timezone.utc),
        time_budget_min=10,
        target_load_limit=5,
        runs=[],
        normalize_runtime_task_fn=lambda entry: entry,
        reconcile_active_plan_if_needed_fn=lambda reason: None,
        log_event_fn=lambda *args, **kwargs: None,
        refresh_runtime_overrides_fn=lambda *args: (False, False, None, None),
        owner_override_global=False,
        last_override_state=False,
        aggression_override_global=None,
        last_aggression_override=None,
        preempt_in_curated=True,
        precision_queue=[],
        followup_queue=[],
        maybe_preempt_curated_entry_fn=lambda entry, **kwargs: (entry, False),
        dequeue_next_task_fn=lambda: None,
        requeue_task_fn=lambda task: None,
        prepare_curated_task_fn=lambda entry, aggression_override: {'task_ctx': {}, 'objective': 'Recon', 'target': 'https://a.example.com/', 'mode': 'fast', 'aggression': 3, 'owner_auth': False, 'owner_override': False, 'plan_name': 'Plan'},
        build_execute_runtime_request_fn=lambda prepared, **kwargs: {},
        execute_runtime_task_fn=lambda **kwargs: executed.append(True) or (0.0, 0),
        last_heartbeat_ts=0.0,
        confirm_total=0,
        idx=0,
        build_deduped_target_plan_fn=lambda raw_plan, dedup_key_fn: raw_plan,
        dedup_key_fn=lambda *args: ('k',),
        read_runtime_control_state_fn=lambda: {'stopped': True},
        sleep_fn=lambda _sec: None,
    )
    assert executed == []
    assert hb == 0.0
    assert confirm_total == 0
    assert idx == 0
    assert budget_hit is False


def test_run_main_loop_waits_while_paused_then_resumes() -> None:
    selected_calls = {'count': 0}
    control_states = iter([
        {'paused': True, 'stopped': False},
        {'paused': False, 'stopped': False},
    ])
    slept = []

    def _selected(*_args):
        if selected_calls['count'] == 0:
            selected_calls['count'] += 1
            return {'status': 'fatal', 'error_msg': 'stop_after_resume'}
        return {'status': 'fatal', 'error_msg': 'done'}

    hb, confirm_total, budget_hit = run_main_loop(
        max_runs=3,
        runs=[],
        run_started=datetime.now(timezone.utc),
        time_budget_min=10,
        reconcile_active_plan_if_needed_fn=lambda reason: None,
        log_event_fn=lambda *args, **kwargs: None,
        refresh_runtime_overrides_fn=lambda *args: (False, False, None, None),
        owner_override_global=False,
        last_override_state=False,
        aggression_override_global=None,
        last_aggression_override=None,
        dequeue_next_task_fn=lambda: None,
        requeue_task_fn=lambda task: None,
        history=[],
        scope_targets=['a.example.com'],
        normalize_runtime_task_fn=lambda task: task,
        unpack_queued_task_fn=lambda task, **kwargs: task,
        clamp_aggression_fn=lambda n: n,
        capped_aggression_fn=lambda family, target, aggression: aggression,
        propose_next_vector_fn=lambda history: ('Probe', 'https://a.example.com/'),
        prepare_runtime_task_fn=lambda *args, **kwargs: None,
        build_execute_runtime_request_fn=lambda prepared, **kwargs: {'task_ctx': prepared.get('task_ctx', {}), **kwargs},
        execute_runtime_task_fn=lambda *args, **kwargs: (0.0, 0),
        last_heartbeat_ts=0.0,
        confirm_total=0,
        selected_error_record_fn=_selected,
        read_runtime_control_state_fn=lambda: next(control_states),
        sleep_fn=lambda sec: slept.append(sec),
    )
    assert slept == [1.0]
    assert hb == 0.0
    assert confirm_total == 0
    assert budget_hit is False
