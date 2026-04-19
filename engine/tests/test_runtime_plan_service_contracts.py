from __future__ import annotations

import json
import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_plan_service as rps  # type: ignore
from runtime_plan_service import runtime_plan_entries_from_blueprint  # type: ignore
from planer.parser import parse_program_text  # type: ignore
from planer.interpretation import build_interpretations  # type: ignore
from planer.blueprint import build_blueprint  # type: ignore


def test_runtime_plan_entries_include_planner_rationale_fields() -> None:
    blueprint = {
        'structured_scope': {'domains': ['api.example.com'], 'allow_keywords': ['authz']},
        'target_profiles': {
            'api.example.com': {
                'target_type': 'api',
                'surface_keywords': ['json', 'rest'],
                'task_family_seeds': ['authz', 'logic'],
                'candidate_vectors': ['idor', 'workflow abuse'],
                'notes': ['high value surface'],
            }
        },
        'task_family_seeds': {'api.example.com': ['authz']},
        'planner_hints': {
            'per_target_vectors': {'api.example.com': ['authz', 'logic']},
            'recommended_task_families': ['authz', 'logic'],
            'deprioritized_task_families': ['secret_hunt'],
            'ambiguities': ['shared auth edge'],
            'interpretation_conflicts': ['api/web boundary'],
            'llm_confidence': 0.81,
        },
        'aggression_profile': {'recommended_default': 5, 'recommended_min': 3, 'recommended_max': 7},
    }
    entries = runtime_plan_entries_from_blueprint(blueprint)
    assert entries
    rationale = entries[0]['planner_rationale']
    assert rationale['preferred_vector_families'] == ['authz', 'logic']
    assert rationale['deprioritized_task_families'] == ['secret_hunt']
    assert rationale['target_profile_summary']['target_type'] == 'api'
    assert rationale['planner_input_source'] == 'legacy_seed_synthesis'
    assert rationale['field_ownership']['contract_mode'] == 'legacy_seed_synthesis'
    assert 'task_success_criteria' in rationale['field_ownership']['derived_or_defaulted']
    assert entries[0]['planner_input_source'] == 'legacy_seed_synthesis'
    assert entries[0]['planner_field_ownership']['contract_mode'] == 'legacy_seed_synthesis'
    assert entries[0]['runtime_task']['planner_input_source'] == 'legacy_seed_synthesis'
    assert entries[0]['runtime_task']['planner_field_ownership']['contract_mode'] == 'legacy_seed_synthesis'
    assert entries[0]['runtime_task']['planner_rationale']['preferred_vector_families'] == ['authz', 'logic']
    assert entries[0]['runtime_task']['schema_version'] == 2
    assert entries[0]['runtime_task']['action_type'] == 'single_probe'
    assert entries[0]['runtime_task']['capability'] == 'http_probe'
    assert entries[0]['runtime_task']['exploit_ladder']['stage'] == 'control_boundary_confirmation'
    assert rationale['recommended_progression'][0] == 'authenticated_or_boundary_mapping'
    assert 'control_boundary_confirmation' in rationale['recommended_progression']
    assert entries[0]['runtime_task']['planner_rationale']['recommended_progression'] == rationale['recommended_progression']
    assert entries[0]['runtime_task']['planner_rationale']['target_profile_summary']['target_type'] == 'api'
    assert entries[0]['runtime_task']['planner_rationale']['target_surface_rationale'][0] == 'authenticated_or_boundary_mapping'
    assert entries[0]['runtime_task']['planning_ladder']['current_stage'] == 'control_boundary_confirmation'
    assert entries[0]['success_semantics']['success_model'] == 'differential_or_stateful_signal'


def test_load_campaign_blueprint_for_key_supports_relative_latest_path(tmp_path: Path, monkeypatch) -> None:
    registry_root = tmp_path / 'campaign_registry'
    key = 'camp1'
    campaign_dir = registry_root / key
    version_dir = campaign_dir / 'versions' / 'v0001'
    version_dir.mkdir(parents=True)
    (campaign_dir / 'latest.json').write_text('{"path": "versions/v0001"}', encoding='utf-8')
    (version_dir / 'blueprint.json').write_text('{"structured_scope": {"domains": ["api.example.com"]}}', encoding='utf-8')
    monkeypatch.setattr(rps, 'PLANNER_REGISTRY_ROOT', registry_root)
    resolved_version_dir, bp_path, bp = rps.load_campaign_blueprint_for_key(key)
    assert resolved_version_dir == version_dir
    assert bp_path == version_dir / 'blueprint.json'
    assert bp['structured_scope']['domains'] == ['api.example.com']


def test_load_active_campaign_blueprint_prefers_bound_campaign_key_over_runtime_meta(tmp_path: Path, monkeypatch) -> None:
    registry_root = tmp_path / 'campaign_registry'
    camp1 = registry_root / 'camp1'
    camp2 = registry_root / 'camp2'
    v1 = camp1 / 'versions' / 'v0001'
    v2 = camp2 / 'versions' / 'v0001'
    v1.mkdir(parents=True)
    v2.mkdir(parents=True)
    (camp1 / 'latest.json').write_text('{"path": "versions/v0001"}', encoding='utf-8')
    (camp2 / 'latest.json').write_text('{"path": "versions/v0001"}', encoding='utf-8')
    (v1 / 'blueprint.json').write_text('{"structured_scope": {"domains": ["api.example.com"]}}', encoding='utf-8')
    (v2 / 'blueprint.json').write_text('{"structured_scope": {"domains": ["wrong.example.com"]}}', encoding='utf-8')
    monkeypatch.setattr(rps, 'PLANNER_REGISTRY_ROOT', registry_root)
    key, _version_dir, _bp_path, bp = rps.load_active_campaign_blueprint('camp1', runtime_plan_meta={'campaign_key': 'camp2'})
    assert key == 'camp1'
    assert bp['structured_scope']['domains'] == ['api.example.com']


def test_runtime_plan_entries_support_legacy_type_field_in_target_profiles() -> None:
    blueprint = {
        'structured_scope': {'domains': ['api.example.com']},
        'target_profiles': {
            'api.example.com': {
                'type': 'api',
                'task_family_seeds': ['authz'],
            }
        },
        'task_family_seeds': {'api.example.com': ['authz']},
        'planner_hints': {},
        'aggression_profile': {},
    }
    entries = runtime_plan_entries_from_blueprint(blueprint)
    assert entries
    assert entries[0]['planner_rationale']['target_profile_summary']['target_type'] == 'api'


def test_real_planner_blueprint_normalizes_target_type_for_runtime_entries() -> None:
    parsed = parse_program_text('Program scope:\n- api.example.com\n- app.example.com\nAllowed: recon, idor')
    blueprint = build_blueprint(parsed, {'flags': {}}, build_interpretations(parsed, 'Program scope:\n- api.example.com\n- app.example.com\nAllowed: recon, idor'))
    entries = runtime_plan_entries_from_blueprint(blueprint)
    assert entries
    summaries = [e['planner_rationale']['target_profile_summary'] for e in entries]
    assert any(str(s.get('target_type') or '') == 'api' for s in summaries)


def test_runtime_plan_entries_use_experiment_intents_when_present() -> None:
    blueprint = {
        'structured_scope': {'domains': ['api.example.com']},
        'target_profiles': {'api.example.com': {'target_type': 'api', 'task_family_seeds': ['authz'], 'surface_keywords': ['json'], 'priority_tier': 'high', 'expected_depth': 'deep', 'surface_role': 'primary', 'target_cluster': 'integration_api'}},
        'task_family_seeds': {'api.example.com': ['authz']},
        'planner_hints': {},
        'planner_directives': {'constraints': {}, 'preferences': {}, 'unknowns': {}},
        'experiment_intents': [
            {
                'intent_id': 'intent-authz-1',
                'target': 'https://api.example.com/',
                'target_host': 'api.example.com',
                'target_type': 'api',
                'task_family': 'authz',
                'objective': 'AuthN/AuthZ boundary probing (safe)',
                'capability_candidates': ['http_probe', 'response_diff'],
                'recommended_action_types': ['differential_probe', 'confirmatory_probe'],
                'hypothesis_candidates': ['idor', 'tenant boundary'],
                'evidence_contract': {'acceptance_checks': ['negative_control'], 'evidence_required': ['response_diff'], 'expected_signal_type': 'behavior_delta', 'evidence_goal_type': 'controlled_comparison'},
                'success_model': 'differential_or_stateful_signal',
                'negative_control_requirements': ['negative_control'],
                'planner_constraints': {'campaign_bound_context': True},
                'planner_preferences': {'preferred_vector_families': ['authz'], 'recommended_task_families': ['authz'], 'deprioritized_task_families': ['secret_hunt']},
                'priority_tier': 'high',
                'expected_depth': 'deep',
                'activation_phase': 1,
                'activation_mode': 'immediate',
                'conditional_gate': 'authenticated_or_boundary_mapping',
                'surface_role': 'primary',
                'target_cluster': 'integration_api',
                'ambiguity_flags': ['tenant edge'],
                'open_questions': ['role inheritance unclear'],
                'runtime_task_contract': {
                    'schema_version': 2,
                    'action_type': 'differential_probe',
                    'capability': 'http_probe',
                    'experiment_shape': 'differential',
                    'evidence_goal': 'controlled_comparison',
                    'exploit_ladder': {'stage': 'control_boundary_confirmation', 'progression': ['discovery','validation','control_boundary_confirmation'], 'proof_strategy': 'actor_or_object_boundary_delta'},
                    'actor_requirements': {'required': True, 'differential': True, 'preferred_roles': ['anonymous', 'baseline_user']},
                    'session_requirements': {'stateful': False, 'auth_context': True, 'prerequisites': ['establish comparison identities']},
                    'promotion_policy': {'followup_allowed': True, 'confirm_preferred': True, 'bounded_only': True},
                    'contamination_policy': {'learning_excluded_on_cross_host_mismatch': True, 'learning_excluded_on_hygiene_violation': True},
                    'priority_tier': 'high',
                    'expected_depth': 'deep',
                    'activation_phase': 1,
                    'activation_mode': 'immediate',
                    'conditional_gate': 'authenticated_or_boundary_mapping',
                    'surface_role': 'primary',
                    'target_cluster': 'integration_api',
                    'approval_sensitivity': {'owner_approval_required': True, 'auth_sensitive': True}
                },
                'action_type': 'differential_probe',
                'capability': 'http_probe',
                'experiment_shape': 'differential',
                'evidence_goal': 'controlled_comparison',
                'exploit_ladder': {'stage': 'control_boundary_confirmation'},
                'actor_requirements': {'required': True, 'differential': True},
                'session_requirements': {'stateful': False, 'auth_context': True},
                'promotion_policy': {'followup_allowed': True, 'confirm_preferred': True, 'bounded_only': True},
                'contamination_policy': {'learning_excluded_on_cross_host_mismatch': True, 'learning_excluded_on_hygiene_violation': True},
                'approval_sensitivity': {'owner_approval_required': True, 'auth_sensitive': True},
            }
        ],
        'aggression_profile': {'recommended_default': 5, 'recommended_min': 3, 'recommended_max': 7},
    }
    entries = runtime_plan_entries_from_blueprint(blueprint)
    assert len(entries) == 1
    entry = entries[0]
    assert entry['planner_input_source'] == 'experiment_intent_canonical'
    assert entry['planner_rationale']['planner_input_source'] == 'experiment_intent_canonical'
    assert entry['runtime_task']['planner_input_source'] == 'experiment_intent_canonical'
    assert entry['planner_field_ownership']['contract_mode'] == 'experiment_intent_canonical'
    assert 'target' in entry['planner_field_ownership']['strict_from_input']
    assert 'task_success_criteria' in entry['planner_field_ownership']['derived_or_defaulted']
    assert 'acceptance_checks' in entry['planner_field_ownership']['strict_from_input']
    assert entry['planner_rationale']['experiment_intent_id'] == 'intent-authz-1'
    assert entry['planner_rationale']['capability_candidates'] == ['http_probe', 'response_diff']
    assert entry['planner_rationale']['planning_ladder']['planning_mode'] == 'laddered'
    assert entry['planning_ladder']['current_stage'] == 'control_boundary_confirmation'
    assert entry['planner_rationale']['recommended_progression'][0] == 'authenticated_or_boundary_mapping'
    assert entry['planner_rationale']['recommended_progression'][1] == 'control_boundary_confirmation'
    assert entry['planner_rationale']['target_surface_rationale'][0] == 'authenticated_or_boundary_mapping'
    assert entry['runtime_task']['planning_ladder']['current_stage'] == 'control_boundary_confirmation'
    assert entry['semantic_lineage']['planner_contract']['planning_ladder']['current_stage'] == 'control_boundary_confirmation'
    assert entry['semantic_lineage']['artifact_boundaries']['lineage_sha256']
    assert entry['runtime_task']['semantic_lineage']['artifact_boundaries']['lineage_sha256'] == entry['semantic_lineage']['artifact_boundaries']['lineage_sha256']
    assert entry['runtime_task']['schema_version'] == 2
    assert entry['runtime_task']['recommended_action_types'] == ['differential_probe', 'confirmatory_probe']
    assert entry['runtime_task']['action_type'] == 'differential_probe'
    assert entry['runtime_task']['capability'] == 'http_probe'
    assert entry['runtime_task']['experiment_shape'] == 'differential'
    assert entry['runtime_task']['evidence_goal'] == 'controlled_comparison'
    assert entry['runtime_task']['exploit_ladder']['stage'] == 'control_boundary_confirmation'
    assert entry['runtime_task']['actor_requirements']['differential'] is True
    assert entry['runtime_task']['session_requirements']['prerequisites'] == ['establish comparison identities']
    assert entry['runtime_task']['approval_sensitivity']['auth_sensitive'] is True
    assert entry['runtime_task']['hypothesis_candidates'] == ['idor', 'tenant boundary']
    assert entry['priority_tier'] == 'high'
    assert entry['expected_depth'] == 'deep'
    assert entry['activation_phase'] == 1
    assert entry['activation_mode'] == 'immediate'
    assert entry['conditional_gate'] == 'authenticated_or_boundary_mapping'
    assert entry['surface_role'] == 'primary'
    assert entry['target_cluster'] == 'integration_api'
    assert entry['runtime_task']['priority_tier'] == 'high'
    assert entry['runtime_task']['expected_depth'] == 'deep'
    assert entry['runtime_task']['target_cluster'] == 'integration_api'
    assert entry['acceptance_checks'] == ['negative_control']


def test_runtime_plan_entries_strip_cross_host_text_from_experiment_intents() -> None:
    blueprint = {
        'structured_scope': {'domains': ['api.example.com']},
        'target_profiles': {'api.example.com': {'target_type': 'api', 'task_family_seeds': ['authz'], 'notes': ['high value', 'compare insight2.tradepmr.com']}},
        'task_family_seeds': {'api.example.com': ['authz']},
        'planner_hints': {},
        'planner_directives': {'constraints': {}, 'preferences': {}, 'unknowns': {}},
        'experiment_intents': [
            {
                'intent_id': 'intent-authz-2',
                'target': 'https://api.example.com/',
                'target_host': 'api.example.com',
                'task_family': 'authz',
                'objective': 'AuthN/AuthZ boundary probing (safe)',
                'hypothesis_candidates': ['idor', 'compare insight2.tradepmr.com role edge'],
                'open_questions': ['role inheritance unclear', 'why does insight2.tradepmr.com differ?'],
                'ambiguity_flags': ['tenant edge', 'insight2.tradepmr.com relationship'],
            }
        ],
        'aggression_profile': {'recommended_default': 5},
    }
    entries = runtime_plan_entries_from_blueprint(blueprint)
    entry = entries[0]
    assert entry['runtime_task']['hypothesis_candidates'] == ['idor']
    assert entry['planner_rationale']['open_questions'] == ['role inheritance unclear']
    assert entry['planner_rationale']['ambiguity_flags'] == ['tenant edge']


def test_runtime_plan_entries_preserve_exact_url_targets_for_authoritative_url_scope() -> None:
    blueprint = {
        'structured_scope': {
            'domains': ['www.oppo.com'],
            'authoritative_assets': [
                {'asset_kind': 'url', 'host': 'www.oppo.com', 'target': 'https://www.oppo.com/th/store', 'path_prefix': '/th/store', 'scope_source': 'authoritative'},
            ],
        },
        'target_profiles': {'www.oppo.com': {'target_type': 'web', 'task_family_seeds': ['content_discovery', 'auth_flow', 'recon'], 'surface_keywords': ['web']}},
        'task_family_seeds': {'www.oppo.com': ['content_discovery', 'auth_flow', 'recon']},
        'planner_hints': {},
        'planner_directives': {'constraints': {}, 'preferences': {}, 'unknowns': {}},
        'experiment_intents': [
            {
                'intent_id': 'intent-url-1',
                'target': 'https://www.oppo.com/th/store',
                'target_host': 'www.oppo.com',
                'target_type': 'web',
                'scope_asset_kind': 'url',
                'scope_path_prefix': '/th/store',
                'scope_source': 'authoritative',
                'task_family': 'content_discovery',
                'objective': 'Content discovery and path surface mapping',
                'capability_candidates': ['content_discovery'],
                'recommended_action_types': ['enumeration_probe', 'confirmatory_probe'],
                'hypothesis_candidates': ['content_discovery'],
                'evidence_contract': {'acceptance_checks': ['novelty_confirmation'], 'evidence_required': ['novel_endpoint_or_asset'], 'expected_signal_type': 'novel_asset_or_endpoint', 'evidence_goal_type': 'enumeration_gain'},
                'success_model': 'surface_expansion',
                'planner_constraints': {},
                'planner_preferences': {'surface_keywords': ['web'], 'scope_asset_kind': 'url', 'scope_path_prefix': '/th/store', 'scope_source': 'authoritative'},
                'ambiguity_flags': [],
                'open_questions': [],
                'runtime_task_contract': {'schema_version': 2, 'action_type': 'enumeration_probe', 'capability': 'content_discovery', 'experiment_shape': 'single_step', 'evidence_goal': 'enumeration_gain', 'exploit_ladder': {'stage': 'discovery', 'progression': ['discovery', 'validation', 'report_artifact_capture'], 'proof_strategy': 'surface_expansion_and_pivot_selection'}, 'actor_requirements': {'required': False, 'differential': False, 'preferred_roles': []}, 'session_requirements': {'stateful': False, 'auth_context': False, 'prerequisites': []}, 'promotion_policy': {'followup_allowed': True, 'confirm_preferred': False, 'bounded_only': True}, 'contamination_policy': {'learning_excluded_on_cross_host_mismatch': True, 'learning_excluded_on_hygiene_violation': True}, 'priority_tier': 'medium', 'expected_depth': 'medium', 'activation_phase': 1, 'activation_mode': 'immediate', 'conditional_gate': 'none', 'surface_role': 'primary', 'target_cluster': 'general', 'approval_sensitivity': {'owner_approval_required': False, 'auth_sensitive': False}},
                'action_type': 'enumeration_probe',
                'capability': 'content_discovery',
                'experiment_shape': 'single_step',
                'evidence_goal': 'enumeration_gain',
                'exploit_ladder': {'stage': 'discovery'},
                'actor_requirements': {'required': False, 'differential': False},
                'session_requirements': {'stateful': False, 'auth_context': False},
                'promotion_policy': {'followup_allowed': True, 'confirm_preferred': False, 'bounded_only': True},
                'contamination_policy': {'learning_excluded_on_cross_host_mismatch': True, 'learning_excluded_on_hygiene_violation': True},
                'approval_sensitivity': {'owner_approval_required': False, 'auth_sensitive': False},
            }
        ],
        'aggression_profile': {'recommended_default': 5},
    }
    entries = runtime_plan_entries_from_blueprint(blueprint)
    assert len(entries) == 1
    assert entries[0]['target'] == 'https://www.oppo.com/th/store'
    assert entries[0]['runtime_task']['target'] == 'https://www.oppo.com/th/store'
    assert entries[0]['scope_asset_kind'] == 'url'
    assert entries[0]['scope_path_prefix'] == '/th/store'


def test_runtime_plan_entries_reject_broadened_host_target_when_scope_is_exact_url_only() -> None:
    blueprint = {
        'structured_scope': {
            'domains': ['www.oppo.com'],
            'authoritative_assets': [
                {'asset_kind': 'url', 'host': 'www.oppo.com', 'target': 'https://www.oppo.com/th/store', 'path_prefix': '/th/store', 'scope_source': 'authoritative'},
            ],
        },
        'target_profiles': {'www.oppo.com': {'target_type': 'web', 'task_family_seeds': ['content_discovery']}},
        'task_family_seeds': {'www.oppo.com': ['content_discovery']},
        'planner_hints': {},
        'planner_directives': {'constraints': {}, 'preferences': {}, 'unknowns': {}},
        'experiment_intents': [
            {
                'intent_id': 'intent-url-bad',
                'target': 'https://www.oppo.com/',
                'target_host': 'www.oppo.com',
                'target_type': 'web',
                'task_family': 'content_discovery',
                'objective': 'Content discovery and path surface mapping',
                'capability_candidates': ['content_discovery'],
                'recommended_action_types': ['enumeration_probe'],
                'evidence_contract': {'acceptance_checks': ['novelty_confirmation'], 'evidence_required': ['novel_endpoint_or_asset'], 'expected_signal_type': 'novel_asset_or_endpoint', 'evidence_goal_type': 'enumeration_gain'},
                'success_model': 'surface_expansion',
                'planner_constraints': {},
                'planner_preferences': {'surface_keywords': ['web']},
                'ambiguity_flags': [],
                'open_questions': [],
                'runtime_task_contract': {'schema_version': 2, 'action_type': 'enumeration_probe', 'capability': 'content_discovery', 'experiment_shape': 'single_step', 'evidence_goal': 'enumeration_gain', 'exploit_ladder': {'stage': 'discovery', 'progression': ['discovery', 'report_artifact_capture'], 'proof_strategy': 'surface_expansion_and_pivot_selection'}, 'actor_requirements': {'required': False, 'differential': False, 'preferred_roles': []}, 'session_requirements': {'stateful': False, 'auth_context': False, 'prerequisites': []}, 'promotion_policy': {'followup_allowed': False, 'confirm_preferred': False, 'bounded_only': True}, 'contamination_policy': {'learning_excluded_on_cross_host_mismatch': True, 'learning_excluded_on_hygiene_violation': True}, 'priority_tier': 'medium', 'expected_depth': 'medium', 'activation_phase': 1, 'activation_mode': 'immediate', 'conditional_gate': 'none', 'surface_role': 'primary', 'target_cluster': 'general', 'approval_sensitivity': {'owner_approval_required': False, 'auth_sensitive': False}},
                'action_type': 'enumeration_probe',
                'capability': 'content_discovery',
                'experiment_shape': 'single_step',
                'evidence_goal': 'enumeration_gain',
                'exploit_ladder': {'stage': 'discovery'},
                'actor_requirements': {'required': False, 'differential': False},
                'session_requirements': {'stateful': False, 'auth_context': False},
                'promotion_policy': {'followup_allowed': False, 'confirm_preferred': False, 'bounded_only': True},
                'contamination_policy': {'learning_excluded_on_cross_host_mismatch': True, 'learning_excluded_on_hygiene_violation': True},
                'approval_sensitivity': {'owner_approval_required': False, 'auth_sensitive': False},
            }
        ],
        'aggression_profile': {'recommended_default': 5},
    }
    entries = runtime_plan_entries_from_blueprint(blueprint)
    assert entries == []


def test_write_runtime_plan_target_count_tracks_unique_scoped_targets_not_unique_hosts(tmp_path: Path, monkeypatch) -> None:
    runtime_plan_path = tmp_path / 'state' / 'public_targets_plan.json'
    legacy_runtime_plan_path = tmp_path / 'public_targets_plan.json'
    runtime_plan_meta_path = tmp_path / '.runtime_plan.meta.json'
    monkeypatch.setattr(rps, 'RUNTIME_PLAN_PATH', runtime_plan_path)
    monkeypatch.setattr(rps, 'LEGACY_RUNTIME_PLAN_PATH', legacy_runtime_plan_path)
    monkeypatch.setattr(rps, 'RUNTIME_PLAN_META_PATH', runtime_plan_meta_path)

    entries = [
        {'target': 'https://www.oppo.com/th/store', 'objective': 'a', 'task_family': 'content_discovery'},
        {'target': 'https://www.oppo.com/th', 'objective': 'b', 'task_family': 'content_discovery'},
        {'target': 'https://www.oppo.com/th/store', 'objective': 'c', 'task_family': 'auth_flow'},
        {'target': 'id.oppo.com', 'objective': 'd', 'task_family': 'recon'},
    ]
    res = rps.write_runtime_plan(entries, 'camp-truth', reason='unit_test')
    assert res['ok'] is True
    assert res['generated'] == 4
    assert res['target_count'] == 3
    assert res['input_total'] == 3

    meta = json.loads(runtime_plan_meta_path.read_text(encoding='utf-8'))
    assert meta['target_count'] == 3
    assert meta['input_total'] == 3


def test_runtime_plan_entries_preserve_distinct_experiment_intent_ids_even_when_host_family_and_objective_match() -> None:
    blueprint = {
        'structured_scope': {'domains': ['api.example.com']},
        'target_profiles': {'api.example.com': {'target_type': 'api', 'task_family_seeds': ['authz']}},
        'task_family_seeds': {'api.example.com': ['authz']},
        'planner_hints': {},
        'planner_directives': {'constraints': {}, 'preferences': {}, 'unknowns': {}},
        'experiment_intents': [
            {
                'intent_id': 'intent-authz-a',
                'target': 'https://api.example.com/',
                'target_host': 'api.example.com',
                'target_type': 'api',
                'task_family': 'authz',
                'objective': 'AuthN/AuthZ boundary probing (safe)',
                'capability_candidates': ['http_probe'],
                'recommended_action_types': ['differential_probe'],
                'hypothesis_candidates': ['idor'],
                'evidence_contract': {'acceptance_checks': ['negative_control'], 'evidence_required': ['response_diff']},
                'success_model': 'differential_or_stateful_signal',
                'planner_constraints': {},
                'planner_preferences': {'preferred_vector_families': ['authz']},
                'ambiguity_flags': [],
                'open_questions': ['tenant edge'],
            },
            {
                'intent_id': 'intent-authz-b',
                'target': 'https://api.example.com/',
                'target_host': 'api.example.com',
                'target_type': 'api',
                'task_family': 'authz',
                'objective': 'AuthN/AuthZ boundary probing (safe)',
                'capability_candidates': ['http_probe'],
                'recommended_action_types': ['confirmatory_probe'],
                'hypothesis_candidates': ['role edge'],
                'evidence_contract': {'acceptance_checks': ['negative_control'], 'evidence_required': ['response_diff']},
                'success_model': 'differential_or_stateful_signal',
                'planner_constraints': {},
                'planner_preferences': {'preferred_vector_families': ['authz']},
                'ambiguity_flags': [],
                'open_questions': ['role inheritance'],
            },
        ],
        'aggression_profile': {'recommended_default': 5, 'recommended_min': 3, 'recommended_max': 7},
    }
    entries = runtime_plan_entries_from_blueprint(blueprint)
    assert len(entries) == 2
    assert {e['planner_rationale']['experiment_intent_id'] for e in entries} == {'intent-authz-a', 'intent-authz-b'}


def test_runtime_plan_entries_dedupe_duplicate_experiment_intent_id() -> None:
    blueprint = {
        'structured_scope': {'domains': ['api.example.com']},
        'target_profiles': {'api.example.com': {'target_type': 'api', 'task_family_seeds': ['authz']}},
        'task_family_seeds': {'api.example.com': ['authz']},
        'planner_hints': {},
        'planner_directives': {'constraints': {}, 'preferences': {}, 'unknowns': {}},
        'experiment_intents': [
            {
                'intent_id': 'intent-authz-dup',
                'target': 'https://api.example.com/',
                'target_host': 'api.example.com',
                'target_type': 'api',
                'task_family': 'authz',
                'objective': 'AuthN/AuthZ boundary probing (safe)',
                'capability_candidates': ['http_probe'],
                'recommended_action_types': ['differential_probe'],
                'hypothesis_candidates': ['idor'],
                'evidence_contract': {'acceptance_checks': ['negative_control'], 'evidence_required': ['response_diff']},
                'success_model': 'differential_or_stateful_signal',
                'planner_constraints': {},
                'planner_preferences': {'preferred_vector_families': ['authz']},
                'ambiguity_flags': [],
                'open_questions': ['tenant edge'],
            },
            {
                'intent_id': 'intent-authz-dup',
                'target': 'https://api.example.com/',
                'target_host': 'api.example.com',
                'target_type': 'api',
                'task_family': 'authz',
                'objective': 'AuthN/AuthZ boundary probing (safe)',
                'capability_candidates': ['http_probe'],
                'recommended_action_types': ['confirmatory_probe'],
                'hypothesis_candidates': ['role edge'],
                'evidence_contract': {'acceptance_checks': ['negative_control'], 'evidence_required': ['response_diff']},
                'success_model': 'differential_or_stateful_signal',
                'planner_constraints': {},
                'planner_preferences': {'preferred_vector_families': ['authz']},
                'ambiguity_flags': [],
                'open_questions': ['role inheritance'],
            },
        ],
        'aggression_profile': {'recommended_default': 5, 'recommended_min': 3, 'recommended_max': 7},
    }
    entries = runtime_plan_entries_from_blueprint(blueprint)
    assert len(entries) == 1
    assert entries[0]['planner_rationale']['experiment_intent_id'] == 'intent-authz-dup'


def test_runtime_plan_entries_sanitize_legacy_hint_text_per_host() -> None:
    blueprint = {
        'structured_scope': {'domains': ['api.example.com']},
        'target_profiles': {'api.example.com': {'target_type': 'api', 'task_family_seeds': ['authz'], 'notes': ['high value', 'compare insight2.tradepmr.com']}},
        'task_family_seeds': {'api.example.com': ['authz']},
        'planner_hints': {'per_target_vectors': {'api.example.com': ['authz']}, 'ambiguities': ['tenant edge', 'insight2.tradepmr.com relation'], 'interpretation_conflicts': ['api/web', 'bitstamp vs insight2.tradepmr.com']},
        'planner_directives': {'constraints': {}, 'preferences': {}, 'unknowns': {}},
        'aggression_profile': {'recommended_default': 5},
    }
    entries = runtime_plan_entries_from_blueprint(blueprint)
    entry = entries[0]
    assert entry['planner_rationale']['ambiguity_flags'] == ['tenant edge']
    assert entry['planner_rationale']['interpretation_conflicts'] == ['api/web']


def test_runtime_plan_entries_mark_legacy_fallback_when_experiment_intents_exist_but_none_survive() -> None:
    blueprint = {
        'structured_scope': {'domains': ['api.example.com']},
        'target_profiles': {'api.example.com': {'target_type': 'api', 'task_family_seeds': ['authz']}},
        'task_family_seeds': {'api.example.com': ['authz']},
        'planner_hints': {'per_target_vectors': {'api.example.com': ['authz']}},
        'planner_directives': {'constraints': {}, 'preferences': {}, 'unknowns': {}},
        'experiment_intents': [
            {
                'intent_id': 'intent-out-of-scope',
                'target': 'https://elsewhere.example.net/',
                'target_host': 'elsewhere.example.net',
                'target_type': 'api',
                'task_family': 'authz',
                'objective': 'AuthN/AuthZ boundary probing (safe)',
                'capability_candidates': ['http_probe'],
                'recommended_action_types': ['differential_probe'],
                'hypothesis_candidates': ['idor'],
                'evidence_contract': {'acceptance_checks': ['negative_control'], 'evidence_required': ['response_diff']},
                'success_model': 'differential_or_stateful_signal',
                'planner_constraints': {},
                'planner_preferences': {'preferred_vector_families': ['authz']},
                'ambiguity_flags': [],
                'open_questions': [],
            },
        ],
        'aggression_profile': {'recommended_default': 5, 'recommended_min': 3, 'recommended_max': 7},
    }
    entries = runtime_plan_entries_from_blueprint(blueprint)
    assert entries
    assert entries[0]['planner_input_source'] == 'legacy_seed_synthesis_after_empty_experiment_intents'
    assert entries[0]['planner_rationale']['planner_input_source'] == 'legacy_seed_synthesis_after_empty_experiment_intents'
    assert entries[0]['runtime_task']['planner_input_source'] == 'legacy_seed_synthesis_after_empty_experiment_intents'


def test_write_runtime_plan_persists_planner_input_source_summary(tmp_path: Path, monkeypatch) -> None:
    runtime_plan_path = tmp_path / 'reports' / 'state' / 'public_targets_plan.json'
    legacy_runtime_plan_path = tmp_path / 'engine' / 'public_targets_plan.json'
    runtime_plan_meta_path = tmp_path / '.runtime_plan.meta.json'
    monkeypatch.setattr(rps, 'RUNTIME_PLAN_PATH', runtime_plan_path)
    monkeypatch.setattr(rps, 'LEGACY_RUNTIME_PLAN_PATH', legacy_runtime_plan_path)
    monkeypatch.setattr(rps, 'RUNTIME_PLAN_META_PATH', runtime_plan_meta_path)

    entries = [
        {
            'target': 'https://api.example.com/',
            'objective': 'AuthN/AuthZ boundary probing (safe)',
            'task_family': 'authz',
            'planner_input_source': 'experiment_intent_canonical',
        },
        {
            'target': 'https://app.example.com/',
            'objective': 'Passive recon and endpoint discovery',
            'task_family': 'recon',
            'planner_input_source': 'legacy_seed_synthesis_after_empty_experiment_intents',
        },
    ]
    out = rps.write_runtime_plan(entries, 'camp1', reason='manual_or_ui')
    assert out['ok'] is True
    assert out['planner_input_sources'] == ['experiment_intent_canonical', 'legacy_seed_synthesis_after_empty_experiment_intents']
    assert out['planner_input_source_counts']['experiment_intent_canonical'] == 1
    assert out['planner_input_source_counts']['legacy_seed_synthesis_after_empty_experiment_intents'] == 1

    assert runtime_plan_path.exists()
    assert legacy_runtime_plan_path.exists()
    assert json.loads(runtime_plan_path.read_text(encoding='utf-8')) == json.loads(legacy_runtime_plan_path.read_text(encoding='utf-8'))

    meta = json.loads(runtime_plan_meta_path.read_text(encoding='utf-8'))
    assert meta['planner_input_sources'] == ['experiment_intent_canonical', 'legacy_seed_synthesis_after_empty_experiment_intents']
    assert meta['planner_input_source_counts']['experiment_intent_canonical'] == 1
