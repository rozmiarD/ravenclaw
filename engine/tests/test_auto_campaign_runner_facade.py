from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import auto_campaign_runner as acr  # type: ignore


def test_extend_run_pipeline_contract_args_adds_only_present_contract_fields() -> None:
    cmd = ["python3", acr.RUN_PIPE, "--objective", "Probe", "--target", "https://api.example.com/"]
    acr._extend_run_pipeline_contract_args(
        cmd,
        success_criteria="collect evidence",
        task_family="authz",
        success_semantics_json='{"success_model":"differential_or_stateful_signal"}',
        experiment_intent_id="intent-123",
        capability_candidates_json='["http_probe"]',
        planner_constraints_json='{"campaign_bound_context":true}',
        open_questions_json='["tenant edge"]',
        planner_rationale_json='{"target_surface_rationale":["authenticated_or_boundary_mapping"]}',
        planning_ladder_json='{"current_stage":"control_boundary_confirmation"}',
        target_surface_rationale_json='["authenticated_or_boundary_mapping"]',
        recommended_progression_json='["control_boundary_confirmation"]',
        semantic_lineage_json='{"lineage_sha256":"abc"}',
        semantic_lineage_summary_json='{"summary":"boundary-confirmation"}',
    )
    assert "--task-success-criteria" in cmd
    assert "collect evidence" in cmd
    assert "--task-family" in cmd
    assert "authz" in cmd
    assert "--success-semantics-json" in cmd
    assert '{"success_model":"differential_or_stateful_signal"}' in cmd
    assert "--experiment-intent-id" in cmd
    assert "intent-123" in cmd
    assert "--capability-candidates-json" in cmd
    assert '["http_probe"]' in cmd
    assert "--planner-constraints-json" in cmd
    assert '{"campaign_bound_context":true}' in cmd
    assert "--open-questions-json" in cmd
    assert '["tenant edge"]' in cmd
    assert "--planner-rationale-json" in cmd
    assert '{"target_surface_rationale":["authenticated_or_boundary_mapping"]}' in cmd
    assert "--planning-ladder-json" in cmd
    assert '{"current_stage":"control_boundary_confirmation"}' in cmd
    assert "--target-surface-rationale-json" in cmd
    assert '["authenticated_or_boundary_mapping"]' in cmd
    assert "--recommended-progression-json" in cmd
    assert '["control_boundary_confirmation"]' in cmd
    assert "--semantic-lineage-json" in cmd
    assert '{"lineage_sha256":"abc"}' in cmd
    assert "--semantic-lineage-summary-json" in cmd
    assert '{"summary":"boundary-confirmation"}' in cmd
    assert "--campaign-success-criteria" not in cmd
    assert "--recommended-action-types-json" not in cmd


def test_run_pipeline_wrapper_forwards_extended_runtime_contract_fields(monkeypatch) -> None:
    captured = {}

    def fake_run_pipeline_request(request, *, timeout=420):
        captured['request'] = dict(vars(request)) if hasattr(request, '__dict__') else dict(request)
        captured['timeout'] = timeout
        return {'ok': True}

    monkeypatch.setattr(acr, '_run_pipeline_request', fake_run_pipeline_request)

    out = acr.run_pipeline(
        'Probe',
        'https://api.example.com/',
        aggression=4,
        task_family='authz',
        planner_rationale_json='{"target_surface_rationale":["authenticated_or_boundary_mapping"]}',
        planning_ladder_json='{"current_stage":"control_boundary_confirmation"}',
        target_surface_rationale_json='["authenticated_or_boundary_mapping"]',
        recommended_progression_json='["control_boundary_confirmation"]',
        semantic_lineage_json='{"lineage_sha256":"abc"}',
        semantic_lineage_summary_json='{"summary":"boundary-confirmation"}',
    )

    assert out == {'ok': True}
    assert captured['timeout'] == 420
    request = captured['request']
    assert request['aggression'] == 4
    assert request['task_family'] == 'authz'
    assert request['planner_rationale_json'] == '{"target_surface_rationale":["authenticated_or_boundary_mapping"]}'
    assert request['planning_ladder_json'] == '{"current_stage":"control_boundary_confirmation"}'
    assert request['target_surface_rationale_json'] == '["authenticated_or_boundary_mapping"]'
    assert request['recommended_progression_json'] == '["control_boundary_confirmation"]'
    assert request['semantic_lineage_json'] == '{"lineage_sha256":"abc"}'
    assert request['semantic_lineage_summary_json'] == '{"summary":"boundary-confirmation"}'


def test_build_normalized_runtime_task_core_prefers_task_then_runtime_values() -> None:
    out = acr._build_normalized_runtime_task_core(
        {
            'objective': 'Probe',
            'success_criteria': 'collect evidence',
        },
        {
            'objective': 'Fallback probe',
            'target': 'https://api.example.com/',
            'task_family': 'authz',
            'acceptance_checks': ['negative_control'],
            'evidence_required': ['response_diff'],
        },
    )
    assert out['objective'] == 'Probe'
    assert out['target'] == 'https://api.example.com/'
    assert out['task_family'] == 'authz'
    assert out['task_success_criteria'] == 'collect evidence'
    assert out['acceptance_checks'] == ['negative_control']
    assert out['evidence_required'] == ['response_diff']



def test_ensure_runtime_task_view_builds_fallback_when_missing() -> None:
    out = acr._ensure_runtime_task_view(
        {
            'target': 'https://api.example.com/',
            'task_family': 'authz',
            'acceptance_checks': ['negative_control'],
            'evidence_required': ['response_diff'],
        },
        {},
    )
    assert out == {
        'target': 'https://api.example.com/',
        'task_family': 'authz',
        'acceptance_checks': ['negative_control'],
        'evidence_required': ['response_diff'],
    }



def test_merge_runtime_task_contract_metadata_inherits_from_runtime_task() -> None:
    out = acr._merge_runtime_task_contract_metadata(
        {'objective': 'Probe'},
        {
            'experiment_intent_id': 'intent-1',
            'capability_candidates': ['http_probe'],
            'planner_constraints': {'campaign_bound_context': True},
            'planning_ladder': {'current_stage': 'validation', 'next_stage': 'control_boundary_confirmation'},
        },
    )
    assert out['experiment_intent_id'] == 'intent-1'
    assert out['capability_candidates'] == ['http_probe']
    assert out['planner_constraints'] == {'campaign_bound_context': True}
    assert out['planning_ladder']['next_stage'] == 'control_boundary_confirmation'



def test_normalize_runtime_task_builds_defaults_and_inherits_contract_metadata() -> None:
    out = acr.normalize_runtime_task(
        {
            'success_criteria': 'collect evidence',
            'runtime_task': {
                'target': 'https://api.example.com/',
                'task_family': 'authz',
                'acceptance_checks': ['negative_control'],
                'evidence_required': ['response_diff'],
                'experiment_intent_id': 'intent-1',
                'recommended_action_types': ['differential_probe'],
            },
        }
    )
    assert out['target'] == 'https://api.example.com/'
    assert out['task_family'] == 'authz'
    assert out['task_success_criteria'] == 'collect evidence'
    assert out['acceptance_checks'] == ['negative_control']
    assert out['evidence_required'] == ['response_diff']
    assert out['experiment_intent_id'] == 'intent-1'
    assert out['recommended_action_types'] == ['differential_probe']
    assert out['runtime_task']['schema_version'] == 2
    assert out['runtime_task']['action_type'] == 'differential_probe'
    assert out['runtime_task']['experiment_shape'] == 'differential'
    assert out['runtime_task']['exploit_ladder']['stage'] == 'control_boundary_confirmation'
    assert out['action_type'] == 'differential_probe'
    assert out['capability'] == 'http_probe'



def test_load_runtime_session_bootstrap_normalizes_retry_policy_and_dns_cache(monkeypatch) -> None:
    monkeypatch.setenv('AUTO_MAX_RUNS', '123')
    monkeypatch.setenv('AUTO_TARGET_LOAD_LIMIT', '321')
    monkeypatch.setenv('AUTO_TIME_BUDGET_MIN', '7')
    monkeypatch.setenv('AUTO_RETRY_POLICY', 'AGGRESSIVE')
    monkeypatch.setattr(acr, 'load_existing_runs', lambda: [{'objective': 'Probe', 'target': 'https://api.example.com/', 'promising': True}])
    monkeypatch.setattr(acr, 'load_host_state', lambda: {'api.example.com': {'ok': True}})
    monkeypatch.setattr(acr, 'load_curated_plan', lambda: [{'target': 'https://api.example.com/'}, {'target': 'https://api.example.com/'}])
    monkeypatch.setattr(acr, 'load_runtime_plan_meta', lambda: {'plan_revision': 4, 'plan_hash': 'abc'})
    monkeypatch.setattr(acr, 'host_from_target', lambda target: 'api.example.com')
    monkeypatch.setattr(acr, 'is_resolvable_host', lambda host: True)
    monkeypatch.setattr(acr, 'load_runtime_toggles', lambda: {'x': True})
    monkeypatch.setattr(acr, 'load_planner_hints', lambda: {'hints': []})
    monkeypatch.setattr(acr, 'load_queue_state', lambda: {'followup_queue': [{'a': 1}], 'precision_queue': [{'b': 2}]})
    monkeypatch.setattr(acr, 'dedup_key', lambda objective, target: (objective, target))
    monkeypatch.setattr(acr, 'campaign_settings_for_key', lambda selected_key: {})

    out = acr._load_runtime_session_bootstrap()
    assert out.max_runs == 123
    assert out.target_load_limit == 321
    assert out.time_budget_min == 7
    assert out.retry_policy == 'aggressive'
    assert out.retry_limit == 2
    assert out.host_dns_cache == {'api.example.com': True}
    assert out.executed_keys == {('Probe', 'https://api.example.com/')}


def test_load_runtime_session_bootstrap_uses_campaign_settings_when_env_missing(monkeypatch) -> None:
    monkeypatch.delenv('AUTO_MAX_RUNS', raising=False)
    monkeypatch.delenv('AUTO_TARGET_LOAD_LIMIT', raising=False)
    monkeypatch.delenv('AUTO_TIME_BUDGET_MIN', raising=False)
    monkeypatch.delenv('AUTO_RETRY_POLICY', raising=False)
    monkeypatch.setattr(acr, 'load_existing_runs', lambda: [])
    monkeypatch.setattr(acr, 'load_host_state', lambda: {})
    monkeypatch.setattr(acr, 'load_curated_plan', lambda: [])
    monkeypatch.setattr(acr, 'load_runtime_plan_meta', lambda: {})
    monkeypatch.setattr(acr, 'load_runtime_toggles', lambda: {})
    monkeypatch.setattr(acr, 'load_planner_hints', lambda: {})
    monkeypatch.setattr(acr, 'load_queue_state', lambda: {})
    monkeypatch.setattr(acr, 'campaign_settings_for_key', lambda selected_key: {'max_runs': 20, 'target_load_limit': 55, 'time_budget_min': 20, 'retry_policy': 'strict'})
    monkeypatch.setattr(acr, 'resolve_campaign_key', lambda explicit='': 'camp-1')

    out = acr._load_runtime_session_bootstrap()
    assert out.max_runs == 20
    assert out.target_load_limit == 55
    assert out.time_budget_min == 20
    assert out.retry_policy == 'strict'
    assert out.retry_limit == 0


def test_load_runtime_toggles_normalizes_profile_style_fields(monkeypatch, tmp_path: Path) -> None:
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
    monkeypatch.setattr(acr, 'PIPELINE_CONFIG_PATH', str(config_path))

    out = acr.load_runtime_toggles(
        pipeline_config_path=acr.PIPELINE_CONFIG_PATH,
        normalize_pipeline_flags_fn=acr.normalize_pipeline_flags,
        warn_fn=acr._warn_runner,
    )

    assert out['plan_adaptation_mode'] == 'aggressive'
    assert out['aggressive_adaptation'] is True
    assert out['freeze_plan_revision'] is False
    assert out['confirm_jobs_profile'] == 'aggressive'
    assert out['max_confirm_jobs_per_target'] == 2
    assert out['confirm_job_cooldown_sec'] == 300
    assert out['workflow_escalation_profile'] == 'aggressive'
    assert out['enable_followups'] is True
    assert out['qualification_shadow_workflow_bridge'] is True
    assert out['candidate_partial_followup_bridge'] is True
    assert out['weak_signal_positive_bridge'] is True
    assert out['evidence_bearing_followup_bridge'] is True
    assert out['safe_dual_action_enabled'] is True
    assert out['max_followups_per_target'] == 4
    assert out['followup_cooldown_sec'] == 180


def test_next_followup_family_prefers_progressive_bug_finding_lanes() -> None:
    assert acr.next_followup_family('recon') == 'historical_url_mining'
    assert acr.next_followup_family('historical_url_mining') == 'content_discovery'
    assert acr.next_followup_family('content_discovery') == 'input_tamper'
    assert acr.next_followup_family('tls_assessment') == 'content_discovery'
    assert acr.next_followup_family('auth_flow') == 'authz'



def test_next_followup_family_can_use_progression_priors(tmp_path, monkeypatch) -> None:
    import learning_store  # type: ignore

    monkeypatch.setattr(learning_store, 'LEARNING_PATH', tmp_path / 'learning_store.json')
    learning_store.update_learning(
        'api.example.com',
        'recon',
        'medium',
        True,
        'ok',
        next_stage='control_boundary_confirmation',
        next_family='authz',
        target_type='api',
        target_surface_rationale=['authenticated_or_boundary_mapping'],
    )
    assert acr.next_followup_family(
        'recon',
        {
            'planning_ladder': {'current_stage': 'validation', 'next_stage': 'control_boundary_confirmation'},
            'planner_rationale': {'target_profile_summary': {'target_type': 'api'}, 'target_surface_rationale': ['authenticated_or_boundary_mapping']},
        },
    ) == 'authz'



def test_next_followup_family_attaches_archetype_explainability_for_auth_heavy_selection() -> None:
    import learning_store  # type: ignore

    result = {
        'target': 'https://portal.example.com/',
        'planning_ladder': {'current_stage': 'validation', 'next_stage': 'control_boundary_confirmation'},
        'planner_rationale': {'target_profile_summary': {'target_type': 'web'}},
    }
    learning_store.update_learning(
        'portal.example.com',
        'recon',
        'medium',
        True,
        'ok',
        target_type='web',
        archetypes=['auth_heavy'],
    )
    assert acr.next_followup_family('recon', result) == 'authz'
    assert result['followup_explainability']['archetype_primary'] == 'auth_heavy'
    assert 'prefer_authz_for_auth_heavy_archetype' in result['followup_explainability']['archetype_followup_reasons']
    assert result['followup_explainability']['selected_family'] == 'authz'
    assert result['followup_explainability']['current_family'] == 'recon'
    assert result['followup_explainability']['synthesis_recommended_action'] in {'confirm', 'pivot', 'deepen', 'abandon'}



def test_next_followup_family_prefers_authz_for_auth_heavy_archetype() -> None:
    import learning_store  # type: ignore

    learning_store.update_learning(
        'portal.example.com',
        'recon',
        'medium',
        True,
        'ok',
        target_type='web',
        archetypes=['auth_heavy'],
    )
    assert acr.next_followup_family(
        'recon',
        {
            'target': 'https://portal.example.com/',
            'planning_ladder': {'current_stage': 'validation', 'next_stage': 'control_boundary_confirmation'},
            'planner_rationale': {'target_profile_summary': {'target_type': 'web'}},
        },
    ) == 'authz'



def test_next_followup_family_attaches_archetype_explainability_for_static_edge_selection() -> None:
    import learning_store  # type: ignore

    result = {
        'target': 'https://cdn.example.com/',
        'planning_ladder': {'current_stage': 'discovery', 'next_stage': 'validation'},
        'planner_rationale': {'target_profile_summary': {'target_type': 'static'}},
    }
    learning_store.update_learning(
        'cdn.example.com',
        'recon',
        'medium',
        True,
        'ok',
        target_type='static',
        archetypes=['static_edge'],
    )
    assert acr.next_followup_family('recon', result) == 'tls_assessment'
    assert result['followup_explainability']['archetype_primary'] == 'static_edge'
    assert 'prefer_tls_assessment_for_static_edge_archetype' in result['followup_explainability']['archetype_followup_reasons']
    assert result['followup_explainability']['selected_family'] == 'tls_assessment'
    assert result['followup_explainability']['current_family'] == 'recon'



def test_next_followup_family_prefers_tls_assessment_for_static_edge_archetype() -> None:
    import learning_store  # type: ignore

    learning_store.update_learning(
        'cdn.example.com',
        'recon',
        'medium',
        True,
        'ok',
        target_type='static',
        archetypes=['static_edge'],
    )
    assert acr.next_followup_family(
        'recon',
        {
            'target': 'https://cdn.example.com/',
            'planning_ladder': {'current_stage': 'discovery', 'next_stage': 'validation'},
            'planner_rationale': {'target_profile_summary': {'target_type': 'static'}},
        },
    ) == 'tls_assessment'



def test_next_followup_family_prefers_ladder_stage_over_family_mapping() -> None:
    assert acr.next_followup_family(
        'recon',
        {
            'planning_ladder': {'current_stage': 'validation', 'next_stage': 'control_boundary_confirmation'},
            'planner_rationale': {'target_profile_summary': {'target_type': 'api'}},
        },
    ) == 'authz'
    assert acr.next_followup_family(
        'content_discovery',
        {
            'planning_ladder': {'current_stage': 'discovery', 'next_stage': 'report_artifact_capture'},
            'planner_rationale': {'target_profile_summary': {'target_type': 'static'}, 'target_surface_rationale': ['artifact_capture']},
        },
    ) == 'tls_assessment'



def test_next_followup_family_downshifts_under_dead_end_pressure() -> None:
    out = acr.next_followup_family(
        'recon',
        {
            'analysis': {'next_stage_hint': 'bounded_exploit_proof', 'target_type': 'api'},
            'planner_rationale': {'target_surface_rationale': ['authenticated_or_boundary_mapping']},
            'planner_feedback': {'dead_end_pressure_recent': 0.8, 'branch_quality_rate_recent': 0.2},
        },
    )
    assert out == 'content_discovery'



def test_next_followup_family_preserves_exploit_family_when_quality_is_strong() -> None:
    out = acr.next_followup_family(
        'authz',
        {
            'analysis': {'next_stage_hint': 'bounded_exploit_proof', 'target_type': 'api'},
            'planner_rationale': {'target_surface_rationale': ['authenticated_or_boundary_mapping']},
            'planner_feedback': {'dead_end_pressure_recent': 0.1, 'branch_quality_rate_recent': 0.8, 'recon_conversion_rate_recent': 0.6},
        },
    )
    assert out == 'authz'



def test_next_followup_family_uses_quality_to_upgrade_logic_to_authz() -> None:
    out = acr.next_followup_family(
        'recon',
        {
            'analysis': {'next_stage_hint': 'bounded_exploit_proof', 'target_type': 'api'},
            'planner_rationale': {'target_surface_rationale': ['authenticated_or_boundary_mapping']},
            'planner_feedback': {'dead_end_pressure_recent': 0.0, 'branch_quality_rate_recent': 0.8, 'recon_conversion_rate_recent': 0.5},
        },
    )
    assert out == 'authz'



def test_adaptive_followup_explainability_captures_quality_and_synthesis_truth() -> None:
    out = acr.adaptive_followup_explainability(
        inferred={'primary_archetype': 'auth_heavy', 'archetypes': ['auth_heavy'], 'confidence': 1.2, 'flags': {'auth_heavy': True}},
        planner_feedback={'dead_end_pressure_recent': 0.85, 'branch_quality_rate_recent': 0.1},
        selected_family='authz',
        current_family='recon',
        next_stage='bounded_exploit_proof',
        target_type='api',
        target_surface_rationale=['authenticated_or_boundary_mapping'],
    )
    assert out['archetype_primary'] == 'auth_heavy'
    assert out['quality_dead_end_heavy'] is True
    assert out['synthesis_recommended_action'] == 'pivot'
    assert out['synthesis_reason'] == 'dead_end_pressure_redirect'
    assert 'prefer_authz_for_auth_heavy_archetype' in out['archetype_followup_reasons']



def test_next_followup_family_uses_synthesis_to_downshift_exploit_candidate() -> None:
    out = acr.next_followup_family(
        'recon',
        {
            'analysis': {'next_stage_hint': 'bounded_exploit_proof', 'target_type': 'api'},
            'planner_rationale': {'target_surface_rationale': ['authenticated_or_boundary_mapping']},
            'planner_feedback': {'dead_end_pressure_recent': 0.85, 'branch_quality_rate_recent': 0.1},
        },
    )
    assert out == 'content_discovery'



def test_maybe_reconsult_planner_uses_stage_and_surface_hints() -> None:
    tier = acr.maybe_reconsult_planner(
        {'planner_reconsult_on_high_signal': True, 'planner_reconsult_min_interval_runs': 2, 'planner_reconsult_signal_threshold': 2},
        runs=[
            {'analysis': {'next_stage_hint': 'bounded_exploit_proof'}, 'runtime_task': {'planning_ladder': {'next_stage': 'bounded_exploit_proof'}, 'planner_rationale': {'target_surface_rationale': ['authenticated_or_boundary_mapping']}}},
            {'analysis': {'next_stage_hint': 'bounded_exploit_proof'}, 'runtime_task': {'planning_ladder': {'next_stage': 'bounded_exploit_proof'}, 'planner_rationale': {'target_surface_rationale': ['authenticated_or_boundary_mapping']}}},
        ],
        promising_count=1,
        host_state=None,
        summarize_planner_feedback_fn=acr.summarize_planner_feedback,
    )
    assert tier == 'structural'



def test_build_runtime_session_state_from_bootstrap_sets_plan_fields() -> None:
    now = datetime.now(timezone.utc)
    state = acr._build_runtime_session_state_from_bootstrap(
        acr.RuntimeSessionBootstrap(
            runs=[{'objective': 'Probe', 'target': 'https://api.example.com/', 'promising': True}],
            history=[{'objective': 'Probe', 'target': 'https://api.example.com/', 'promising': True}],
            host_state={'api.example.com': {'ok': True}},
            executed_keys={('Probe', 'https://api.example.com/')},
            run_started=now,
            max_runs=123,
            target_load_limit=321,
            time_budget_min=7,
            retry_policy='aggressive',
            retry_limit=2,
            curated_plan=[{'target': 'https://api.example.com/'}],
            runtime_plan_meta={'plan_revision': 4, 'plan_hash': 'abc'},
            host_dns_cache={'api.example.com': True},
            toggles={'x': True},
            planner_hints_cache={'hints': []},
            followup_queue=[{'a': 1}],
            precision_queue=[{'b': 2}],
        )
    )
    assert state.active_plan_revision == 4
    assert state.active_plan_hash == 'abc'
    assert state.scheduled_keys == {('Probe', 'https://api.example.com/')}
    assert state.promising_hits_ref == [1]
    assert state.idx == 1



def test_build_main_runtime_controls_normalizes_thresholds_and_modes() -> None:
    out = acr._build_main_runtime_controls(
        {
            'code000_streak_threshold': '4',
            'code000_session_cap': '6',
            'code000_cooldown_sec': '1200',
            'autodiscover_deep_skip': False,
            'max_followups_per_target': '5',
            'qualification_mode': 'LOUD',
            'qualification_promising_threshold': 'confirmed',
            'max_confirm_jobs_per_target': '3',
            'confirm_job_cooldown_sec': '60',
            'max_confirm_jobs_total': '9',
            'max_confirm_jobs_per_class': '7',
        }
    )
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



def test_build_main_state_aliases_preserves_refs_and_normalizes_scalars() -> None:
    from runtime_session_state import RuntimeSessionState  # type: ignore

    state = RuntimeSessionState(
        runs=[],
        history=[],
        host_state={},
        curated_plan=[],
        runtime_plan_meta={},
        host_dns_cache={},
        toggles={},
        planner_hints_cache={},
        followup_queue=[{'kind': 'followup'}],
        precision_queue=[{'kind': 'precision'}],
        scheduled_keys={('Probe', 'https://api.example.com/')},
        followup_counts={'api.example.com': 1},
        confirm_counts={'api.example.com': 2},
        confirm_recent={'api.example.com': 123.0},
        confirm_class_counts={'medium': 1},
        confirm_total=4,
        quality_telemetry={'probable': 1},
        retry_counts={'api.example.com': 1},
        precheck_skip_count=5,
        followup_recent={'api.example.com': 111.0},
        precheck_skip_examples=['skip'],
        unresolved_hosts={'api.example.com'},
        dns_skip_count={'api.example.com': 1},
        execution_gate_skip_count={'api.example.com': 2},
        execution_gate_skip_examples={'api.example.com': ['gate']},
        host_cooldown_until={'api.example.com': 999.0},
        host_cooldown_skip_count={'api.example.com': 3},
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
    out = acr._build_main_state_aliases(state)
    assert out.followup_queue is state.followup_queue
    assert out.precision_queue is state.precision_queue
    assert out.scheduled_keys is state.scheduled_keys
    assert out.confirm_total == 4
    assert out.precheck_skip_count == 5
    assert out.last_persist_ts == 55.5
    assert out.host_family_owner_gate is state.host_family_owner_gate
    assert out.host_precheck_burst is state.host_precheck_burst



def test_build_main_skip_summary_flushers_wires_each_summary_bucket(monkeypatch) -> None:
    calls = []

    def fake_flush_skip_summaries(**kwargs):  # type: ignore[no-untyped-def]
        calls.append(kwargs)
        if kwargs['precheck_skip_count_ref']:
            kwargs['precheck_skip_count_ref'][0] = 0

    monkeypatch.setattr(acr.acst, 'flush_skip_summaries', fake_flush_skip_summaries)
    precheck_ref = [5]
    precheck_examples = ['skip']
    dns_skip_count = {'api.example.com': 1}
    host_cooldown_skip_count = {'api.example.com': 2}
    execution_gate_skip_count = {'api.example.com': 3}
    execution_gate_skip_examples = {'api.example.com': ['gate']}

    flushers = acr._build_main_skip_summary_flushers(
        precheck_skip_count_ref=precheck_ref,
        precheck_skip_examples=precheck_examples,
        dns_skip_count=dns_skip_count,
        host_cooldown_skip_count=host_cooldown_skip_count,
        execution_gate_skip_count=execution_gate_skip_count,
        execution_gate_skip_examples=execution_gate_skip_examples,
    )
    flushers['flush_precheck_summary'](force=True)
    flushers['flush_dns_skip_summary']()
    flushers['flush_host_cooldown_summary']()
    flushers['flush_execution_gate_summary']()

    assert precheck_ref == [0]
    assert calls[0]['precheck_skip_count_ref'] is precheck_ref
    assert calls[0]['precheck_skip_examples_ref'] is precheck_examples
    assert calls[0]['force'] is True
    assert calls[1]['dns_skip_count_ref'] is dns_skip_count
    assert calls[2]['host_cooldown_skip_count_ref'] is host_cooldown_skip_count
    assert calls[3]['execution_gate_skip_count_ref'] is execution_gate_skip_count
    assert calls[3]['execution_gate_skip_examples_ref'] is execution_gate_skip_examples



def test_build_main_planner_callbacks_updates_refs_and_delegates(monkeypatch) -> None:
    from runtime_session_state import RuntimeSessionState  # type: ignore

    state = RuntimeSessionState(
        runs=[{'objective': 'Probe', 'target': 'https://api.example.com/'}],
        history=[],
        host_state={'api.example.com': {'ok': True}},
        curated_plan=[{'target': 'https://api.example.com/'}],
        runtime_plan_meta={},
        host_dns_cache={},
        toggles={},
        planner_hints_cache={'old': True},
    )
    refresh_calls = {}
    regen_calls = {}
    reconcile_calls = {}

    monkeypatch.setattr(acr, 'load_planner_hints', lambda: {'fresh': True})
    monkeypatch.setattr(acr, 'load_runtime_plan_meta', lambda: {'plan_revision': 2, 'plan_hash': 'xyz'})
    monkeypatch.setattr(acr, 'load_curated_plan', lambda: [{'target': 'https://next.example.com/'}])

    def fake_refresh(**kwargs):  # type: ignore[no-untyped-def]
        refresh_calls.update(kwargs)
        return {'fresh': True}

    def fake_regen(**kwargs):  # type: ignore[no-untyped-def]
        regen_calls.update(kwargs)
        return 99

    def fake_reconcile(**kwargs):  # type: ignore[no-untyped-def]
        reconcile_calls.update(kwargs)
        return ([{'target': 'https://next.example.com/'}], 7, 'hash-7', True)

    monkeypatch.setattr(acr, 'apply_planner_hints_refresh', fake_refresh)
    monkeypatch.setattr(acr, 'apply_plan_regeneration', fake_regen)
    monkeypatch.setattr(acr, 'apply_plan_reconciliation', fake_reconcile)

    planner_hints_cache_ref = [{'old': True}]
    last_regen_run_index_ref = [1]
    curated_plan_ref = [[{'target': 'https://api.example.com/'}]]
    active_plan_revision_ref = [3]
    active_plan_hash_ref = ['hash-3']

    callbacks = acr._build_main_planner_callbacks(
        state=state,
        toggles={'planner': True},
        runs=state.runs,
        followup_queue=[{'a': 1}],
        precision_queue=[{'b': 2}],
        planner_hints_cache_ref=planner_hints_cache_ref,
        last_regen_run_index_ref=last_regen_run_index_ref,
        curated_plan_ref=curated_plan_ref,
        active_plan_revision_ref=active_plan_revision_ref,
        active_plan_hash_ref=active_plan_hash_ref,
        reprioritize_queues_fn=lambda: None,
    )
    callbacks['refresh_planner_hints_and_reprioritize']('cycle', tier='deep')
    callbacks['maybe_trigger_plan_regeneration']('regen', force=True)
    callbacks['reconcile_active_plan_if_needed']('reconcile')

    assert planner_hints_cache_ref[0] == {'fresh': True}
    assert last_regen_run_index_ref == [99]
    assert curated_plan_ref == [[{'target': 'https://next.example.com/'}]]
    assert active_plan_revision_ref == [7]
    assert active_plan_hash_ref == ['hash-7']
    assert refresh_calls['reason'] == 'cycle'
    assert refresh_calls['tier'] == 'deep'
    assert refresh_calls['followup_queue_len'] == 1
    assert refresh_calls['precision_queue_len'] == 1
    assert regen_calls['reason'] == 'regen'
    assert regen_calls['force'] is True
    assert regen_calls['last_regen_run_index'] == 1
    assert reconcile_calls['reason'] == 'reconcile'
    assert reconcile_calls['curated_plan'] == [{'target': 'https://api.example.com/'}]
    assert reconcile_calls['active_plan_revision'] == 3
    assert reconcile_calls['active_plan_hash'] == 'hash-3'



def test_build_main_runtime_callbacks_wire_persist_queue_and_override(monkeypatch) -> None:
    persist_calls = {}
    override_calls = {}

    class FakeQueueCoordinator:
        def __init__(self) -> None:
            self.enqueued = []
            self.dequeued = {'target': 'https://api.example.com/'}

        def enqueue(self, task, high_priority=False):  # type: ignore[no-untyped-def]
            self.enqueued.append((task, high_priority))

        def dequeue(self):  # type: ignore[no-untyped-def]
            return self.dequeued

    def fake_persist_live_snapshot(**kwargs):  # type: ignore[no-untyped-def]
        persist_calls.update(kwargs)

    def fake_apply_runtime_overrides(**kwargs):  # type: ignore[no-untyped-def]
        override_calls.update(kwargs)
        return (True, False, 5, 4)

    monkeypatch.setattr(acr.acst, 'persist_live_snapshot', fake_persist_live_snapshot)
    monkeypatch.setattr(acr, 'load_runtime_plan_meta', lambda: {'plan_revision': 7})
    monkeypatch.setattr(acr, 'apply_runtime_overrides', fake_apply_runtime_overrides)

    queue = FakeQueueCoordinator()
    precheck_skip_count_ref = [6]
    callbacks = acr._build_main_runtime_callbacks(
        campaign_validation={'ok': True},
        run_started=datetime.now(timezone.utc),
        max_runs=12,
        time_budget_min=9,
        retry_policy='balanced',
        runs=[{'objective': 'Probe', 'target': 'https://api.example.com/'}],
        followup_queue=[{'kind': 'followup'}],
        precision_queue=[{'kind': 'precision'}],
        precheck_skip_count_ref=precheck_skip_count_ref,
        dns_skip_count={'api.example.com': 1},
        host_cooldown_skip_count={'api.example.com': 2},
        execution_gate_skip_count={'api.example.com': 3},
        quality_telemetry={'probable': 1},
        host_state={'api.example.com': {'ok': True}},
        queue_coordinator=queue,
    )
    callbacks['persist_live_summary']()
    callbacks['enqueue_followup_task']({'target': 'https://next.example.com/'}, high_priority=True)
    dequeued = callbacks['dequeue_next_task']()
    out = callbacks['refresh_runtime_overrides'](False, True, 2, 1)

    assert persist_calls['precheck_skip_count'] == 6
    assert persist_calls['followup_queue'] == [{'kind': 'followup'}]
    assert persist_calls['precision_queue'] == [{'kind': 'precision'}]
    assert persist_calls['runtime_plan_meta'] == {'plan_revision': 7}
    assert persist_calls['host_state'] == {'api.example.com': {'ok': True}}
    assert queue.enqueued == [({'target': 'https://next.example.com/'}, True)]
    assert dequeued == {'target': 'https://api.example.com/'}
    assert out == (True, False, 5, 4)
    assert override_calls['owner_override_global'] is False
    assert override_calls['last_override_state'] is True
    assert override_calls['aggression_override_global'] == 2
    assert override_calls['last_aggression_override'] == 1
    assert override_calls['read_runtime_owner_override_fn'] == acr.read_runtime_owner_override
    assert override_calls['read_runtime_aggression_override_fn'] == acr.read_runtime_aggression_override



def test_build_main_precheck_hooks_increment_and_flush() -> None:
    calls = []
    ref = [2]
    hooks = acr._build_main_precheck_hooks(
        precheck_skip_count_ref=ref,
        flush_precheck_summary_fn=lambda: calls.append('precheck'),
        flush_dns_skip_summary_fn=lambda: calls.append('dns'),
        flush_host_cooldown_summary_fn=lambda: calls.append('cooldown'),
        flush_execution_gate_summary_fn=lambda: calls.append('gate'),
    )
    hooks['inc_precheck_skip']()
    hooks['on_executed_key']()
    assert ref == [3]
    assert calls == ['precheck', 'dns', 'cooldown', 'gate']



def test_persist_main_runtime_snapshot_passes_expected_payload(monkeypatch) -> None:
    persist_calls = {}

    def fake_persist_live_snapshot(**kwargs):  # type: ignore[no-untyped-def]
        persist_calls.update(kwargs)

    monkeypatch.setattr(acr.acst, 'persist_live_snapshot', fake_persist_live_snapshot)
    monkeypatch.setattr(acr, 'load_runtime_plan_meta', lambda: {'plan_revision': 7})

    acr._persist_main_runtime_snapshot(
        campaign_validation={'ok': True},
        run_started=datetime.now(timezone.utc),
        max_runs=12,
        time_budget_min=9,
        retry_policy='balanced',
        runs=[{'objective': 'Probe', 'target': 'https://api.example.com/'}],
        followup_queue=[{'kind': 'followup'}],
        precision_queue=[{'kind': 'precision'}],
        precheck_skip_count_ref=[6],
        dns_skip_count={'api.example.com': 1},
        host_cooldown_skip_count={'api.example.com': 2},
        execution_gate_skip_count={'api.example.com': 3},
        quality_telemetry={'probable': 1},
        host_state={'api.example.com': {'ok': True}},
    )
    assert persist_calls['precheck_skip_count'] == 6
    assert persist_calls['runtime_plan_meta'] == {'plan_revision': 7}
    assert persist_calls['host_state'] == {'api.example.com': {'ok': True}}
    assert persist_calls['followup_queue'] == [{'kind': 'followup'}]



def test_refresh_main_runtime_overrides_delegates(monkeypatch) -> None:
    captured = {}

    def fake_apply_runtime_overrides(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return (True, False, 5, 4)

    monkeypatch.setattr(acr, 'apply_runtime_overrides', fake_apply_runtime_overrides)
    out = acr._refresh_main_runtime_overrides(False, True, 2, 1)
    assert out == (True, False, 5, 4)
    assert captured['owner_override_global'] is False
    assert captured['last_override_state'] is True
    assert captured['aggression_override_global'] == 2
    assert captured['last_aggression_override'] == 1
    assert captured['read_runtime_owner_override_fn'] == acr.read_runtime_owner_override
    assert captured['read_runtime_aggression_override_fn'] == acr.read_runtime_aggression_override



def test_build_main_prepare_callbacks_delegate_prepare_and_reprioritize(monkeypatch) -> None:
    from runtime_session_state import RuntimeSessionState  # type: ignore

    class FakePrecheckContext:
        def __init__(self) -> None:
            self.calls = []

        def prepare_task_precheck(self, **kwargs):  # type: ignore[no-untyped-def]
            self.calls.append(kwargs)
            return {'prepared': kwargs['target']}

    curated_calls = {}
    runtime_calls = {}
    reprio_calls = {}

    def fake_prepare_curated_task(entry, **kwargs):  # type: ignore[no-untyped-def]
        curated_calls['entry'] = entry
        curated_calls.update(kwargs)
        return {'kind': 'curated'}

    def fake_prepare_runtime_task(task, **kwargs):  # type: ignore[no-untyped-def]
        runtime_calls['task'] = task
        runtime_calls.update(kwargs)
        return {'kind': 'runtime'}

    def fake_reprioritize(**kwargs):  # type: ignore[no-untyped-def]
        reprio_calls.update(kwargs)

    monkeypatch.setattr(acr, 'prepare_curated_task', fake_prepare_curated_task)
    monkeypatch.setattr(acr, 'prepare_runtime_task', fake_prepare_runtime_task)
    monkeypatch.setattr(acr, 'apply_queue_reprioritization', fake_reprioritize)

    state = RuntimeSessionState(
        runs=[{'objective': 'Probe', 'target': 'https://api.example.com/'}],
        history=[],
        host_state={'api.example.com': {'ok': True}},
        curated_plan=[],
        runtime_plan_meta={},
        host_dns_cache={},
        toggles={},
        planner_hints_cache={},
        followup_queue=[{'kind': 'followup'}],
        precision_queue=[{'kind': 'precision'}],
        host_family_owner_gate={'api.example.com': {'authz': True}},
    )
    precheck_ctx = FakePrecheckContext()
    planner_hints_cache_ref = [{'fresh': True}]
    scheduled_keys = {('Probe', 'https://api.example.com/')}

    callbacks = acr._build_main_prepare_callbacks(
        precheck_ctx=precheck_ctx,
        scheduled_keys=scheduled_keys,
        toggles={'queue': True},
        state=state,
        planner_hints_cache_ref=planner_hints_cache_ref,
    )
    precheck_out = callbacks['prepare_task_precheck'](
        objective='Probe',
        target='https://api.example.com/',
        mode='fast',
        task_family='authz',
        dedup_mode_suffix=True,
    )
    curated_out = callbacks['prepare_curated_task']({'target': 'https://api.example.com/'}, 4)
    runtime_out = callbacks['prepare_runtime_task']({'target': 'https://api.example.com/'}, 'Probe', 'https://api.example.com/', 'fast', 5, True, False, 'Plan')
    callbacks['reprioritize_queues']()

    assert precheck_out == {'prepared': 'https://api.example.com/'}
    assert precheck_ctx.calls[0]['objective'] == 'Probe'
    assert precheck_ctx.calls[0]['task_family'] == 'authz'
    assert curated_out == {'kind': 'curated'}
    assert curated_calls['entry'] == {'target': 'https://api.example.com/'}
    assert callable(curated_calls['prepare_task_precheck_fn'])
    assert runtime_out == {'kind': 'runtime'}
    assert runtime_calls['task'] == {'target': 'https://api.example.com/'}
    assert runtime_calls['scheduled_keys'] is scheduled_keys
    assert callable(runtime_calls['prepare_task_precheck_fn'])
    assert reprio_calls['followup_queue'] == state.followup_queue
    assert reprio_calls['precision_queue'] == state.precision_queue
    assert reprio_calls['runs'] == state.runs
    assert reprio_calls['toggles'] == {'queue': True}
    assert reprio_calls['planner_hints_cache'] == {'fresh': True}
    assert reprio_calls['host_state'] == state.host_state
    assert reprio_calls['host_family_owner_gate'] == state.host_family_owner_gate



def test_build_main_post_run_actions_callback_accepts_signal_contract_and_delegates(monkeypatch) -> None:
    captured = {}

    def fake_handle_post_run_actions(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return (5, {'decision': 'queued'})

    monkeypatch.setattr(acr, 'handle_post_run_actions', fake_handle_post_run_actions)
    callback = acr._build_main_post_run_actions_callback(
        retry_counts={},
        retry_limit=2,
        followup_queue=[],
        followup_counts={},
        followup_recent={},
        max_followups_per_target=3,
        scheduled_keys=set(),
        host_weak_count={},
        host_family_owner_gate={},
        confirm_counts={},
        confirm_recent={},
        confirm_class_counts={},
        max_confirm_jobs_per_target=1,
        max_confirm_jobs_total=4,
        max_confirm_jobs_per_class=2,
        confirm_job_cooldown_sec=600,
        quality_telemetry={'probable': 1},
        toggles={'policy_diag_logging': True},
        enqueue_followup_task_fn=lambda task, high_priority=False: None,
    )
    out = callback(
        {'task_family': 'authz'},
        result={'ok': True},
        qual={'verdict': 'probable'},
        classification='medium',
        auditor='approve',
        engine_status='ok',
        success_eval_status='partial',
        summary_text='summary',
        reason_code='interesting',
        target='https://api.example.com/',
        objective='Probe',
        aggression=4,
        owner_auth=True,
        owner_override=False,
        mode='followup',
        confirm_total=2,
        promising=True,
        signal_contract={'workflow_promotion': 'promotable'},
        runtime_decision={'intent_flags': {'followup': True}},
    )
    assert out == (5, {'decision': 'queued'})
    assert captured['signal_contract'] == {'workflow_promotion': 'promotable'}
    assert captured['runtime_decision'] == {'intent_flags': {'followup': True}}
    assert captured['confirm_total'] == 2
    assert callable(captured['enqueue_followup_task_fn'])



def test_build_main_execute_runtime_task_callback_executes_pipeline_and_completion(monkeypatch) -> None:
    from types import SimpleNamespace

    state = SimpleNamespace(
        runs=[{'objective': 'Probe', 'target': 'https://api.example.com/'}],
        followup_queue=[{'kind': 'followup'}],
        precision_queue=[{'kind': 'precision'}],
        host_weak_count={},
        quality_telemetry={},
        host_state={'api.example.com': {'ok': True}},
        promising_hits_ref=[1],
    )
    execution_deps = SimpleNamespace()
    runner_deps = SimpleNamespace()
    pipeline_calls = {}
    complete_calls = {}

    def fake_execute_runtime_task_pipeline(**kwargs):  # type: ignore[no-untyped-def]
        pipeline_calls.update(kwargs)
        return (
            77.0,
            (
                {'ok': True},
                'old-classification',
                'approve',
                'ok',
                'old-summary',
                False,
                {
                    'reason_code': 'interesting',
                    'success_eval_status': 'partial',
                    'summary_text': 'new-summary',
                    'classification': 'medium',
                },
                {'verdict': 'probable'},
                True,
                {'runtime_decision': {'intent_flags': {'followup': True}}},
            ),
        )

    def fake_complete_runtime_run(**kwargs):  # type: ignore[no-untyped-def]
        complete_calls.update(kwargs)
        return (9, {'runtime_decision': {}}, None)

    monkeypatch.setattr(acr, 'execute_runtime_task_pipeline', fake_execute_runtime_task_pipeline)
    monkeypatch.setattr(acr, 'complete_runtime_run', fake_complete_runtime_run)

    callback = acr._build_main_execute_runtime_task_callback(
        state=state,
        execution_deps=execution_deps,
        runner_deps=runner_deps,
        record_and_persist_run_fn=lambda run_info: None,
        toggles={'policy_diag_logging': True},
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
        qualification_mode='shadow',
        qualification_promising_threshold='probable',
    )
    out = callback(
        {'task_family': 'authz'},
        objective='Probe',
        target='https://api.example.com/',
        mode='fast',
        aggression=4,
        owner_auth=True,
        owner_override=False,
        plan_name='Plan',
        run_index=2,
        last_heartbeat_ts=11.0,
        confirm_total=3,
    )
    assert out == (77.0, 9)
    assert pipeline_calls['objective'] == 'Probe'
    assert pipeline_calls['deps'] == execution_deps
    assert pipeline_calls['qualification_mode'] == 'shadow'
    assert complete_calls['classification'] == 'medium'
    assert complete_calls['summary_text'] == 'new-summary'
    assert complete_calls['reason_code'] == 'interesting'
    assert complete_calls['success_eval_status'] == 'partial'
    assert complete_calls['deps'] == runner_deps
    assert callable(complete_calls['record_and_persist_run_fn'])



def test_build_main_persist_callbacks_update_timestamp_and_delegate(monkeypatch) -> None:
    from types import SimpleNamespace

    state = SimpleNamespace(runs=[{'objective': 'Probe'}], history=[], host_state={'api.example.com': {'ok': True}})
    services = acr._build_runtime_persist_services(
        reprioritize_queues_fn=lambda: None,
        persist_recorded_run_fn=lambda **kwargs: 0.0,
        maybe_trigger_plan_regeneration_fn=lambda reason: None,
    )
    persist_calls = {}
    adapt_calls = {}
    last_persist_ts_ref = [12.5]

    def fake_run_record_and_persist_stage(**kwargs):  # type: ignore[no-untyped-def]
        persist_calls.update(kwargs)
        return 55.5

    def fake_apply_runtime_adaptation(**kwargs):  # type: ignore[no-untyped-def]
        adapt_calls.update(kwargs)

    monkeypatch.setattr(acr, '_run_record_and_persist_stage', fake_run_record_and_persist_stage)
    monkeypatch.setattr(acr, 'apply_runtime_adaptation', fake_apply_runtime_adaptation)

    callbacks = acr._build_main_persist_callbacks(
        persist_services=services,
        state=state,
        last_persist_ts_ref=last_persist_ts_ref,
        persist_live_summary_fn=lambda: None,
    )
    callbacks['record_and_persist_run']({'objective': 'Probe'})
    callbacks['apply_recorded_runtime_adaptation']({'objective': 'Probe'})

    assert last_persist_ts_ref == [55.5]
    assert persist_calls['services'] == services
    assert persist_calls['state'] == state
    assert persist_calls['run_info'] == {'objective': 'Probe'}
    assert persist_calls['last_persist_ts'] == 12.5
    assert callable(persist_calls['persist_live_summary_fn'])
    assert adapt_calls == {'services': services, 'run_info': {'objective': 'Probe'}}



def test_run_main_execution_stage_executes_and_prints_summary(monkeypatch, capsys) -> None:
    from types import SimpleNamespace

    state = SimpleNamespace()
    prepare_deps = SimpleNamespace()
    captured = {}

    monkeypatch.setattr(acr, 'parse_rc_metrics', lambda *args, **kwargs: {})
    monkeypatch.setattr(acr, 'summarize_result', lambda *args, **kwargs: {})
    monkeypatch.setattr(acr, 'run_pipeline', lambda *args, **kwargs: {})

    def fake_execute_runner_session(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return {'ok': True, 'runs': 1}

    monkeypatch.setattr(acr, 'execute_runner_session', fake_execute_runner_session)
    acr._run_main_execution_stage(
        state=state,
        campaign_validation={'ok': True},
        run_started=datetime.now(timezone.utc),
        max_runs=5,
        target_load_limit=9,
        time_budget_min=10,
        retry_policy='balanced',
        toggles={'queue_preemption_in_curated_loop': False},
        queue_coordinator=object(),
        prepare_deps=prepare_deps,
        quality_telemetry={},
        execute_runtime_task_fn=lambda *args, **kwargs: (0.0, 0),
        maybe_trigger_plan_regeneration_fn=lambda reason, force=False: None,
        reconcile_active_plan_if_needed_fn=lambda reason: None,
        persist_live_summary_fn=lambda: None,
        flush_precheck_summary_fn=lambda force=False: None,
        flush_dns_skip_summary_fn=lambda force=False: None,
        flush_host_cooldown_summary_fn=lambda force=False: None,
        flush_execution_gate_summary_fn=lambda force=False: None,
        log_operation_fn=lambda *args, **kwargs: None,
    )
    out = capsys.readouterr().out
    assert '"ok": true' in out
    assert captured['state'] == state
    assert captured['prepare_deps'] == prepare_deps



def test_run_main_execution_stage_finalizes_and_reraises(monkeypatch) -> None:
    from runtime_session_state import RuntimeSessionState  # type: ignore

    state = RuntimeSessionState(runs=[], history=[], host_state={}, curated_plan=[], runtime_plan_meta={}, host_dns_cache={}, toggles={}, planner_hints_cache={})
    finalized = {}

    monkeypatch.setattr(acr, 'parse_rc_metrics', lambda *args, **kwargs: {})
    monkeypatch.setattr(acr, 'summarize_result', lambda *args, **kwargs: {})
    monkeypatch.setattr(acr, 'run_pipeline', lambda *args, **kwargs: {})

    def fake_execute_runner_session(**kwargs):  # type: ignore[no-untyped-def]
        raise RuntimeError('boom')

    def fake_finalize_runner_exception(**kwargs):  # type: ignore[no-untyped-def]
        finalized.update(kwargs)

    monkeypatch.setattr(acr, 'execute_runner_session', fake_execute_runner_session)
    monkeypatch.setattr(acr, 'finalize_runner_exception', fake_finalize_runner_exception)

    try:
        acr._run_main_execution_stage(
            state=state,
            campaign_validation={'ok': True},
            run_started=datetime.now(timezone.utc),
            max_runs=5,
            target_load_limit=9,
            time_budget_min=10,
            retry_policy='balanced',
            toggles={'queue_preemption_in_curated_loop': False},
            queue_coordinator=object(),
            prepare_deps=object(),
            quality_telemetry={},
            execute_runtime_task_fn=lambda *args, **kwargs: (0.0, 0),
            maybe_trigger_plan_regeneration_fn=lambda reason, force=False: None,
            reconcile_active_plan_if_needed_fn=lambda reason: None,
            persist_live_summary_fn=lambda: None,
            flush_precheck_summary_fn=lambda force=False: None,
            flush_dns_skip_summary_fn=lambda force=False: None,
            flush_host_cooldown_summary_fn=lambda force=False: None,
            flush_execution_gate_summary_fn=lambda force=False: None,
            log_operation_fn=lambda *args, **kwargs: None,
        )
        raise AssertionError('expected RuntimeError')
    except RuntimeError as exc:
        assert str(exc) == 'boom'
    assert finalized['state'] == state
    assert str(finalized['error']) == 'boom'



def test_build_main_session_base_fields_wraps_state_refs() -> None:
    from runtime_session_state import RuntimeSessionState  # type: ignore

    state = RuntimeSessionState(
        runs=[{'objective': 'Probe'}],
        history=[],
        host_state={'api.example.com': {'ok': True}},
        curated_plan=[{'target': 'https://api.example.com/'}],
        runtime_plan_meta={},
        host_dns_cache={'api.example.com': True},
        toggles={'x': True},
        planner_hints_cache={'fresh': True},
    )
    out = acr._build_main_session_base_fields(state)
    assert out.runs is state.runs
    assert out.host_state is state.host_state
    assert out.executed_keys is state.executed_keys
    assert out.curated_plan_ref == [state.curated_plan]
    assert out.active_plan_revision_ref == [state.active_plan_revision]
    assert out.active_plan_hash_ref == [state.active_plan_hash]
    assert out.host_dns_cache is state.host_dns_cache
    assert out.toggles is state.toggles
    assert out.planner_hints_cache_ref == [state.planner_hints_cache]
    assert out.last_regen_run_index_ref == [state.last_regen_run_index]



def test_build_main_session_alias_fields_wraps_aliases_and_queue_coordinator() -> None:
    from runtime_session_state import RuntimeSessionState  # type: ignore

    state = RuntimeSessionState(
        runs=[],
        history=[],
        host_state={},
        curated_plan=[],
        runtime_plan_meta={},
        host_dns_cache={},
        toggles={},
        planner_hints_cache={},
        followup_queue=[{'kind': 'followup'}],
        precision_queue=[{'kind': 'precision'}],
        scheduled_keys={('Probe', 'https://api.example.com/')},
        followup_counts={'api.example.com': 1},
        confirm_counts={'api.example.com': 2},
        confirm_recent={'api.example.com': 123.0},
        confirm_class_counts={'medium': 1},
        confirm_total=4,
        quality_telemetry={'probable': 1},
        retry_counts={'api.example.com': 1},
        precheck_skip_count=5,
        followup_recent={'api.example.com': 111.0},
        precheck_skip_examples=['skip'],
        unresolved_hosts={'api.example.com'},
        dns_skip_count={'api.example.com': 1},
        execution_gate_skip_count={'api.example.com': 2},
        execution_gate_skip_examples={'api.example.com': ['gate']},
        host_cooldown_until={'api.example.com': 999.0},
        host_cooldown_skip_count={'api.example.com': 3},
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
    aliases = acr._build_main_state_aliases(state)
    queue_coordinator = acr._build_queue_coordinator(
        followup_queue=aliases.followup_queue,
        precision_queue=aliases.precision_queue,
        host_rr=aliases.host_rr,
        host_success_count=aliases.host_success_count,
        host_fail_count=aliases.host_fail_count,
    )
    out = acr._build_main_session_alias_fields(aliases, queue_coordinator)
    assert out.followup_queue is state.followup_queue
    assert out.precision_queue is state.precision_queue
    assert out.confirm_total == 4
    assert out.precheck_skip_count_ref == [5]
    assert out.queue_coordinator is queue_coordinator
    assert out.last_persist_ts_ref == [55.5]
    assert out.host_family_owner_gate is state.host_family_owner_gate



def test_build_main_session_setup_compacts_state_controls_and_queue_context() -> None:
    from runtime_session_state import RuntimeSessionState  # type: ignore

    state = RuntimeSessionState(
        runs=[{'objective': 'Probe', 'target': 'https://api.example.com/'}],
        history=[],
        host_state={'api.example.com': {'ok': True}},
        curated_plan=[{'target': 'https://api.example.com/'}],
        runtime_plan_meta={'plan_revision': 4},
        host_dns_cache={'api.example.com': True},
        toggles={
            'code000_streak_threshold': '4',
            'code000_session_cap': '6',
            'code000_cooldown_sec': '1200',
            'autodiscover_deep_skip': False,
            'max_followups_per_target': '5',
            'qualification_mode': 'LOUD',
            'qualification_promising_threshold': 'confirmed',
            'max_confirm_jobs_per_target': '3',
            'confirm_job_cooldown_sec': '60',
            'max_confirm_jobs_total': '9',
            'max_confirm_jobs_per_class': '7',
        },
        planner_hints_cache={'fresh': True},
        followup_queue=[{'kind': 'followup'}],
        precision_queue=[{'kind': 'precision'}],
        executed_keys={('Probe', 'https://api.example.com/')},
        followup_counts={'api.example.com': 1},
        confirm_counts={'api.example.com': 2},
        confirm_recent={'api.example.com': 123.0},
        confirm_class_counts={'medium': 1},
        confirm_total=4,
        quality_telemetry={'probable': 1},
        retry_counts={'api.example.com': 1},
        precheck_skip_count=5,
        followup_recent={'api.example.com': 111.0},
        precheck_skip_examples=['skip'],
        unresolved_hosts={'api.example.com'},
        dns_skip_count={'api.example.com': 1},
        execution_gate_skip_count={'api.example.com': 2},
        execution_gate_skip_examples={'api.example.com': ['gate']},
        host_cooldown_until={'api.example.com': 999.0},
        host_cooldown_skip_count={'api.example.com': 3},
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
    out = acr._build_main_session_setup(state)
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
    assert out.followup_queue is state.followup_queue
    assert out.queue_coordinator.followup_queue is state.followup_queue
    assert out.queue_coordinator.precision_queue is state.precision_queue
    assert out.precheck_skip_count_ref == [5]
    assert out.last_persist_ts_ref == [55.5]



def test_build_runtime_execution_deps_assembles_execution_services() -> None:
    deps = acr._build_runtime_execution_deps(
        qualification_mode='shadow',
        qualification_promising_threshold='probable',
    )
    assert deps.summarize_result_fn == acr.summarize_result
    assert deps.post_result_common_fn == acr.post_result_common
    assert deps.log_event_fn == acr.log_event
    assert deps.run_pipeline_fn == acr.run_pipeline



def test_build_runtime_runner_deps_assembles_runner_services(monkeypatch) -> None:
    captured = {}

    class FakeRuntimeRunnerDeps:
        def __init__(self, **kwargs):
            captured.update(kwargs)
            self.__dict__.update(kwargs)

    monkeypatch.setattr(acr, 'RuntimeRunnerDeps', FakeRuntimeRunnerDeps)
    deps = acr._build_runtime_runner_deps(
        apply_post_run_actions_fn=lambda **kwargs: (0, {}),
        project_runtime_decision_to_run_info_fn=lambda **kwargs: {},
        maybe_reconsult_planner_fn=lambda **kwargs: None,
        refresh_planner_hints_and_reprioritize_fn=lambda **kwargs: None,
        prepare_task_precheck_fn=lambda **kwargs: {},
        prepare_curated_task_fn=lambda *args, **kwargs: None,
        prepare_runtime_task_fn=lambda *args, **kwargs: None,
        reprioritize_queues_fn=lambda: None,
        persist_recorded_run_fn=lambda **kwargs: 0.0,
        apply_runtime_adaptation_fn=lambda run_info: None,
    )
    assert deps.apply_post_run_actions_fn is not None
    assert deps.persist_recorded_run_fn is not None
    assert captured



def test_build_queue_coordinator_wraps_queue_coordinator_construction(monkeypatch) -> None:
    captured = {}

    class FakeQueueCoordinator:
        def __init__(self, **kwargs):
            captured.update(kwargs)
            self.__dict__.update(kwargs)

    monkeypatch.setattr(acr, 'QueueCoordinator', FakeQueueCoordinator)
    out = acr._build_queue_coordinator(
        followup_queue=[],
        precision_queue=[],
        host_rr={},
        host_success_count={},
        host_fail_count={},
    )
    assert isinstance(out, FakeQueueCoordinator)
    assert captured == {
        'followup_queue': [],
        'precision_queue': [],
        'host_rr': {},
        'host_success_count': {},
        'host_fail_count': {},
    }



def test_build_runtime_precheck_context_inputs_assembles_precheck_bundle() -> None:
    payload = acr._build_runtime_precheck_context_inputs(
        unresolved_hosts=set(),
        dns_skip_count={},
        host_dns_cache={},
        host_cooldown_until={},
        host_cooldown_skip_count={},
        autodiscover_deep_skip=True,
        executed_keys=set(),
        precheck_skip_examples=[],
        host_precheck_burst={},
        host_state={},
        deep_budget={},
        host_fail_streak={},
        host_success_count={},
        host_fail_count={},
        gate_skip_count={},
        gate_skip_examples={},
        increment_precheck_skip_fn=lambda: None,
        on_executed_key_fn=lambda: None,
        is_sensitive_host_fn=lambda host: host.endswith('.sensitive'),
        host_warmup_complete_fn=lambda host_state, target: True,
    )
    assert payload.autodiscover_deep_skip is True
    assert callable(payload.dedup_key_fn)
    assert callable(payload.family_allowed_for_host_stage_fn)
    assert callable(payload.log_skip_fn)



def test_build_execute_runtime_task_inputs_assembles_execution_bundle() -> None:
    from types import SimpleNamespace

    state = SimpleNamespace(
        runs=[{'objective': 'Probe', 'target': 'https://api.example.com/'}],
        followup_queue=[{'a': 1}],
        precision_queue=[{'b': 2}],
        host_weak_count={},
        quality_telemetry={},
    )
    deps = SimpleNamespace()
    payload = acr._build_execute_runtime_task_inputs(
        task_ctx={'task_family': 'authz'},
        objective='Probe',
        target='https://api.example.com/',
        mode='fast',
        aggression=4,
        owner_auth=True,
        owner_override=False,
        plan_name='Plan',
        run_index=2,
        last_heartbeat_ts=11.0,
        confirm_total=3,
        state=state,
        execution_deps=deps,
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
        toggles={'policy_diag_logging': True},
        qualification_mode='shadow',
        qualification_promising_threshold='probable',
    )
    assert payload.objective == 'Probe'
    assert payload.runs_count == 1
    assert payload.followup_queue_len == 1
    assert payload.precision_queue_len == 1
    assert payload.deps == deps



def test_build_complete_runtime_run_inputs_assembles_completion_bundle() -> None:
    from types import SimpleNamespace
    from runtime_session_state import RuntimeSessionState  # type: ignore

    state = RuntimeSessionState(runs=[], history=[], host_state={'api.example.com': {'ok': True}}, curated_plan=[], runtime_plan_meta={}, host_dns_cache={}, toggles={}, planner_hints_cache={}, promising_hits_ref=[1])
    runner_deps = SimpleNamespace(
        apply_post_run_actions_fn=lambda **kwargs: (0, {}),
        project_runtime_decision_to_run_info_fn=lambda **kwargs: {},
        maybe_reconsult_planner_fn=lambda **kwargs: None,
        refresh_planner_hints_and_reprioritize_fn=lambda **kwargs: None,
        precheck_and_prepare_task_fn=lambda **kwargs: {},
        prepare_curated_task_fn=lambda *args, **kwargs: None,
        prepare_runtime_task_fn=lambda *args, **kwargs: None,
        reprioritize_queues_fn=lambda: None,
        persist_recorded_run_fn=lambda **kwargs: 0.0,
        apply_runtime_adaptation_fn=lambda run_info: None,
    )
    payload = acr._build_complete_runtime_run_inputs(
        task_ctx={'task_family': 'authz'},
        result={'ok': True},
        qual={'verdict': 'probable'},
        classification='medium',
        auditor='approve',
        engine_status='ok',
        success_eval_status='partial',
        summary_text='summary',
        reason_code='interesting',
        target='https://api.example.com/',
        objective='Probe',
        aggression=4,
        owner_auth=True,
        owner_override=False,
        mode='fast',
        confirm_total=3,
        promising=True,
        run_info={'runtime_decision': {'intent_flags': {'followup': True}}},
        runner_deps=runner_deps,
        record_and_persist_run_fn=lambda run_info: None,
        toggles={'policy_diag_logging': True},
        state=state,
    )
    assert payload.target == 'https://api.example.com/'
    assert payload.confirm_total == 3
    assert payload.promising is True
    assert payload.deps == runner_deps
    assert payload.promising_hits_ref == [1]



def test_run_record_and_persist_stage_builds_inputs_and_calls_runtime_persist(monkeypatch) -> None:
    from types import SimpleNamespace

    state = SimpleNamespace(runs=[{'objective': 'Probe', 'target': 'https://api.example.com/'}], history=[{'objective': 'Probe', 'target': 'https://api.example.com/'}], host_state={'api.example.com': {'ok': True}})
    services = acr._build_runtime_persist_services(
        reprioritize_queues_fn=lambda: None,
        persist_recorded_run_fn=lambda **kwargs: 0.0,
        maybe_trigger_plan_regeneration_fn=lambda reason: None,
    )
    captured = {}

    def fake_record_and_persist_runtime_run(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return 55.5

    monkeypatch.setattr(acr, 'record_and_persist_runtime_run', fake_record_and_persist_runtime_run)
    out = acr._run_record_and_persist_stage(
        services=services,
        state=state,
        run_info={'objective': 'Probe'},
        last_persist_ts=12.5,
        persist_live_summary_fn=lambda: None,
        update_learning_fn=lambda *args, **kwargs: None,
        save_host_state_fn=lambda *args, **kwargs: None,
        attack_family_fn=lambda objective, target, family: family or 'generic',
    )
    assert out == 55.5
    assert captured['services'] == services
    assert captured['runs'] == state.runs
    assert captured['last_persist_ts'] == 12.5



def test_build_runtime_persist_services_assembles_services() -> None:
    services = acr._build_runtime_persist_services(
        reprioritize_queues_fn=lambda: None,
        persist_recorded_run_fn=lambda **kwargs: 0.0,
        maybe_trigger_plan_regeneration_fn=lambda reason: None,
    )
    assert services.reprioritize_queues_fn is not None
    assert services.persist_recorded_run_fn is not None
    assert services.maybe_trigger_plan_regeneration_fn is not None



def test_build_record_and_persist_run_inputs_assembles_persist_bundle() -> None:
    from types import SimpleNamespace

    state = SimpleNamespace(runs=[{'objective': 'Probe', 'target': 'https://api.example.com/'}], history=[{'objective': 'Probe', 'target': 'https://api.example.com/'}], host_state={'api.example.com': {'ok': True}})
    services = acr._build_runtime_persist_services(
        reprioritize_queues_fn=lambda: None,
        persist_recorded_run_fn=lambda **kwargs: 0.0,
        maybe_trigger_plan_regeneration_fn=lambda reason: None,
    )
    payload = acr._build_record_and_persist_run_inputs(
        services=services,
        state=state,
        run_info={'objective': 'Probe'},
        last_persist_ts=12.5,
        persist_live_summary_fn=lambda: None,
        update_learning_fn=lambda *args, **kwargs: None,
        save_host_state_fn=lambda *args, **kwargs: None,
        attack_family_fn=lambda objective, target, family: family or 'generic',
    )
    assert payload.services == services
    assert payload.runs == state.runs
    assert payload.history == state.history
    assert payload.host_state == state.host_state
    assert payload.last_persist_ts == 12.5
    assert payload.record_run_fn == acr.record_run



def test_build_runtime_session_bundle_inputs_assembles_bundle_call() -> None:
    payload = acr._build_runtime_session_bundle_inputs(
        apply_post_run_actions_fn=lambda **kwargs: (0, {}),
        project_runtime_decision_to_run_info_fn=lambda **kwargs: {},
        maybe_reconsult_planner_fn=lambda **kwargs: None,
        refresh_planner_hints_and_reprioritize_fn=lambda **kwargs: None,
        prepare_task_precheck_fn=lambda **kwargs: {},
        prepare_curated_task_fn=lambda *args, **kwargs: None,
        prepare_runtime_task_fn=lambda *args, **kwargs: None,
        build_execute_runtime_request_fn=lambda *args, **kwargs: {},
        reprioritize_queues_fn=lambda: None,
        persist_recorded_run_fn=lambda **kwargs: 0.0,
        apply_runtime_adaptation_fn=lambda run_info: None,
        qualification_mode='shadow',
        qualification_promising_threshold='probable',
    )
    assert payload.prepare_task_precheck_fn is not None
    assert payload.build_execute_runtime_request_fn is not None
    assert payload.run_pipeline_fn == acr.run_pipeline
    assert payload.normalize_pipeline_status_fn == acr.normalize_pipeline_status



def test_build_execute_runner_session_inputs_assembles_runner_call_bundle() -> None:
    from types import SimpleNamespace

    state = SimpleNamespace()
    prepare_deps = SimpleNamespace(
        precheck_and_prepare_task_fn=lambda **kwargs: {},
        prepare_curated_task_fn=lambda *args, **kwargs: None,
        prepare_runtime_task_fn=lambda *args, **kwargs: None,
    )
    payload = acr._build_execute_runner_session_inputs(
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
    )
    assert payload.state == state
    assert payload.max_runs == 5
    assert payload.target_load_limit == 9
    assert payload.preempt_in_curated is False
    assert payload.prepare_deps == prepare_deps
    assert payload.execute_runtime_task_fn is not None



def test_build_finalize_runner_exception_inputs_assembles_finalize_bundle() -> None:
    from runtime_session_state import RuntimeSessionState  # type: ignore

    state = RuntimeSessionState(runs=[], history=[], host_state={}, curated_plan=[], runtime_plan_meta={}, host_dns_cache={}, toggles={}, planner_hints_cache={})
    err = RuntimeError('boom')
    payload = acr._build_finalize_runner_exception_inputs(
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
    )
    assert payload.state == state
    assert payload.retry_policy == 'balanced'
    assert payload.error is err
    assert payload.reports_dir == acr.REPORTS_DIR



def test_build_post_run_action_inputs_normalizes_and_binds_helpers() -> None:
    payload = acr._build_post_run_action_inputs(
        task={'task_family': 'authz'},
        result={'ok': True},
        qual={'verdict': 'probable'},
        classification='medium',
        auditor='approve',
        engine_status='ok',
        success_eval_status='partial',
        summary_text='summary',
        reason_code='interesting',
        target='https://api.example.com/',
        objective='Probe',
        aggression=4,
        owner_auth=True,
        owner_override=False,
        mode='followup',
        retry_counts={},
        retry_limit=2,
        followup_queue=[],
        followup_counts={},
        followup_recent={},
        max_followups_per_target=3,
        scheduled_keys=set(),
        host_weak_count={},
        host_family_owner_gate={},
        confirm_counts={},
        confirm_recent={},
        confirm_total=1,
        confirm_class_counts={},
        max_confirm_jobs_per_target=2,
        max_confirm_jobs_total=4,
        max_confirm_jobs_per_class=2,
        confirm_job_cooldown_sec=600,
        quality_telemetry={},
        toggles={'policy_diag_logging': True},
        promising=True,
        signal_contract={'workflow_promotion': 'promotable'},
        runtime_decision={'intent_flags': {'followup': True}},
        enqueue_followup_task_fn=lambda task, high_priority=False: None,
    )
    assert payload.task['mode'] == 'followup'
    assert payload.classification == 'medium'
    assert payload.retry_limit == 2
    assert payload.promising is True
    assert payload.signal_contract == {'workflow_promotion': 'promotable'}
    assert callable(payload.enqueue_followup_task_fn)
    assert payload.dedup_key_fn == acr.dedup_key
    assert payload.post_run_decision_fn == acr.post_run_decision



def test_planner_vector_weight_falls_back_on_bad_task_shape() -> None:
    out = acr.planner_vector_weight(object(), {'suggested_attack_vectors': ['authz-check']})  # type: ignore[arg-type]
    assert out == 1.0



def test_handle_post_run_actions_delegates_built_inputs(monkeypatch) -> None:
    captured = {}

    def fake_apply_effective_decision(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return (7, {'decision': 'queued'})

    monkeypatch.setattr(acr, 'apply_effective_decision', fake_apply_effective_decision)
    out = acr.handle_post_run_actions(
        task={'task_family': 'authz'},
        result={'ok': True},
        qual={'verdict': 'probable'},
        classification='medium',
        auditor='approve',
        engine_status='ok',
        success_eval_status='partial',
        summary_text='summary',
        reason_code='interesting',
        target='https://api.example.com/',
        objective='Probe',
        aggression=4,
        owner_auth=True,
        owner_override=False,
        mode='followup',
        retry_counts={},
        retry_limit=2,
        followup_queue=[],
        followup_counts={},
        followup_recent={},
        max_followups_per_target=3,
        scheduled_keys=set(),
        host_weak_count={},
        host_family_owner_gate={},
        confirm_counts={},
        confirm_recent={},
        confirm_total=1,
        confirm_class_counts={},
        max_confirm_jobs_per_target=2,
        max_confirm_jobs_total=4,
        max_confirm_jobs_per_class=2,
        confirm_job_cooldown_sec=600,
        quality_telemetry={},
        toggles={'policy_diag_logging': True},
        promising=True,
        signal_contract={'workflow_promotion': 'promotable'},
        runtime_decision={'intent_flags': {'followup': True}},
        enqueue_followup_task_fn=lambda task, high_priority=False: None,
    )
    assert out == (7, {'decision': 'queued'})
    assert captured['task']['mode'] == 'followup'
    assert captured['objective'] == 'Probe'
    assert captured['signal_contract'] == {'workflow_promotion': 'promotable'}
    assert callable(captured['enqueue_followup_task_fn'])
    assert captured['dedup_key_fn'] == acr.dedup_key



def test_handle_post_run_actions_suppresses_followup_under_dead_end_pressure(monkeypatch) -> None:
    captured = {}

    def fake_apply_effective_decision(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return (1, {'decision': 'suppressed'})

    monkeypatch.setattr(acr, 'apply_effective_decision', fake_apply_effective_decision)
    acr.handle_post_run_actions(
        task={'task_family': 'authz'},
        result={'planner_feedback': {'dead_end_pressure_recent': 0.8}},
        qual={'verdict': 'probable'},
        classification='medium',
        auditor='approve',
        engine_status='ok',
        success_eval_status='partial',
        summary_text='summary',
        reason_code='interesting',
        target='https://api.example.com/',
        objective='Probe',
        aggression=4,
        owner_auth=True,
        owner_override=False,
        mode='followup',
        retry_counts={},
        retry_limit=2,
        followup_queue=[],
        followup_counts={},
        followup_recent={},
        max_followups_per_target=3,
        scheduled_keys=set(),
        host_weak_count={},
        host_family_owner_gate={},
        confirm_counts={},
        confirm_recent={},
        confirm_total=1,
        confirm_class_counts={},
        max_confirm_jobs_per_target=2,
        max_confirm_jobs_total=4,
        max_confirm_jobs_per_class=2,
        confirm_job_cooldown_sec=600,
        quality_telemetry={},
        toggles={'policy_diag_logging': True},
        promising=True,
        signal_contract={'workflow_promotion': 'promotable'},
        runtime_decision={'intent_flags': {'followup': True, 'confirm': False}},
        enqueue_followup_task_fn=lambda task, high_priority=False: None,
    )
    assert captured['runtime_decision']['intent_flags']['followup'] is False



def test_handle_post_run_actions_promotes_high_priority_under_strong_quality(monkeypatch) -> None:
    captured = {}

    def fake_apply_effective_decision(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return (2, {'decision': 'queued'})

    monkeypatch.setattr(acr, 'apply_effective_decision', fake_apply_effective_decision)
    acr.handle_post_run_actions(
        task={'task_family': 'authz'},
        result={'planner_feedback': {'branch_quality_rate_recent': 0.8, 'recon_conversion_rate_recent': 0.6}},
        qual={'verdict': 'probable'},
        classification='medium',
        auditor='approve',
        engine_status='ok',
        success_eval_status='partial',
        summary_text='summary',
        reason_code='interesting',
        target='https://api.example.com/',
        objective='Probe',
        aggression=4,
        owner_auth=True,
        owner_override=False,
        mode='followup',
        retry_counts={},
        retry_limit=2,
        followup_queue=[],
        followup_counts={},
        followup_recent={},
        max_followups_per_target=3,
        scheduled_keys=set(),
        host_weak_count={},
        host_family_owner_gate={},
        confirm_counts={},
        confirm_recent={},
        confirm_total=1,
        confirm_class_counts={},
        max_confirm_jobs_per_target=2,
        max_confirm_jobs_total=4,
        max_confirm_jobs_per_class=2,
        confirm_job_cooldown_sec=600,
        quality_telemetry={},
        toggles={'policy_diag_logging': True},
        promising=True,
        signal_contract={'workflow_promotion': 'promotable'},
        runtime_decision={'intent_flags': {'followup': True}},
        enqueue_followup_task_fn=lambda task, high_priority=False: None,
    )
    assert captured['runtime_decision']['high_priority'] is True



def test_build_run_pipeline_request_normalizes_request_bundle() -> None:
    req = acr._build_run_pipeline_request(
        'Probe target',
        'https://api.example.com/',
        aggression=3,
        owner_auth=True,
        owner_override=True,
        success_semantics_json='{"success_model":"differential_or_stateful_signal"}',
        recommended_action_types_json='["differential_probe"]',
    )
    assert req.objective == 'Probe target'
    assert req.target == 'https://api.example.com/'
    assert req.aggression == 3
    assert req.owner_auth is True
    assert req.owner_override is True
    assert req.success_semantics_json == '{"success_model":"differential_or_stateful_signal"}'
    assert req.recommended_action_types_json == '["differential_probe"]'



def test_build_run_pipeline_command_includes_contract_fields_and_owner_flags() -> None:
    cmd = acr._build_run_pipeline_command(
        'Probe target',
        'https://api.example.com/',
        aggression=3,
        owner_auth=True,
        owner_override=True,
        success_semantics_json='{"success_model":"differential_or_stateful_signal"}',
        recommended_action_types_json='["differential_probe"]',
    )
    assert cmd[:2] == ['python3', acr.RUN_PIPE]
    assert '--success-semantics-json' in cmd
    assert '{"success_model":"differential_or_stateful_signal"}' in cmd
    assert '--recommended-action-types-json' in cmd
    assert '["differential_probe"]' in cmd
    assert '--owner-approved-auth' in cmd
    assert '--owner-override' in cmd


def test_run_pipeline_builds_expected_command_with_owner_flags(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class DummyProc:
        returncode = 0
        stdout = '{}'
        stderr = ''

    def fake_run(cmd, capture_output, text, timeout):  # type: ignore[no-untyped-def]
        captured['cmd'] = list(cmd)
        captured['timeout'] = timeout
        return DummyProc()

    monkeypatch.setattr(acr.subprocess, 'run', fake_run)
    out = acr.run_pipeline(
        'Probe target',
        'https://api.example.com/',
        aggression=3,
        owner_auth=True,
        owner_override=True,
        success_semantics_json='{"success_model":"differential_or_stateful_signal"}',
        recommended_action_types_json='["differential_probe"]',
    )
    assert out == {}
    cmd = list(captured['cmd'] or [])
    assert cmd == acr._build_run_pipeline_command(
        'Probe target',
        'https://api.example.com/',
        aggression=3,
        owner_auth=True,
        owner_override=True,
        success_semantics_json='{"success_model":"differential_or_stateful_signal"}',
        recommended_action_types_json='["differential_probe"]',
    )
    assert captured['timeout'] == 420



def test_run_pipeline_command_flow_composes_execute_and_decode(monkeypatch) -> None:
    monkeypatch.setattr(acr, '_execute_run_pipeline_command', lambda cmd, timeout=420: {'proc': type('P', (), {'returncode': 0, 'stdout': '{}', 'stderr': ''})()})
    out = acr._run_pipeline_command_flow(['python3', acr.RUN_PIPE], timeout=9)
    assert out == {}


def test_run_pipeline_accepts_runtime_intent_metadata_without_crashing(monkeypatch) -> None:
    captured = {}

    class DummyProc:
        returncode = 0
        stdout = '{}'
        stderr = ''

    def fake_run(cmd, capture_output, text, timeout):  # type: ignore[no-untyped-def]
        captured['cmd'] = list(cmd)
        captured['timeout'] = timeout
        return DummyProc()

    monkeypatch.setattr(acr.subprocess, 'run', fake_run)
    out = acr.run_pipeline(
        'Probe target',
        'https://api.example.com/',
        aggression=3,
        owner_auth=False,
        owner_override=False,
        planner_rationale_json='{"target_surface_rationale":["authenticated_or_boundary_mapping"]}',
        planning_ladder_json='{"current_stage":"control_boundary_confirmation"}',
        target_surface_rationale_json='["authenticated_or_boundary_mapping"]',
        recommended_progression_json='["control_boundary_confirmation"]',
        semantic_lineage_json='{"lineage_sha256":"abc"}',
        semantic_lineage_summary_json='{"summary":"ok"}',
    )
    assert out == {}
    assert captured['timeout'] == 420
    assert '--objective' in captured['cmd']



def test_decode_run_pipeline_result_preserves_exec_error() -> None:
    out = acr._decode_run_pipeline_result({'error': 'run_pipeline_timeout:boom'})
    assert out == {'error': 'run_pipeline_timeout:boom'}


def test_decode_run_pipeline_result_handles_invalid_json() -> None:
    class DummyProc:
        returncode = 0
        stdout = 'not-json'
        stderr = ''

    out = acr._decode_run_pipeline_result({'proc': DummyProc()})
    assert out['error'] == 'invalid_pipeline_output'
    assert out['raw'] == 'not-json'


def test_inspect_json_signal_from_command_detects_findings_and_info(tmp_path) -> None:
    out_path = tmp_path / 'response.json'
    out_path.write_text(
        '{"error":"boom","token":"eyJhbGciOiJIUzI1NiI.abcdefghijkL.mnopqrstuvWX","owner_id":1,"debug":"/swagger","note":"redirect_uri=https://example.com/cb","headers":"set-cookie"}',
        encoding='utf-8',
    )
    out = acr.inspect_json_signal_from_command(['curl', '-o', str(out_path)])
    assert out['signal'] is True
    assert any(item['code'] == 'secret_leak_signal' for item in out['findings'])
    assert any(item['code'] == 'authz_boundary_signal' for item in out['findings'])
    assert any(item['code'] == 'redirect_handling_signal' for item in out['info'])
    assert any(item['code'] == 'header_exposure_signal' for item in out['info'])
    assert out['keys']


def test_summarize_result_applies_metric_overrides() -> None:
    result = {
        'engine': {
            'status': 'failed',
            'stdout': '__RC_METRICS__ code=403 total=1',
            'stderr': '',
            'returncode': 22,
            'command': 'curl https://api.example.com/',
        },
        'auditor': {'decision': 'approve'},
    }
    classification, auditor, engine_status, summary_text, error_flag = acr.summarize_result(result)
    assert classification == 'blocked'
    assert auditor == 'approve'
    assert engine_status == 'failed'
    assert summary_text == 'Blocked by origin/WAF policy (HTTP 403).'
    assert error_flag is False


def test_execute_run_pipeline_command_timeout_normalization(monkeypatch) -> None:
    def fake_run(cmd, capture_output, text, timeout):  # type: ignore[no-untyped-def]
        raise subprocess.TimeoutExpired(cmd=cmd, timeout=timeout)

    monkeypatch.setattr(acr.subprocess, 'run', fake_run)
    out = acr._execute_run_pipeline_command(['python3', acr.RUN_PIPE], timeout=7)
    assert str(out.get('error') or '').startswith('run_pipeline_timeout:')


def test_run_pipeline_returns_exec_failure_from_helper(monkeypatch) -> None:
    monkeypatch.setattr(acr, '_execute_run_pipeline_command', lambda cmd, timeout=420: {'error': 'run_pipeline_exec_failed:boom'})
    out = acr.run_pipeline('Probe target', 'https://api.example.com/')
    assert out == {'error': 'run_pipeline_exec_failed:boom'}



def test_run_pipeline_request_builds_command_and_runs_flow(monkeypatch) -> None:
    captured = {}

    def fake_flow(cmd, timeout=420):  # type: ignore[no-untyped-def]
        captured['cmd'] = list(cmd)
        captured['timeout'] = timeout
        return {'ok': True}

    monkeypatch.setattr(acr, '_run_pipeline_command_flow', fake_flow)
    req = acr._build_run_pipeline_request('Probe target', 'https://api.example.com/', aggression=3)
    out = acr._run_pipeline_request(req, timeout=11)
    assert out == {'ok': True}
    assert captured['cmd'] == acr._build_run_pipeline_command('Probe target', 'https://api.example.com/', aggression=3)
    assert captured['timeout'] == 11



def test_run_pipeline_delegates_command_flow(monkeypatch) -> None:
    captured = {}

    def fake_request(request, timeout=420):  # type: ignore[no-untyped-def]
        captured['request'] = request
        captured['timeout'] = timeout
        return {'ok': True}

    monkeypatch.setattr(acr, '_run_pipeline_request', fake_request)
    out = acr.run_pipeline('Probe target', 'https://api.example.com/', aggression=3)
    assert out == {'ok': True}
    assert captured['request'] == acr._build_run_pipeline_request('Probe target', 'https://api.example.com/', aggression=3)
    assert captured['timeout'] == 420
