from __future__ import annotations

import json
import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import learning_store
from runtime_runner_bootstrap import (  # type: ignore
    current_scope_summary,
    current_scope_targets,
    load_openclaw_env,
    load_runtime_toggles,
    maybe_reconsult_planner,
    selected_scope_path,
)


def test_selected_scope_path_prefers_ui_relative_path(tmp_path: Path) -> None:
    scope_dir = tmp_path / 'scope'
    scope_dir.mkdir()
    scope_file = scope_dir / 'scope.txt'
    scope_file.write_text('example.com\n', encoding='utf-8')

    out = selected_scope_path(
        load_planner_ui_state_fn=lambda: {'scope_txt': 'scope/scope.txt'},
        wp_fn=lambda *parts: tmp_path.joinpath(*parts),
    )
    assert out == scope_file


def test_current_scope_targets_prefers_domains_and_falls_back() -> None:
    out = current_scope_targets(
        load_scope_domains_fn=lambda: {'exact': ['api.example.com'], 'suffix': ['example.org']},
        load_scope_targets_fn=lambda: [{'name': 'ignored.example.net'}],
    )
    assert out == ['*.example.org', 'api.example.com']

    fallback = current_scope_targets(
        load_scope_domains_fn=lambda: (_ for _ in ()).throw(RuntimeError('boom')),
        load_scope_targets_fn=lambda: [{'name': 'one.example.com'}, {'name': ''}, {'name': 'two.example.com'}],
    )
    assert fallback == ['one.example.com', 'two.example.com']


def test_current_scope_summary_uses_targets_first() -> None:
    assert current_scope_summary(current_scope_targets_fn=lambda: ['a.example.com', 'b.example.com'], summarize_scope_fn=lambda: 'fallback') == 'a.example.com, b.example.com'
    assert current_scope_summary(current_scope_targets_fn=lambda: [], summarize_scope_fn=lambda: 'fallback') == 'fallback'


def test_load_openclaw_env_merges_defaults_without_overwriting_existing(tmp_path: Path) -> None:
    env_file = tmp_path / '.env'
    env_file.write_text('A=1\nB=2\n', encoding='utf-8')
    out = load_openclaw_env(environ={'B': 'existing', 'C': '3'}, env_path=env_file)
    assert out['A'] == '1'
    assert out['B'] == 'existing'
    assert out['C'] == '3'


def test_load_runtime_toggles_normalizes_profile_style_fields(tmp_path: Path) -> None:
    config_path = tmp_path / 'pipeline_config.json'
    config_path.write_text(json.dumps({
        'plan_adaptation_mode': 'aggressive',
        'aggressive_adaptation': False,
        'confirm_jobs_profile': 'aggressive',
        'max_confirm_jobs_per_target': 1,
        'confirm_job_cooldown_sec': 900,
        'workflow_escalation_profile': 'aggressive',
        'max_followups_per_target': 1,
    }), encoding='utf-8')

    out = load_runtime_toggles(pipeline_config_path=config_path)
    assert out['plan_adaptation_mode'] == 'aggressive'
    assert out['aggressive_adaptation'] is True
    assert out['freeze_plan_revision'] is False
    assert out['confirm_jobs_profile'] == 'aggressive'
    assert out['max_confirm_jobs_per_target'] == 2
    assert out['confirm_job_cooldown_sec'] == 300
    assert out['workflow_escalation_profile'] == 'aggressive'
    assert out['enable_followups'] is True
    assert out['safe_dual_action_enabled'] is True
    assert out['max_followups_per_target'] == 4


def test_maybe_reconsult_planner_uses_progression_priors_for_structural_tier(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(learning_store, 'LEARNING_PATH', tmp_path / 'learning_store.json')
    learning_store.update_learning(
        'api.example.com',
        'authz',
        'medium',
        True,
        'ok',
        next_stage='bounded_exploit_proof',
        next_family='authz',
        reconsult_tier='structural',
        target_type='api',
        target_surface_rationale=['authenticated_or_boundary_mapping'],
    )
    tier = maybe_reconsult_planner(
        {'planner_reconsult_on_high_signal': True, 'planner_reconsult_min_interval_runs': 2, 'planner_reconsult_signal_threshold': 3},
        runs=[{'a': 1}, {'b': 2}],
        promising_count=0,
        host_state=None,
        summarize_planner_feedback_fn=lambda **_kwargs: {
            'reconsult_worthy_recent': 0,
            'adaptation_positive_recent': 0,
            'recent_next_family_hints': ['authz'],
            'recent_next_stage_hints': ['bounded_exploit_proof'],
            'recent_target_surface_rationale': ['authenticated_or_boundary_mapping'],
            'degraded_hosts': 0,
            'planner_override_recent': 0,
            'high_redundancy_recent': 0,
            'not_met_recent': 0,
        },
    )
    assert tier == 'structural'



def test_maybe_reconsult_planner_uses_stage_and_surface_hints() -> None:
    tier = maybe_reconsult_planner(
        {'planner_reconsult_on_high_signal': True, 'planner_reconsult_min_interval_runs': 2, 'planner_reconsult_signal_threshold': 2},
        runs=[{'a': 1}, {'b': 2}],
        promising_count=1,
        host_state=None,
        summarize_planner_feedback_fn=lambda **_kwargs: {
            'reconsult_worthy_recent': 0,
            'adaptation_positive_recent': 0,
            'recent_next_stage_hints': ['bounded_exploit_proof', 'bounded_exploit_proof'],
            'recent_target_surface_rationale': ['authenticated_or_boundary_mapping', 'authenticated_or_boundary_mapping'],
            'degraded_hosts': 0,
            'planner_override_recent': 0,
            'high_redundancy_recent': 0,
            'not_met_recent': 0,
            'dead_end_pressure_recent': 0.0,
        },
    )
    assert tier == 'structural'


def test_maybe_reconsult_planner_downgrades_structural_when_dead_end_pressure_is_high() -> None:
    tier = maybe_reconsult_planner(
        {'planner_reconsult_on_high_signal': True, 'planner_reconsult_min_interval_runs': 2, 'planner_reconsult_signal_threshold': 2},
        runs=[{'a': 1}, {'b': 2}],
        promising_count=4,
        host_state=None,
        summarize_planner_feedback_fn=lambda **_kwargs: {
            'reconsult_worthy_recent': 4,
            'adaptation_positive_recent': 1,
            'recent_next_stage_hints': ['bounded_exploit_proof', 'bounded_exploit_proof'],
            'recent_target_surface_rationale': ['authenticated_or_boundary_mapping', 'authenticated_or_boundary_mapping'],
            'degraded_hosts': 0,
            'planner_override_recent': 0,
            'high_redundancy_recent': 0,
            'not_met_recent': 0,
            'dead_end_pressure_recent': 0.8,
            'branch_quality_rate_recent': 0.2,
            'recon_conversion_rate_recent': 0.0,
        },
    )
    assert tier == 'light'


def test_maybe_reconsult_planner_upgrades_to_structural_on_good_quality_metrics() -> None:
    tier = maybe_reconsult_planner(
        {'planner_reconsult_on_high_signal': True, 'planner_reconsult_min_interval_runs': 2, 'planner_reconsult_signal_threshold': 3},
        runs=[{'a': 1}, {'b': 2}],
        promising_count=0,
        host_state=None,
        summarize_planner_feedback_fn=lambda **_kwargs: {
            'reconsult_worthy_recent': 2,
            'adaptation_positive_recent': 2,
            'recent_next_stage_hints': [],
            'recent_target_surface_rationale': [],
            'recent_next_family_hints': [],
            'degraded_hosts': 0,
            'planner_override_recent': 0,
            'high_redundancy_recent': 0,
            'not_met_recent': 0,
            'dead_end_pressure_recent': 0.1,
            'branch_quality_rate_recent': 0.8,
            'recon_conversion_rate_recent': 0.5,
            'adaptive_quality': {'dead_end_heavy': False, 'quality_structural': True},
        },
    )
    assert tier == 'structural'
