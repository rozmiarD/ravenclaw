from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_runner_execution_stage as rres  # type: ignore


def test_build_execute_runner_session_inputs_assembles_runner_call_bundle() -> None:
    state = SimpleNamespace()
    prepare_deps = SimpleNamespace()
    payload = rres.build_execute_runner_session_inputs(
        state=state,
        max_runs=5,
        target_load_limit=9,
        time_budget_min=10,
        retry_policy='balanced',
        run_started=datetime.now(timezone.utc),
        scope_targets=['a.example.com'],
        toggles={'queue_preemption_in_curated_loop': False},
        queue_coordinator=object(),
        prepare_deps=prepare_deps,
        quality_telemetry={},
        campaign_validation={'ok': True},
        execute_runtime_task_fn=lambda *args, **kwargs: (0.0, 0),
        maybe_trigger_plan_regeneration_fn=lambda reason, force=False: None,
        reconcile_active_plan_if_needed_fn=lambda reason: None,
        persist_live_summary_fn=lambda: None,
        flush_precheck_summary_fn=lambda force=False: None,
        flush_dns_skip_summary_fn=lambda force=False: None,
        flush_host_cooldown_summary_fn=lambda force=False: None,
        flush_execution_gate_summary_fn=lambda force=False: None,
        log_operation_fn=lambda *args, **kwargs: None,
        log_event_fn=lambda *args, **kwargs: None,
        read_runtime_control_state_fn=lambda: {},
        read_runtime_owner_override_fn=lambda default=False: False,
        read_runtime_aggression_override_fn=lambda: None,
        apply_runtime_overrides_fn=lambda *args, **kwargs: (False, False, None, None),
        handle_post_run_actions_fn=lambda *args, **kwargs: (0, {}),
        prepare_curated_task_fn=lambda *args, **kwargs: None,
        prepare_runtime_task_fn=lambda *args, **kwargs: None,
        reprioritize_queues_fn=lambda: None,
        persist_recorded_run_fn=lambda **kwargs: 0.0,
        resolve_main_loop_candidate_fn=lambda *args, **kwargs: None,
        record_run_fn=lambda **kwargs: None,
        normalize_runtime_task_fn=lambda task: task,
        maybe_preempt_curated_entry_fn=lambda *args, **kwargs: None,
        dedup_key_fn=lambda *args, **kwargs: 'dedup:1',
        build_deduped_target_plan_fn=lambda *args, **kwargs: [],
        propose_next_vector_fn=lambda *args, **kwargs: None,
        unpack_queued_task_fn=lambda *args, **kwargs: (),
        clamp_aggression_fn=lambda level: level,
        capped_aggression_fn=lambda family, target, aggression: aggression,
        run_curated_loop_fn=lambda *args, **kwargs: None,
        run_main_loop_fn=lambda *args, **kwargs: None,
        out_path='reports/out.json',
        reports_dir=Path('reports'),
        archive_root=Path('archive'),
        finalize_outputs_fn=lambda **kwargs: {},
    )
    assert payload.state == state
    assert payload.max_runs == 5
    assert payload.target_load_limit == 9
    assert payload.preempt_in_curated is False
    assert payload.prepare_deps == prepare_deps
    assert payload.execute_runtime_task_fn is not None


def test_build_finalize_runner_exception_inputs_assembles_finalize_bundle() -> None:
    state = SimpleNamespace()
    err = RuntimeError('boom')
    payload = rres.build_finalize_runner_exception_inputs(
        state=state,
        campaign_validation={'ok': True},
        run_started=datetime.now(timezone.utc),
        max_runs=5,
        time_budget_min=10,
        retry_policy='balanced',
        quality_telemetry={},
        flush_precheck_summary_fn=lambda force=False: None,
        flush_dns_skip_summary_fn=lambda force=False: None,
        flush_host_cooldown_summary_fn=lambda force=False: None,
        flush_execution_gate_summary_fn=lambda force=False: None,
        log_operation_fn=lambda *args, **kwargs: None,
        error=err,
        out_path='reports/out.json',
        reports_dir=Path('reports'),
        archive_root=Path('archive'),
        finalize_outputs_fn=lambda **kwargs: {},
    )
    assert payload.state == state
    assert payload.retry_policy == 'balanced'
    assert payload.error is err
    assert payload.reports_dir == Path('reports')
