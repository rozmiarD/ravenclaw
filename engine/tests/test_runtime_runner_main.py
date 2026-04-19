from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from runtime_prepare_deps import RuntimePrepareDeps  # type: ignore
from runtime_runner_main import execute_runner_session, finalize_runner_exception  # type: ignore
from runtime_session_state import RuntimeSessionState  # type: ignore


def test_execute_runner_session_returns_summary() -> None:
    state = RuntimeSessionState(runs=[], history=[], host_state={}, curated_plan=[], runtime_plan_meta={}, host_dns_cache={}, toggles={}, planner_hints_cache={})
    prepare_deps = RuntimePrepareDeps(
        precheck_and_prepare_task_fn=lambda **kwargs: {},
        prepare_curated_task_fn=lambda *args, **kwargs: None,
        prepare_runtime_task_fn=lambda *args, **kwargs: None,
    )
    summary = execute_runner_session(
        state=state,
        max_runs=5,
        target_load_limit=9,
        time_budget_min=10,
        retry_policy='balanced',
        run_started=datetime.now(timezone.utc),
        scope_targets=['a.example.com'],
        preempt_in_curated=True,
        queue_coordinator=type('Q', (), {'enqueue': lambda self, task, high_priority=False: None, 'dequeue': lambda self: None})(),
        log_event_fn=lambda *args, **kwargs: None,
        read_runtime_control_state_fn=lambda: {},
        read_runtime_owner_override_fn=lambda default=False: False,
        read_runtime_aggression_override_fn=lambda: None,
        apply_runtime_overrides_fn=lambda **kwargs: (False, False, None, None),
        handle_post_run_actions_fn=lambda **kwargs: (0, {}),
        prepare_curated_task_fn=lambda *args, **kwargs: None,
        prepare_runtime_task_fn=lambda *args, **kwargs: None,
        reprioritize_queues_fn=lambda **kwargs: None,
        persist_recorded_run_fn=lambda **kwargs: 0.0,
        maybe_trigger_plan_regeneration_fn=lambda reason: None,
        execute_runtime_task_fn=lambda *args, **kwargs: (0.0, 0),
        resolve_main_loop_candidate_fn=lambda **kwargs: {'status': 'fatal', 'error_msg': 'brain_proposal_failed'},
        record_run_fn=lambda runs, row: runs.append(row),
        persist_live_summary_fn=lambda: None,
        normalize_runtime_task_fn=lambda task: task,
        reconcile_active_plan_if_needed_fn=lambda reason: None,
        maybe_preempt_curated_entry_fn=lambda entry, **kwargs: (entry, False),
        dedup_key_fn=lambda *args: ('k',),
        build_deduped_target_plan_fn=lambda raw_plan, dedup_key_fn: raw_plan,
        prepare_deps=prepare_deps,
        propose_next_vector_fn=lambda history: ('Probe', 'https://a.example.com/'),
        unpack_queued_task_fn=lambda task, **kwargs: task,
        clamp_aggression_fn=lambda n: n,
        capped_aggression_fn=lambda family, target, aggression: aggression,
        run_curated_loop_fn=lambda **kwargs: (0.0, 0, 0, False),
        run_main_loop_fn=lambda **kwargs: (0.0, 0, False),
        out_path='out.json',
        reports_dir=Path('.'),
        archive_root=Path('.'),
        campaign_validation={'ok': True},
        quality_telemetry={},
        finalize_outputs_fn=lambda **kwargs: {'executed': len(kwargs['runs'])},
        flush_precheck_summary_fn=lambda force=False: None,
        flush_dns_skip_summary_fn=lambda force=False: None,
        flush_host_cooldown_summary_fn=lambda force=False: None,
        flush_execution_gate_summary_fn=lambda force=False: None,
        log_operation_fn=lambda *args, **kwargs: None,
    )
    assert 'executed' in summary


def test_finalize_runner_exception_completes_without_raise() -> None:
    state = RuntimeSessionState(runs=[], history=[], host_state={}, curated_plan=[], runtime_plan_meta={}, host_dns_cache={}, toggles={}, planner_hints_cache={})
    finalize_runner_exception(
        state=state,
        campaign_validation={'ok': True},
        run_started=datetime.now(timezone.utc),
        max_runs=1,
        time_budget_min=1,
        retry_policy='balanced',
        out_path='out.json',
        reports_dir=Path('.'),
        archive_root=Path('.'),
        quality_telemetry={},
        finalize_outputs_fn=lambda **kwargs: {'executed': 0},
        flush_precheck_summary_fn=lambda force=False: None,
        flush_dns_skip_summary_fn=lambda force=False: None,
        flush_host_cooldown_summary_fn=lambda force=False: None,
        flush_execution_gate_summary_fn=lambda force=False: None,
        log_operation_fn=lambda *args, **kwargs: None,
        error=RuntimeError('boom'),
    )
