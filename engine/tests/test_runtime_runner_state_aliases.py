from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_runner_state_aliases as rrsa  # type: ignore


def test_build_main_state_aliases_preserves_refs_and_normalizes_scalars() -> None:
    state = SimpleNamespace(
        followup_queue=[{'kind': 'followup'}],
        host_rr={'api.example.com': 1},
        followup_counts={'api.example.com': 2},
        confirm_counts={'api.example.com': 3},
        confirm_recent={'api.example.com': 4.0},
        confirm_class_counts={'high': 1},
        confirm_total='5',
        quality_telemetry={'probable': 1},
        scheduled_keys={('Probe', 'https://api.example.com/')},
        retry_counts={'api.example.com': 1},
        precheck_skip_count='6',
        followup_recent={'api.example.com': 7.0},
        precheck_skip_examples=['skip'],
        unresolved_hosts={'api.example.com'},
        dns_skip_count={'api.example.com': 1},
        execution_gate_skip_count={'api.example.com': 2},
        execution_gate_skip_examples={'api.example.com': ['gate']},
        host_cooldown_until={'api.example.com': 9.0},
        host_cooldown_skip_count={'api.example.com': 3},
        precision_queue=[{'kind': 'precision'}],
        deep_budget={'api.example.com': {'used': 1}},
        host_fail_streak={'api.example.com': 1},
        host_success_count={'api.example.com': 2},
        host_fail_count={'api.example.com': 3},
        host_weak_count={'api.example.com': 4},
        host_family_owner_gate={'api.example.com': {'authz': True}},
        host_code000_streak={'api.example.com': 1},
        host_code000_total={'api.example.com': 2},
        host_403_streak={'api.example.com': 3},
        host_precheck_burst={'api.example.com': 4},
        last_persist_ts='55.5',
    )
    out = rrsa.build_main_state_aliases(state)
    assert out.followup_queue is state.followup_queue
    assert out.confirm_total == 5
    assert out.precheck_skip_count == 6
    assert out.last_persist_ts == 55.5


def test_make_skip_summary_flusher_delegates() -> None:
    captured = {}

    def fake_flush_skip_summaries(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)

    flusher = rrsa.make_skip_summary_flusher(
        flush_skip_summaries_fn=fake_flush_skip_summaries,
        log_event_fn=lambda *args, **kwargs: None,
        precheck_skip_count_ref=[1],
        precheck_skip_examples_ref=['skip'],
        dns_skip_count_ref={'api.example.com': 1},
        host_cooldown_skip_count_ref={'api.example.com': 2},
        execution_gate_skip_count_ref={'api.example.com': 3},
        execution_gate_skip_examples_ref={'api.example.com': ['gate']},
    )
    flusher(True)
    assert captured['force'] is True
    assert captured['precheck_skip_count_ref'] == [1]


def test_build_main_skip_summary_flushers_wires_each_summary_bucket() -> None:
    events = []

    def fake_make_skip_summary_flusher(**kwargs):  # type: ignore[no-untyped-def]
        bucket = kwargs
        def flush(force: bool = False) -> None:
            events.append((bucket, force))
        return flush

    out = rrsa.build_main_skip_summary_flushers(
        make_skip_summary_flusher_fn=fake_make_skip_summary_flusher,
        precheck_skip_count_ref=[5],
        precheck_skip_examples=['skip'],
        dns_skip_count={'api.example.com': 1},
        host_cooldown_skip_count={'api.example.com': 2},
        execution_gate_skip_count={'api.example.com': 3},
        execution_gate_skip_examples={'api.example.com': ['gate']},
    )
    out['flush_precheck_summary']()
    out['flush_dns_skip_summary']()
    out['flush_host_cooldown_summary']()
    out['flush_execution_gate_summary']()
    assert len(events) == 4
