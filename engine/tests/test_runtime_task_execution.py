from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_task_execution as rte  # type: ignore
from runtime_task_execution import _build_dispatch_runtime_request, _build_execute_runtime_context, _build_post_runtime_inputs, _build_qualify_runtime_inputs, _build_run_pipeline_runtime_payload, _build_runtime_dispatch_stage_inputs, _build_runtime_result_stage_inputs, _build_runtime_task_execution_result, _emit_runtime_dispatch_events, _invoke_runtime_dispatch_request, _process_runtime_task_result, _run_runtime_dispatch_stage, dispatch_runtime_task, execute_runtime_task_pipeline  # type: ignore
from runtime_execution_deps import RuntimeExecutionDeps  # type: ignore


def test_emit_runtime_dispatch_events_emits_heartbeat_when_interval_elapsed(monkeypatch) -> None:
    events = []

    class FakeNow:
        def timestamp(self):
            return 100.0

    class FakeDateTime:
        @staticmethod
        def now(_tz=None):
            return FakeNow()

    monkeypatch.setattr(rte, 'datetime', FakeDateTime)
    hb = _emit_runtime_dispatch_events(
        label='Recon a',
        target='https://a.example.com/',
        mode='fast',
        run_index=1,
        last_heartbeat_ts=0.0,
        runs_count=5,
        followup_queue_len=2,
        precision_queue_len=1,
        log_event_fn=lambda *args, **kwargs: events.append((args, kwargs)),
    )
    assert hb == 100.0
    assert any(args[1] == 'pipeline_heartbeat' for args, _kwargs in events)



def test_invoke_runtime_dispatch_request_threads_request_into_pipeline_call() -> None:
    called = {}
    request = {
        'objective': 'Recon',
        'target': 'https://a.example.com/',
        'aggression': 3,
        'owner_auth': False,
        'owner_override': True,
        'task_family': 'recon',
    }
    out = _invoke_runtime_dispatch_request(
        request,
        run_pipeline_fn=lambda objective, target, **kwargs: called.update({'objective': objective, 'target': target, **kwargs}) or {'ok': True},
    )
    assert out == {'ok': True}
    assert called['objective'] == 'Recon'
    assert called['target'] == 'https://a.example.com/'
    assert called['aggression'] == 3
    assert called['owner_override'] is True
    assert called['task_family'] == 'recon'



def test_dispatch_runtime_task_emits_heartbeat_and_runs_pipeline() -> None:
    events = []
    called = {}

    result, hb = dispatch_runtime_task(
        task_ctx={'task_family': 'recon', 'task_success_criteria': 'ok', 'campaign_success_criteria': 'ok'},
        objective='Recon',
        target='https://a.example.com/',
        mode='fast',
        aggression=3,
        owner_auth=False,
        owner_override=False,
        label='Recon a',
        run_index=1,
        last_heartbeat_ts=0.0,
        runs_count=5,
        followup_queue_len=2,
        precision_queue_len=1,
        log_event_fn=lambda *args, **kwargs: events.append((args, kwargs)),
        run_pipeline_fn=lambda objective, target, **kwargs: called.update({'objective': objective, 'target': target, **kwargs}) or {'ok': True},
    )

    assert result == {'ok': True}
    assert hb > 0
    assert any(args[1] == 'pipeline_heartbeat' for args, _kwargs in events)
    assert called['objective'] == 'Recon'
    assert called['task_family'] == 'recon'


def test_build_run_pipeline_runtime_payload_merges_task_and_runtime_intent_fields() -> None:
    task_ctx = {
        'task_family': 'authz',
        'task_success_criteria': 'ok',
        'campaign_success_criteria': 'campaign-ok',
        'acceptance_checks': ['negative_control'],
        'runtime_task': {
            'experiment_intent_id': 'intent-authz-1',
            'capability_candidates': ['http_probe', 'response_diff'],
            'recommended_action_types': ['differential_probe'],
            'hypothesis_candidates': ['idor', 'compare insight2.tradepmr.com role edge'],
            'planner_constraints': {'campaign_bound_context': True},
            'planner_preferences': {'preferred_vector_families': ['authz']},
            'planner_rationale': {'target_surface_rationale': ['authenticated_or_boundary_mapping'], 'recommended_progression': ['authenticated_or_boundary_mapping', 'control_boundary_confirmation']},
            'planning_ladder': {'current_stage': 'control_boundary_confirmation', 'next_stage': 'bounded_exploit_proof'},
            'open_questions': ['role inheritance unclear', 'why does insight2.tradepmr.com differ?'],
            'success_semantics': {'success_model': 'differential_or_stateful_signal'},
        },
    }
    payload = _build_run_pipeline_runtime_payload(task_ctx, 'https://api.example.com/')
    assert payload['success_criteria'] == 'ok'
    assert payload['campaign_success_criteria'] == 'campaign-ok'
    assert payload['task_family'] == 'authz'
    assert payload['acceptance_checks'] == 'negative_control'
    assert payload['experiment_intent_id'] == 'intent-authz-1'
    assert 'http_probe' in payload['capability_candidates_json']
    assert 'differential_probe' in payload['recommended_action_types_json']
    assert 'campaign_bound_context' in payload['planner_constraints_json']
    assert 'preferred_vector_families' in payload['planner_preferences_json']
    assert 'role inheritance unclear' in payload['open_questions_json']
    assert 'insight2.tradepmr.com' not in payload['open_questions_json']
    assert 'insight2.tradepmr.com' not in payload['hypothesis_candidates_json']
    assert 'differential_or_stateful_signal' in payload['success_semantics_json']
    assert 'bounded_exploit_proof' in payload['planning_ladder_json']
    assert 'authenticated_or_boundary_mapping' in payload['target_surface_rationale_json']
    assert 'control_boundary_confirmation' in payload['recommended_progression_json']
    assert 'lineage_sha256' in payload['semantic_lineage_json']
    assert 'control_boundary_confirmation' in payload['semantic_lineage_json']
    assert 'summary' in payload['semantic_lineage_json']
    assert 'control_boundary_confirmation' in payload['semantic_lineage_summary_json']


def test_build_dispatch_runtime_request_wraps_payload_and_dispatch_controls() -> None:
    task_ctx = {
        'task_family': 'authz',
        'task_success_criteria': 'ok',
        'runtime_task': {
            'experiment_intent_id': 'intent-authz-1',
            'capability_candidates': ['http_probe'],
        },
    }
    request = _build_dispatch_runtime_request(
        task_ctx=task_ctx,
        objective='Probe',
        target='https://api.example.com/',
        aggression=4,
        owner_auth=True,
        owner_override=False,
    )
    assert request['objective'] == 'Probe'
    assert request['target'] == 'https://api.example.com/'
    assert request['aggression'] == 4
    assert request['owner_auth'] is True
    assert request['owner_override'] is False
    assert request['task_family'] == 'authz'
    assert request['experiment_intent_id'] == 'intent-authz-1'
    assert 'http_probe' in request['capability_candidates_json']


def test_build_execute_runtime_context_normalizes_plan_name_and_decision_label() -> None:
    ctx = _build_execute_runtime_context(
        objective='Probe',
        target='https://api.example.com/',
        mode='fast',
        aggression=4,
        owner_auth=True,
        owner_override=False,
        plan_name='Plan A',
        run_index=7,
    )
    assert ctx['objective'] == 'Probe'
    assert ctx['target'] == 'https://api.example.com/'
    assert ctx['mode'] == 'fast'
    assert ctx['aggression'] == 4
    assert ctx['owner_auth'] is True
    assert ctx['owner_override'] is False
    assert ctx['plan_name'] == 'Plan A'
    assert ctx['decision_label'] == 'Plan A'



def test_dispatch_runtime_task_threads_intent_level_fields_to_pipeline() -> None:
    called = {}
    task_ctx = {
        'task_family': 'authz',
        'task_success_criteria': 'ok',
        'campaign_success_criteria': 'ok',
        'runtime_task': {
            'experiment_intent_id': 'intent-authz-1',
            'capability_candidates': ['http_probe', 'response_diff'],
            'recommended_action_types': ['differential_probe'],
            'hypothesis_candidates': ['idor'],
            'planner_constraints': {'campaign_bound_context': True},
            'planner_preferences': {'preferred_vector_families': ['authz']},
            'open_questions': ['role inheritance unclear'],
            'success_semantics': {'success_model': 'differential_or_stateful_signal', 'expected_signal_type': 'behavior_delta', 'evidence_goal_type': 'controlled_comparison'},
        },
    }
    dispatch_runtime_task(
        task_ctx=task_ctx,
        objective='Probe',
        target='https://api.example.com/',
        mode='fast',
        aggression=4,
        owner_auth=False,
        owner_override=False,
        label='Probe',
        run_index=1,
        last_heartbeat_ts=0.0,
        runs_count=0,
        followup_queue_len=0,
        precision_queue_len=0,
        log_event_fn=lambda *args, **kwargs: None,
        run_pipeline_fn=lambda objective, target, **kwargs: called.update({'objective': objective, 'target': target, **kwargs}) or {'ok': True},
    )
    expected_request = _build_dispatch_runtime_request(
        task_ctx=task_ctx,
        objective='Probe',
        target='https://api.example.com/',
        aggression=4,
        owner_auth=False,
        owner_override=False,
    )
    for key, value in expected_request.items():
        assert called[key] == value
    assert called['experiment_intent_id'] == 'intent-authz-1'
    assert 'http_probe' in called['capability_candidates_json']
    assert 'differential_probe' in called['recommended_action_types_json']
    assert 'campaign_bound_context' in called['planner_constraints_json']
    assert 'preferred_vector_families' in called['planner_preferences_json']
    assert 'role inheritance unclear' in called['open_questions_json']
    assert 'differential_or_stateful_signal' in called['success_semantics_json']


def test_build_post_runtime_inputs_uses_normalized_context() -> None:
    ctx = _build_execute_runtime_context(
        objective='Probe',
        target='https://api.example.com/',
        mode='fast',
        aggression=5,
        owner_auth=False,
        owner_override=True,
        plan_name='Plan',
        run_index=2,
    )
    deps = RuntimeExecutionDeps(
        summarize_result_fn=lambda result: ('medium', 'approve', 'ok', 'summary', False),
        post_result_common_fn=lambda **kwargs: kwargs,
        qualify_and_finalize_run_fn=lambda **kwargs: ({}, False, {}),
        inspect_json_signal_from_command_fn=lambda *args, **kwargs: None,
        parse_rc_metrics_fn=lambda *args, **kwargs: {},
        run_control_comparison_fn=lambda *args, **kwargs: {},
        attack_family_fn=lambda *args, **kwargs: 'authz',
        repeated_consistency_ok_fn=lambda runs, target, objective: True,
        qualify_fn=lambda payload: payload,
        can_be_confirmed_fn=lambda qual: True,
        compute_promising_fn=lambda qual, summary_text, classification: True,
        finding_lifecycle_fn=lambda mode, qual: 'probable',
        adaptive_aggression_fn=lambda aggression, classification, reason_code, owner_override: aggression,
        normalize_pipeline_status_fn=lambda engine_status, auditor_decision, error_flag: engine_status,
        log_event_fn=lambda *args, **kwargs: None,
        run_pipeline_fn=lambda *args, **kwargs: {'ok': True},
    )
    payload = _build_post_runtime_inputs(
        task_ctx={'task_family': 'authz'},
        ctx=ctx,
        result={'ok': True},
        summary_text='summary',
        classification='medium',
        auditor='approve',
        engine_status='ok',
        run_index=2,
        deps=deps,
        host_family_owner_gate={},
        host_cooldown_until={},
        host_code000_streak={},
        host_code000_total={},
        host_403_streak={},
        host_fail_streak={},
        host_fail_count={},
        host_success_count={},
        code000_streak_threshold=3,
        code000_cooldown_sec=900,
        code000_session_cap=5,
        toggles={
            'transport_observation_cooldown_sec': 120,
            'http_403_streak_threshold': 2,
            'http_403_cooldown_sec': 900,
            'code000_session_cooldown_sec': 43200,
        },
    )
    assert payload['objective'] == 'Probe'
    assert payload['target'] == 'https://api.example.com/'
    assert payload['mode'] == 'fast'
    assert payload['plan_name'] == 'Plan'
    assert payload['owner_override'] is True
    assert payload['aggression'] == 5
    assert payload['transport_observation_cooldown_sec'] == 120
    assert payload['http_403_streak_threshold'] == 2
    assert payload['http_403_cooldown_sec'] == 900
    assert payload['code000_session_cooldown_sec'] == 43200



def test_build_qualify_runtime_inputs_uses_normalized_context() -> None:
    ctx = _build_execute_runtime_context(
        objective='Probe',
        target='https://api.example.com/',
        mode='fast',
        aggression=5,
        owner_auth=False,
        owner_override=True,
        plan_name='Plan',
        run_index=2,
    )
    deps = RuntimeExecutionDeps(
        summarize_result_fn=lambda result: ('medium', 'approve', 'ok', 'summary', False),
        post_result_common_fn=lambda **kwargs: kwargs,
        qualify_and_finalize_run_fn=lambda **kwargs: ({}, False, {}),
        inspect_json_signal_from_command_fn=lambda *args, **kwargs: None,
        parse_rc_metrics_fn=lambda *args, **kwargs: {},
        run_control_comparison_fn=lambda *args, **kwargs: {},
        attack_family_fn=lambda *args, **kwargs: 'authz',
        repeated_consistency_ok_fn=lambda runs, target, objective: target == 'https://api.example.com/' and objective == 'Probe',
        qualify_fn=lambda payload: payload,
        can_be_confirmed_fn=lambda qual: True,
        compute_promising_fn=lambda qual, summary_text, classification: True,
        finding_lifecycle_fn=lambda mode, qual: 'probable',
        adaptive_aggression_fn=lambda aggression, classification, reason_code, owner_override: aggression,
        normalize_pipeline_status_fn=lambda engine_status, auditor_decision, error_flag: engine_status,
        log_event_fn=lambda *args, **kwargs: None,
        run_pipeline_fn=lambda *args, **kwargs: {'ok': True},
    )
    payload = _build_qualify_runtime_inputs(
        ctx=ctx,
        post={'reason_code': 'interesting'},
        run_index=2,
        error_flag=False,
        runs=[],
        toggles={'policy_diag_logging': True},
        host_weak_count={},
        quality_telemetry={},
        qualification_mode='shadow',
        qualification_promising_threshold='probable',
        deps=deps,
    )
    assert payload['objective'] == 'Probe'
    assert payload['target'] == 'https://api.example.com/'
    assert payload['mode'] == 'fast'
    assert payload['decision_label'] == 'Plan'
    assert payload['owner_override'] is True
    assert payload['aggression'] == 5
    assert payload['policy_diag_logging'] is True
    assert payload['repeated_consistency'] is True



def test_build_runtime_task_execution_result_prefers_post_summary_and_classification() -> None:
    out = _build_runtime_task_execution_result(
        result={'ok': True},
        classification='initial',
        auditor='approve',
        engine_status='ok',
        summary_text='initial-summary',
        error_flag=False,
        post={'classification': 'post-class', 'summary_text': 'post-summary', 'reason_code': 'interesting'},
        qual={'verdict': 'probable'},
        promising=True,
        run_info={'runtime_decision': {}},
    )
    assert out[0] == {'ok': True}
    assert out[1] == 'post-class'
    assert out[2] == 'approve'
    assert out[3] == 'ok'
    assert out[4] == 'post-summary'
    assert out[5] is False
    assert out[7] == {'verdict': 'probable'}
    assert out[8] is True



def test_build_runtime_dispatch_stage_inputs_captures_dispatch_bundle() -> None:
    deps = RuntimeExecutionDeps(
        summarize_result_fn=lambda result: ('medium', 'approve', 'ok', 'summary', False),
        post_result_common_fn=lambda **kwargs: kwargs,
        qualify_and_finalize_run_fn=lambda **kwargs: ({}, False, {}),
        inspect_json_signal_from_command_fn=lambda *args, **kwargs: None,
        parse_rc_metrics_fn=lambda *args, **kwargs: {},
        run_control_comparison_fn=lambda *args, **kwargs: {},
        attack_family_fn=lambda *args, **kwargs: 'authz',
        repeated_consistency_ok_fn=lambda runs, target, objective: True,
        qualify_fn=lambda payload: payload,
        can_be_confirmed_fn=lambda qual: True,
        compute_promising_fn=lambda qual, summary_text, classification: True,
        finding_lifecycle_fn=lambda mode, qual: 'probable',
        adaptive_aggression_fn=lambda aggression, classification, reason_code, owner_override: aggression,
        normalize_pipeline_status_fn=lambda engine_status, auditor_decision, error_flag: engine_status,
        log_event_fn=lambda *args, **kwargs: None,
        run_pipeline_fn=lambda *args, **kwargs: {'ok': True},
    )
    ctx = _build_execute_runtime_context(
        objective='Probe',
        target='https://api.example.com/',
        mode='fast',
        aggression=5,
        owner_auth=False,
        owner_override=False,
        plan_name='Plan',
        run_index=2,
    )
    bundle = _build_runtime_dispatch_stage_inputs(
        task_ctx={'task_family': 'authz'},
        ctx=ctx,
        run_index=2,
        last_heartbeat_ts=0.0,
        runs_count=0,
        followup_queue_len=0,
        precision_queue_len=0,
        deps=deps,
    )
    assert bundle['task_ctx'] == {'task_family': 'authz'}
    assert bundle['objective'] == 'Probe'
    assert bundle['label'] == 'Plan'
    assert bundle['run_pipeline_fn'] == deps.run_pipeline_fn



def test_run_runtime_dispatch_stage_threads_context_into_dispatch(monkeypatch) -> None:
    captured = {}

    def fake_dispatch_runtime_task(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return ({'ok': True}, 123.0)

    monkeypatch.setattr(rte, 'dispatch_runtime_task', fake_dispatch_runtime_task)
    deps = RuntimeExecutionDeps(
        summarize_result_fn=lambda result: ('medium', 'approve', 'ok', 'summary', False),
        post_result_common_fn=lambda **kwargs: kwargs,
        qualify_and_finalize_run_fn=lambda **kwargs: ({}, False, {}),
        inspect_json_signal_from_command_fn=lambda *args, **kwargs: None,
        parse_rc_metrics_fn=lambda *args, **kwargs: {},
        run_control_comparison_fn=lambda *args, **kwargs: {},
        attack_family_fn=lambda *args, **kwargs: 'authz',
        repeated_consistency_ok_fn=lambda runs, target, objective: True,
        qualify_fn=lambda payload: payload,
        can_be_confirmed_fn=lambda qual: True,
        compute_promising_fn=lambda qual, summary_text, classification: True,
        finding_lifecycle_fn=lambda mode, qual: 'probable',
        adaptive_aggression_fn=lambda aggression, classification, reason_code, owner_override: aggression,
        normalize_pipeline_status_fn=lambda engine_status, auditor_decision, error_flag: engine_status,
        log_event_fn=lambda *args, **kwargs: None,
        run_pipeline_fn=lambda *args, **kwargs: {'ok': True},
    )
    ctx = _build_execute_runtime_context(
        objective='Probe',
        target='https://api.example.com/',
        mode='fast',
        aggression=5,
        owner_auth=False,
        owner_override=False,
        plan_name='Plan',
        run_index=2,
    )
    result, hb = _run_runtime_dispatch_stage(
        task_ctx={'task_family': 'authz'},
        ctx=ctx,
        run_index=2,
        last_heartbeat_ts=0.0,
        runs_count=0,
        followup_queue_len=0,
        precision_queue_len=0,
        deps=deps,
    )
    assert result == {'ok': True}
    assert hb == 123.0
    assert captured['objective'] == 'Probe'
    assert captured['target'] == 'https://api.example.com/'
    assert captured['label'] == 'Plan'
    assert captured['log_event_fn'] == deps.log_event_fn
    assert captured['run_pipeline_fn'] == deps.run_pipeline_fn



def test_build_runtime_result_stage_inputs_captures_result_stage_bundle() -> None:
    deps = RuntimeExecutionDeps(
        summarize_result_fn=lambda result: ('medium', 'approve', 'ok', 'summary', False),
        post_result_common_fn=lambda **kwargs: kwargs,
        qualify_and_finalize_run_fn=lambda **kwargs: ({}, False, {}),
        inspect_json_signal_from_command_fn=lambda *args, **kwargs: None,
        parse_rc_metrics_fn=lambda *args, **kwargs: {},
        run_control_comparison_fn=lambda *args, **kwargs: {},
        attack_family_fn=lambda *args, **kwargs: 'authz',
        repeated_consistency_ok_fn=lambda runs, target, objective: True,
        qualify_fn=lambda payload: payload,
        can_be_confirmed_fn=lambda qual: True,
        compute_promising_fn=lambda qual, summary_text, classification: True,
        finding_lifecycle_fn=lambda mode, qual: 'probable',
        adaptive_aggression_fn=lambda aggression, classification, reason_code, owner_override: aggression,
        normalize_pipeline_status_fn=lambda engine_status, auditor_decision, error_flag: engine_status,
        log_event_fn=lambda *args, **kwargs: None,
        run_pipeline_fn=lambda *args, **kwargs: {'ok': True},
    )
    ctx = _build_execute_runtime_context(
        objective='Probe',
        target='https://api.example.com/',
        mode='fast',
        aggression=5,
        owner_auth=False,
        owner_override=False,
        plan_name='Plan',
        run_index=2,
    )
    bundle = _build_runtime_result_stage_inputs(
        task_ctx={'task_family': 'authz'},
        ctx=ctx,
        result={'ok': True},
        run_index=2,
        deps=deps,
        host_family_owner_gate={},
        host_cooldown_until={},
        host_code000_streak={},
        host_code000_total={},
        host_403_streak={},
        host_fail_streak={},
        host_fail_count={},
        host_success_count={},
        code000_streak_threshold=3,
        code000_cooldown_sec=900,
        code000_session_cap=5,
        runs=[],
        toggles={},
        host_weak_count={},
        quality_telemetry={},
        qualification_mode='shadow',
        qualification_promising_threshold='probable',
    )
    assert bundle['ctx'] == ctx
    assert bundle['result'] == {'ok': True}
    assert bundle['run_index'] == 2
    assert bundle['deps'] == deps
    assert bundle['qualification_mode'] == 'shadow'



def test_process_runtime_task_result_composes_post_qualify_and_final_result() -> None:
    captured: dict[str, dict] = {}

    def post_result_common_fn(**kwargs):  # type: ignore[no-untyped-def]
        captured['post'] = dict(kwargs)
        return {'reason_code': 'interesting', 'success_eval_status': 'partial', 'summary_text': 'summary+', 'classification': 'medium', 'run_info': {'engine_status': 'ok', 'auditor_decision': 'approve'}}

    def qualify_and_finalize_run_fn(**kwargs):  # type: ignore[no-untyped-def]
        captured['qualify'] = dict(kwargs)
        return ({'verdict': 'probable'}, True, {'runtime_decision': {'intent_flags': {'followup': True}}, 'decision_intent_flags': {'followup': True}})

    deps = RuntimeExecutionDeps(
        summarize_result_fn=lambda result: ('medium', 'approve', 'ok', 'summary', False),
        post_result_common_fn=post_result_common_fn,
        qualify_and_finalize_run_fn=qualify_and_finalize_run_fn,
        inspect_json_signal_from_command_fn=lambda *args, **kwargs: None,
        parse_rc_metrics_fn=lambda *args, **kwargs: {},
        run_control_comparison_fn=lambda *args, **kwargs: {},
        attack_family_fn=lambda *args, **kwargs: 'authz',
        repeated_consistency_ok_fn=lambda runs, target, objective: True,
        qualify_fn=lambda payload: payload,
        can_be_confirmed_fn=lambda qual: True,
        compute_promising_fn=lambda qual, summary_text, classification: True,
        finding_lifecycle_fn=lambda mode, qual: 'probable',
        adaptive_aggression_fn=lambda aggression, classification, reason_code, owner_override: aggression,
        normalize_pipeline_status_fn=lambda engine_status, auditor_decision, error_flag: engine_status,
        log_event_fn=lambda *args, **kwargs: None,
        run_pipeline_fn=lambda *args, **kwargs: {'ok': True},
    )
    ctx = _build_execute_runtime_context(
        objective='Probe',
        target='https://api.example.com/',
        mode='fast',
        aggression=5,
        owner_auth=False,
        owner_override=False,
        plan_name='Plan',
        run_index=2,
    )
    payload = _process_runtime_task_result(
        task_ctx={'task_family': 'authz'},
        ctx=ctx,
        result={'ok': True},
        run_index=2,
        deps=deps,
        host_family_owner_gate={},
        host_cooldown_until={},
        host_code000_streak={},
        host_code000_total={},
        host_403_streak={},
        host_fail_streak={},
        host_fail_count={},
        host_success_count={},
        code000_streak_threshold=3,
        code000_cooldown_sec=900,
        code000_session_cap=5,
        runs=[],
        toggles={},
        host_weak_count={},
        quality_telemetry={},
        qualification_mode='shadow',
        qualification_promising_threshold='probable',
    )
    assert payload[0] == {'ok': True}
    assert payload[1] == 'medium'
    assert payload[4] == 'summary+'
    assert payload[7] == {'verdict': 'probable'}
    assert payload[8] is True
    assert captured['post']['plan_name'] == 'Plan'
    assert captured['qualify']['decision_label'] == 'Plan'



def test_execute_runtime_task_pipeline_returns_post_and_run_info() -> None:
    captured: dict[str, dict] = {}

    def post_result_common_fn(**kwargs):  # type: ignore[no-untyped-def]
        captured['post'] = dict(kwargs)
        return {'reason_code': 'interesting', 'success_eval_status': 'partial', 'summary_text': 'summary+', 'classification': 'medium', 'run_info': {'engine_status': 'ok', 'auditor_decision': 'approve'}}

    def qualify_and_finalize_run_fn(**kwargs):  # type: ignore[no-untyped-def]
        captured['qualify'] = dict(kwargs)
        return ({'verdict': 'probable'}, True, {'runtime_decision': {'intent_flags': {'followup': True}}, 'decision_intent_flags': {'followup': True}})

    deps = RuntimeExecutionDeps(
        summarize_result_fn=lambda result: ('medium', 'approve', 'ok', 'summary', False),
        post_result_common_fn=post_result_common_fn,
        qualify_and_finalize_run_fn=qualify_and_finalize_run_fn,
        inspect_json_signal_from_command_fn=lambda *args, **kwargs: None,
        parse_rc_metrics_fn=lambda *args, **kwargs: {},
        run_control_comparison_fn=lambda *args, **kwargs: {},
        attack_family_fn=lambda *args, **kwargs: 'authz',
        repeated_consistency_ok_fn=lambda runs, target, objective: True,
        qualify_fn=lambda payload: payload,
        can_be_confirmed_fn=lambda qual: True,
        compute_promising_fn=lambda qual, summary_text, classification: True,
        finding_lifecycle_fn=lambda mode, qual: 'probable',
        adaptive_aggression_fn=lambda aggression, classification, reason_code, owner_override: aggression,
        normalize_pipeline_status_fn=lambda engine_status, auditor_decision, error_flag: engine_status,
        log_event_fn=lambda *args, **kwargs: None,
        run_pipeline_fn=lambda *args, **kwargs: {'ok': True},
    )
    hb, payload = execute_runtime_task_pipeline(
        task_ctx={'task_family': 'authz'},
        objective='Probe',
        target='https://api.example.com/',
        mode='fast',
        aggression=5,
        owner_auth=False,
        owner_override=False,
        plan_name='Plan',
        run_index=2,
        last_heartbeat_ts=0.0,
        runs_count=0,
        followup_queue_len=0,
        precision_queue_len=0,
        deps=deps,
        host_family_owner_gate={},
        host_cooldown_until={},
        host_code000_streak={},
        host_code000_total={},
        host_403_streak={},
        host_fail_streak={},
        host_fail_count={},
        host_success_count={},
        code000_streak_threshold=3,
        code000_cooldown_sec=900,
        code000_session_cap=5,
        runs=[],
        toggles={},
        host_weak_count={},
        quality_telemetry={},
        qualification_mode='shadow',
        qualification_promising_threshold='probable',
    )

    result, classification, auditor, engine_status, summary_text, error_flag, post, qual, promising, run_info = payload
    assert hb > 0
    assert result == {'ok': True}
    assert classification == 'medium'
    assert auditor == 'approve'
    assert engine_status == 'ok'
    assert summary_text == 'summary+'
    assert error_flag is False
    assert post['reason_code'] == 'interesting'
    assert qual['verdict'] == 'probable'
    assert promising is True
    assert 'runtime_decision' in run_info
    assert captured['post']['plan_name'] == 'Plan'
    assert captured['post']['objective'] == 'Probe'
    assert captured['qualify']['decision_label'] == 'Plan'
    assert captured['qualify']['mode'] == 'fast'
