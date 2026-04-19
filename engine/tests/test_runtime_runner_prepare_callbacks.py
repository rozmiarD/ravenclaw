from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_runner_prepare_callbacks as rrpc  # type: ignore


class FakePrecheckContext:
    def __init__(self) -> None:
        self.calls = []

    def prepare_task_precheck(self, **kwargs):  # type: ignore[no-untyped-def]
        self.calls.append(kwargs)
        return {'prepared': kwargs['target']}


class FakeState:
    def __init__(self) -> None:
        self.followup_queue = [{'kind': 'followup'}]
        self.precision_queue = [{'kind': 'precision'}]
        self.runs = [{'objective': 'Probe', 'target': 'https://api.example.com/'}]
        self.host_state = {'api.example.com': {'ok': True}}
        self.host_family_owner_gate = {'api.example.com': {'authz': True}}



def test_prepare_task_precheck_from_context_normalizes_inputs() -> None:
    precheck_ctx = FakePrecheckContext()
    out = rrpc.prepare_task_precheck_from_context(
        precheck_ctx,
        objective='Probe',
        target='https://api.example.com/',
        mode='fast',
        task_family='authz',
        dedup_mode_suffix=True,
        runtime_task=None,
    )
    assert out == {'prepared': 'https://api.example.com/'}
    assert precheck_ctx.calls[0]['objective'] == 'Probe'
    assert precheck_ctx.calls[0]['task_family'] == 'authz'
    assert precheck_ctx.calls[0]['runtime_task'] == {}



def test_build_main_prepare_callbacks_exposes_expected_callbacks() -> None:
    state = FakeState()
    precheck_ctx = FakePrecheckContext()
    callbacks = rrpc.build_main_prepare_callbacks(
        precheck_ctx=precheck_ctx,
        scheduled_keys={('Probe', 'https://api.example.com/')},
        toggles={'queue': True},
        state=state,
        planner_hints_cache_ref=[{'fresh': True}],
        attack_family_fn=lambda objective, target, family: family or 'generic',
        prepare_curated_task_fn=lambda entry, **kwargs: {'kind': 'curated'},
        prepare_runtime_task_fn=lambda task, **kwargs: {'kind': 'runtime'},
        capped_aggression_fn=lambda family, target, requested: requested,
        family_allowed_for_host_stage_fn=lambda *args, **kwargs: True,
        planner_vector_weight_fn=lambda task, planner_hints: 1.0,
        host_from_target_fn=lambda target: 'api.example.com',
        apply_queue_reprioritization_fn=lambda **kwargs: None,
    )
    assert set(callbacks.keys()) == {'prepare_task_precheck', 'prepare_curated_task', 'prepare_runtime_task', 'reprioritize_queues'}
    assert callable(callbacks['prepare_task_precheck'])
    assert callable(callbacks['prepare_curated_task'])
    assert callable(callbacks['prepare_runtime_task'])
    assert callable(callbacks['reprioritize_queues'])
