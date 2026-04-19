from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_runner_bootstrap_loader as rrbl  # type: ignore


class FakeRuntimeSessionBootstrap:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def test_load_runtime_session_bootstrap_normalizes_retry_policy_and_dns_cache() -> None:
    out = rrbl.load_runtime_session_bootstrap(
        runtime_session_bootstrap_cls=FakeRuntimeSessionBootstrap,
        load_existing_runs_fn=lambda: [{'objective': 'Probe', 'target': 'https://api.example.com/'}],
        load_host_state_fn=lambda: {'api.example.com': {'ok': True}},
        dedup_key_fn=lambda objective, target: (objective, target),
        current_campaign_key_fn=lambda: 'abc123',
        campaign_settings_for_key_fn=lambda key: {'max_runs': 12, 'target_load_limit': 20, 'time_budget_min': 15, 'retry_policy': 'weird'},
        load_curated_plan_fn=lambda: [{'target': 'https://api.example.com/'}],
        load_runtime_plan_meta_fn=lambda: {'plan_revision': 4},
        host_from_target_fn=lambda target: 'api.example.com',
        is_resolvable_host_fn=lambda host: True,
        load_runtime_toggles_fn=lambda **kwargs: {'x': True},
        pipeline_config_path=Path('engine/pipeline_config.json'),
        normalize_pipeline_flags_fn=lambda payload: payload,
        warn_fn=lambda message: None,
        load_planner_hints_fn=lambda: {'fresh': True},
        load_queue_state_fn=lambda: {'followup_queue': [{'kind': 'followup'}], 'precision_queue': [{'kind': 'precision'}]},
    )
    assert out.retry_policy == 'balanced'
    assert out.retry_limit == 1
    assert out.host_dns_cache == {'api.example.com': True}
    assert out.followup_queue == [{'kind': 'followup'}]


def test_load_runtime_session_bootstrap_uses_toggles_fallback_without_kwargs() -> None:
    calls = {'typed': 0, 'fallback': 0}

    def fake_load_runtime_toggles(**kwargs):  # type: ignore[no-untyped-def]
        if kwargs:
            calls['typed'] += 1
            raise TypeError('no kwargs')
        calls['fallback'] += 1
        return {'fallback': True}

    out = rrbl.load_runtime_session_bootstrap(
        runtime_session_bootstrap_cls=FakeRuntimeSessionBootstrap,
        load_existing_runs_fn=lambda: [],
        load_host_state_fn=lambda: {},
        dedup_key_fn=lambda objective, target: (objective, target),
        current_campaign_key_fn=lambda: 'abc123',
        campaign_settings_for_key_fn=lambda key: {},
        load_curated_plan_fn=lambda: [],
        load_runtime_plan_meta_fn=lambda: {},
        host_from_target_fn=lambda target: '',
        is_resolvable_host_fn=lambda host: False,
        load_runtime_toggles_fn=fake_load_runtime_toggles,
        pipeline_config_path=Path('engine/pipeline_config.json'),
        normalize_pipeline_flags_fn=lambda payload: payload,
        warn_fn=lambda message: None,
        load_planner_hints_fn=lambda: {},
        load_queue_state_fn=lambda: {},
    )
    assert out.toggles == {'fallback': True}
    assert calls == {'typed': 1, 'fallback': 1}
