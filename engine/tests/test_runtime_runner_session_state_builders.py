from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_runner_session_state_builders as rrsb  # type: ignore


class FakeRuntimeSessionState:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def test_build_runtime_session_state_from_bootstrap_sets_plan_fields() -> None:
    now = datetime.now(timezone.utc)
    state = rrsb.build_runtime_session_state_from_bootstrap(
        runtime_session_state_cls=FakeRuntimeSessionState,
        bootstrap=SimpleNamespace(
            runs=[{'objective': 'Probe', 'target': 'https://api.example.com/', 'promising': True}],
            history=[{'objective': 'Probe', 'target': 'https://api.example.com/', 'promising': True}],
            host_state={'api.example.com': {'ok': True}},
            executed_keys={('Probe', 'https://api.example.com/')},
            runtime_plan_meta={'plan_revision': 4, 'plan_hash': 'abc'},
            curated_plan=[{'target': 'https://api.example.com/'}],
            host_dns_cache={'api.example.com': True},
            toggles={'x': True},
            planner_hints_cache={'hints': []},
            followup_queue=[{'a': 1}],
            precision_queue=[{'b': 2}],
        ),
    )
    assert state.active_plan_revision == 4
    assert state.active_plan_hash == 'abc'
    assert state.scheduled_keys == {('Probe', 'https://api.example.com/')}
    assert state.promising_hits_ref == [1]
    assert state.idx == 1


def test_build_runtime_session_state_handles_invalid_campaign() -> None:
    out = rrsb.build_runtime_session_state(
        reports_dir=Path('reports'),
        validate_campaign_fn=lambda path: {'ok': False, 'reason': 'bad'},
        selected_scope_path_fn=lambda: Path('scope.txt'),
        runtime_session_state_cls=FakeRuntimeSessionState,
        load_runtime_session_bootstrap_fn=lambda: None,
        build_runtime_session_state_from_bootstrap_fn=lambda **kwargs: None,
    )
    assert out[0] == {'ok': False, 'reason': 'bad'}
    assert out[2].tzinfo is not None
    assert out[3:] == (0, 0, 0, 'balanced', 0)
