from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_runner_session_setup as rrss  # type: ignore


def test_build_main_session_base_fields_wraps_state_refs() -> None:
    state = SimpleNamespace(
        runs=[{'objective': 'Probe'}],
        host_state={'api.example.com': {'ok': True}},
        executed_keys={'dedup:1'},
        curated_plan=[{'target': 'https://api.example.com/'}],
        active_plan_revision=3,
        active_plan_hash='abc123',
        host_dns_cache={'api.example.com': True},
        toggles={'qualification_mode': 'shadow'},
        planner_hints_cache={'foo': 'bar'},
        last_regen_run_index=8,
    )
    out = rrss.build_main_session_base_fields(state)
    assert out.runs == state.runs
    assert out.host_state == state.host_state
    assert out.executed_keys is state.executed_keys
    assert out.curated_plan_ref == [state.curated_plan]
    assert out.active_plan_revision_ref == [3]
    assert out.active_plan_hash_ref == ['abc123']
    assert out.host_dns_cache == {'api.example.com': True}
    assert out.toggles is state.toggles
    assert out.planner_hints_cache_ref == [{'foo': 'bar'}]
    assert out.last_regen_run_index_ref == [8]


def test_build_main_session_alias_fields_wraps_aliases_and_queue_coordinator() -> None:
    aliases = SimpleNamespace(
        followup_queue=[{'kind': 'followup'}],
        followup_counts={'api.example.com': 1},
        confirm_counts={'api.example.com': 2},
        confirm_recent={'api.example.com': 3},
        confirm_class_counts={'authz': 4},
        confirm_total=5,
        quality_telemetry={'branch_quality_rate_recent': 0.5},
        scheduled_keys={'dedup:1'},
        retry_counts={'api.example.com': 1},
        precheck_skip_count=5,
        followup_recent={'api.example.com': 6},
        precheck_skip_examples=['skip'],
        unresolved_hosts={'api.example.com'},
        dns_skip_count={'api.example.com': 1},
        execution_gate_skip_count={'api.example.com': 2},
        execution_gate_skip_examples={'api.example.com': ['gate']},
        host_cooldown_until={'api.example.com': 999.0},
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
        last_persist_ts=55.5,
    )
    queue_coordinator = SimpleNamespace(followup_queue=aliases.followup_queue, precision_queue=aliases.precision_queue)
    out = rrss.build_main_session_alias_fields(state_aliases=aliases, queue_coordinator=queue_coordinator)
    assert out.followup_queue is aliases.followup_queue
    assert out.confirm_total == 5
    assert out.queue_coordinator is queue_coordinator
    assert out.precheck_skip_count_ref == [5]
    assert out.last_persist_ts_ref == [55.5]


def test_build_main_session_setup_compacts_state_controls_and_queue_context() -> None:
    state = SimpleNamespace(
        runs=[{'objective': 'Probe'}],
        host_state={'api.example.com': {'ok': True}},
        executed_keys={'dedup:1'},
        curated_plan=[{'target': 'https://api.example.com/'}],
        active_plan_revision=3,
        active_plan_hash='abc123',
        host_dns_cache={'api.example.com': True},
        toggles={'qualification_mode': 'shadow'},
        planner_hints_cache={'foo': 'bar'},
        last_regen_run_index=8,
    )
    aliases = SimpleNamespace(
        followup_queue=[{'kind': 'followup'}],
        host_rr={'api.example.com': 0},
        followup_counts={'api.example.com': 1},
        confirm_counts={'api.example.com': 2},
        confirm_recent={'api.example.com': 3},
        confirm_class_counts={'authz': 4},
        confirm_total=5,
        quality_telemetry={'branch_quality_rate_recent': 0.5},
        scheduled_keys={'dedup:1'},
        retry_counts={'api.example.com': 1},
        precheck_skip_count=5,
        followup_recent={'api.example.com': 6},
        precheck_skip_examples=['skip'],
        unresolved_hosts={'api.example.com'},
        dns_skip_count={'api.example.com': 1},
        execution_gate_skip_count={'api.example.com': 2},
        execution_gate_skip_examples={'api.example.com': ['gate']},
        host_cooldown_until={'api.example.com': 999.0},
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
        last_persist_ts=55.5,
    )

    out = rrss.build_main_session_setup(
        state=state,
        build_main_runtime_controls_fn=lambda toggles: SimpleNamespace(
            code000_streak_threshold=4,
            code000_session_cap=6,
            code000_cooldown_sec=1200,
            autodiscover_deep_skip=False,
            max_followups_per_target=5,
            qualification_mode='shadow',
            qualification_promising_threshold='confirmed',
            max_confirm_jobs_per_target=3,
            confirm_job_cooldown_sec=60,
            max_confirm_jobs_total=9,
            max_confirm_jobs_per_class=7,
        ),
        build_main_state_aliases_fn=lambda state: aliases,
        build_queue_coordinator_fn=lambda **kwargs: SimpleNamespace(**kwargs),
    )

    assert out.runs == state.runs
    assert out.host_state == state.host_state
    assert out.executed_keys is state.executed_keys
    assert out.curated_plan_ref == [state.curated_plan]
    assert out.active_plan_revision_ref == [state.active_plan_revision]
    assert out.active_plan_hash_ref == [state.active_plan_hash]
    assert out.host_dns_cache == {'api.example.com': True}
    assert out.toggles is state.toggles
    assert out.planner_hints_cache_ref == [state.planner_hints_cache]
    assert out.last_regen_run_index_ref == [state.last_regen_run_index]
    assert out.code000_streak_threshold == 4
    assert out.code000_session_cap == 6
    assert out.code000_cooldown_sec == 1200
    assert out.autodiscover_deep_skip is False
    assert out.max_followups_per_target == 5
    assert out.qualification_mode == 'shadow'
    assert out.qualification_promising_threshold == 'confirmed'
    assert out.max_confirm_jobs_per_target == 3
    assert out.confirm_job_cooldown_sec == 60
    assert out.max_confirm_jobs_total == 9
    assert out.max_confirm_jobs_per_class == 7
    assert out.followup_queue is aliases.followup_queue
    assert out.queue_coordinator.followup_queue is aliases.followup_queue
    assert out.queue_coordinator.precision_queue is aliases.precision_queue
    assert out.precheck_skip_count_ref == [5]
    assert out.last_persist_ts_ref == [55.5]
