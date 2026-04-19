from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from runtime_orchestrator import build_deduped_target_plan, build_execute_runtime_request, maybe_preempt_curated_entry, prepare_curated_task, prepare_runtime_task, resolve_main_loop_candidate, unpack_queued_task  # type: ignore


def test_build_deduped_target_plan_removes_duplicate_objective_target_pairs() -> None:
    raw_plan = [
        {'objective': 'Recon', 'target': 'https://a.example.com/'},
        {'objective': 'Recon', 'target': 'https://a.example.com/'},
        {'objective': 'Probe', 'target': 'https://b.example.com/'},
    ]
    result = build_deduped_target_plan(raw_plan, lambda objective, target: (objective, target))
    assert len(result) == 2
    assert result[0]['target'] == 'https://a.example.com/'
    assert result[1]['target'] == 'https://b.example.com/'


def test_maybe_preempt_curated_entry_returns_queue_task_when_preemption_enabled() -> None:
    entry = {'objective': 'Recon', 'target': 'https://curated.example.com/'}
    queue_task = {'objective': 'Follow-up', 'target': 'https://queued.example.com/'}
    selected, preempted = maybe_preempt_curated_entry(
        entry,
        preempt_in_curated=True,
        has_precision_queue=True,
        has_followup_queue=False,
        dequeue_task_fn=lambda: queue_task,
    )
    assert preempted is True
    assert selected == queue_task


def test_prepare_curated_task_threads_execution_gate() -> None:
    prepared = prepare_curated_task(
        {'objective': 'Recon', 'target': 'https://a.example.com/', 'task_family': 'recon', 'aggression': 6},
        aggression_override_global=None,
        prepare_task_precheck_fn=lambda **_kwargs: {'allowed': True, 'gate': {'reason_code': 'allowed', 'family': 'recon'}},
        clamp_aggression_fn=lambda n: min(10, max(1, n)),
        capped_aggression_fn=lambda family, target, aggression: aggression,
    )
    assert prepared is not None
    assert prepared['task_ctx']['execution_gate']['reason_code'] == 'allowed'
    assert prepared['target'] == 'https://a.example.com/'


def test_unpack_queued_task_applies_override_and_caps() -> None:
    queued = unpack_queued_task(
        {'objective': 'Probe', 'target': 'https://b.example.com/', 'task_family': 'authz', 'aggression': 8, 'mode': 'followup', 'owner_approved_auth': True},
        aggression_override_global=4,
        clamp_aggression_fn=lambda n: min(10, max(1, n)),
        capped_aggression_fn=lambda family, target, aggression: aggression - 1,
        owner_override_global=True,
    )
    assert queued['aggression'] == 3
    assert queued['owner_auth'] is True
    assert queued['owner_override'] is True
    assert queued['mode'] == 'followup'


def test_prepare_runtime_task_adds_scheduled_key_and_gate() -> None:
    scheduled_keys = set()
    prepared = prepare_runtime_task(
        {'task_family': 'authz'},
        objective='Probe',
        target='https://b.example.com/',
        mode='followup',
        aggression=5,
        owner_auth=False,
        owner_override=False,
        plan_name='Queued',
        prepare_task_precheck_fn=lambda **_kwargs: {'allowed': True, 'key': ('k', 'Probe', 'https://b.example.com/'), 'gate': {'reason_code': 'allowed', 'family': 'authz'}},
        scheduled_keys=scheduled_keys,
        attack_family_fn=lambda objective, target, family: family or 'generic',
    )
    assert prepared is not None
    assert ('k', 'Probe', 'https://b.example.com/') in scheduled_keys
    assert prepared['task_ctx']['execution_gate']['family'] == 'authz'


def test_prepare_runtime_task_threads_runtime_task_into_precheck() -> None:
    scheduled_keys = set()
    captured = {}

    def fake_precheck(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return {'allowed': True, 'key': ('k', 'Probe', 'https://b.example.com/'), 'gate': {'reason_code': 'allowed', 'family': 'authz'}}

    prepared = prepare_runtime_task(
        {'task_family': 'authz', 'runtime_task': {'activation_phase': 2, 'conditional_gate': 'authenticated_or_boundary_mapping'}},
        objective='Probe',
        target='https://b.example.com/',
        mode='followup',
        aggression=5,
        owner_auth=False,
        owner_override=False,
        plan_name='Queued',
        prepare_task_precheck_fn=fake_precheck,
        scheduled_keys=scheduled_keys,
        attack_family_fn=lambda objective, target, family: family or 'generic',
    )
    assert prepared is not None
    assert captured['runtime_task'] == {'activation_phase': 2, 'conditional_gate': 'authenticated_or_boundary_mapping'}


def test_build_execute_runtime_request_bridges_prepared_task_to_execution_call() -> None:
    request = build_execute_runtime_request(
        {
            'task_ctx': {'task_family': 'authz'},
            'objective': 'Probe',
            'target': 'https://b.example.com/',
            'mode': 'followup',
            'aggression': 5,
            'owner_auth': False,
            'owner_override': True,
            'plan_name': 'Queued',
        },
        run_index=3,
        last_heartbeat_ts=12.5,
        confirm_total=4,
    )
    assert request['task_ctx']['task_family'] == 'authz'
    assert request['objective'] == 'Probe'
    assert request['target'] == 'https://b.example.com/'
    assert request['mode'] == 'followup'
    assert request['aggression'] == 5
    assert request['owner_override'] is True
    assert request['plan_name'] == 'Queued'
    assert request['run_index'] == 3
    assert request['last_heartbeat_ts'] == 12.5
    assert request['confirm_total'] == 4


def test_resolve_main_loop_candidate_prefers_queue_task() -> None:
    selected = resolve_main_loop_candidate(
        task={'objective': 'Queued', 'target': 'https://queued.example.com/', 'task_family': 'recon'},
        history=[],
        scope_targets=['queued.example.com'],
        runs_count=0,
        owner_override_global=False,
        aggression_override_global=None,
        normalize_runtime_task_fn=lambda task: dict(task, normalized=True),
        unpack_queued_task_fn=lambda task, **_kwargs: {'task': task, 'objective': task['objective'], 'target': task['target'], 'aggression': 5, 'mode': 'followup', 'owner_auth': False, 'owner_override': False, 'plan_name': 'Queued'},
        clamp_aggression_fn=lambda n: n,
        capped_aggression_fn=lambda family, target, aggression: aggression,
        propose_next_vector_fn=lambda history: ('Brain', 'https://brain.example.com/'),
        log_failure_fn=lambda _msg: None,
        log_fallback_fn=lambda _objective, _target: None,
    )
    assert selected['status'] == 'ok'
    assert selected['source'] == 'queue'
    assert selected['objective'] == 'Queued'


def test_resolve_main_loop_candidate_uses_fallback_when_brain_fails() -> None:
    events = []
    selected = resolve_main_loop_candidate(
        task=None,
        history=[],
        scope_targets=['fallback.example.com'],
        runs_count=0,
        owner_override_global=False,
        aggression_override_global=None,
        normalize_runtime_task_fn=lambda task: task,
        unpack_queued_task_fn=lambda task, **_kwargs: task,
        clamp_aggression_fn=lambda n: n,
        capped_aggression_fn=lambda family, target, aggression: aggression,
        propose_next_vector_fn=lambda history: (_ for _ in ()).throw(RuntimeError('boom')),
        log_failure_fn=lambda msg: events.append(('fail', msg)),
        log_fallback_fn=lambda objective, target: events.append(('fallback', f'{objective}|{target}')),
    )
    assert selected['status'] == 'ok'
    assert selected['source'] == 'fallback'
    assert selected['target'] == 'https://fallback.example.com/'
    assert any(kind == 'fail' for kind, _msg in events)
    assert any(kind == 'fallback' for kind, _msg in events)


def test_resolve_main_loop_candidate_returns_fatal_without_scope_targets() -> None:
    selected = resolve_main_loop_candidate(
        task=None,
        history=[],
        scope_targets=[],
        runs_count=0,
        owner_override_global=False,
        aggression_override_global=None,
        normalize_runtime_task_fn=lambda task: task,
        unpack_queued_task_fn=lambda task, **_kwargs: task,
        clamp_aggression_fn=lambda n: n,
        capped_aggression_fn=lambda family, target, aggression: aggression,
        propose_next_vector_fn=lambda history: (_ for _ in ()).throw(RuntimeError('boom')),
        log_failure_fn=lambda _msg: None,
        log_fallback_fn=lambda _objective, _target: None,
    )
    assert selected['status'] == 'fatal'
    assert 'brain_proposal_failed' in selected['error_msg']
