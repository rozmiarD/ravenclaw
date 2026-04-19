from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_runner_prepare_callbacks_wrapper as rrpcw  # type: ignore


def test_build_main_prepare_callbacks_delegates() -> None:
    captured = {}

    def fake_build_main_prepare_callbacks(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return {'reprioritize_queues': lambda: None}

    out = rrpcw.build_main_prepare_callbacks(
        build_main_prepare_callbacks_fn=fake_build_main_prepare_callbacks,
        precheck_ctx=object(),
        scheduled_keys=set(),
        toggles={},
        state=object(),
        planner_hints_cache_ref=[{}],
        attack_family_fn=lambda *args: 'x',
        prepare_curated_task_fn=lambda *args, **kwargs: None,
        prepare_runtime_task_fn=lambda *args, **kwargs: None,
        capped_aggression_fn=lambda *args, **kwargs: 3,
        family_allowed_for_host_stage_fn=lambda *args, **kwargs: True,
        planner_vector_weight_fn=lambda *args, **kwargs: 1.0,
        host_from_target_fn=lambda target: 'example.com',
        apply_queue_reprioritization_fn=lambda **kwargs: None,
    )
    assert 'reprioritize_queues' in out
    assert callable(captured['attack_family_fn'])
