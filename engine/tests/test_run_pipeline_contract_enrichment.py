from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import run_pipeline as rp  # type: ignore
import runtime_plan_service as rps  # type: ignore


def test_compact_recent_context_includes_reason_and_next_family() -> None:
    out = rp.compact_recent_context([
        {
            'timestamp': '2026-03-12T20:00:00+00:00',
            'objective': 'Probe',
            'target': 'https://api.example.com/',
            'status': 'ok',
            'returncode': 0,
            'auditor_decision': 'approve',
            'reason_code': 'interesting_signal',
            'task_family': 'authz',
            'analysis': {'next_family_hint': 'logic', 'success_criteria_eval': 'partial'},
        }
    ])
    assert out[0]['reason_code'] == 'interesting_signal'
    assert out[0]['next_family_hint'] == 'logic'
    assert out[0]['success_eval'] == 'partial'


def test_compact_recent_context_prefers_same_host_for_target() -> None:
    out = rp.compact_recent_context([
        {'timestamp': '2026-03-12T20:00:00+00:00', 'objective': 'Other', 'target': 'https://elsewhere.example.net/', 'status': 'ok'},
        {'timestamp': '2026-03-12T20:01:00+00:00', 'objective': 'Same', 'target': 'https://api.example.com/', 'status': 'ok'},
    ], target='https://api.example.com/')
    assert len(out) == 1
    assert out[0]['target'] == 'https://api.example.com/'


def test_summarize_recent_runtime_state_tracks_host_family_and_blocking() -> None:
    summary = rp.summarize_recent_runtime_state([
        {'target': 'https://api.example.com/', 'task_family': 'authz', 'auditor_decision': 'approve', 'reason_code': 'engine_success', 'analysis': {'success_criteria_eval': 'partial', 'next_family_hint': 'logic'}},
        {'target': 'https://api.example.com/', 'task_family': 'authz', 'auditor_decision': 'owner_approval_required', 'reason_code': 'policy_gate_block', 'analysis': {'success_criteria_eval': 'not_met'}},
    ], target='https://api.example.com/', task_family='authz')
    assert summary['same_host_recent'] == 2
    assert summary['same_family_recent'] == 2
    assert summary['blocked_recent'] == 1
    assert summary['partial_recent'] == 1
    assert summary['recent_next_family_hints'] == ['logic']


def test_load_planner_hints_exposes_target_specific_fields(tmp_path: Path, monkeypatch) -> None:
    registry = tmp_path / 'campaign_registry' / 'camp1'
    version = registry / 'v1'
    version.mkdir(parents=True)
    (registry / 'latest.json').write_text('{"path": "%s"}' % str(version), encoding='utf-8')
    (version / 'blueprint.json').write_text(
        '{"planner_hints": {"global_vectors": ["idor"], "recommended_task_families": ["authz"], "deprioritized_task_families": ["secret_hunt"], "per_target_vectors": {"api.example.com": ["authz"]}, "ambiguities": ["tenant edge", "compare with insight2.tradepmr.com"], "interpretation_conflicts": ["api/web", "bitstamp vs insight2.tradepmr.com"], "candidate_targets": ["https://api.example.com/", "https://elsewhere.example.net/"], "llm_confidence": 0.7}, "aggression_profile": {"recommended_default": 5, "recommended_min": 3, "recommended_max": 7}, "target_profiles": {"api.example.com": {"target_type": "api", "surface_keywords": ["json"], "task_family_seeds": ["authz"], "candidate_vectors": ["idor"], "notes": ["high value", "shares behavior with insight2.tradepmr.com"]}}}',
        encoding='utf-8'
    )
    monkeypatch.setattr(rps, 'PLANNER_REGISTRY_ROOT', tmp_path / 'campaign_registry')
    monkeypatch.setattr(rp, 'resolve_campaign_key', lambda selected_key='': 'camp1')
    hints = rp.load_planner_hints(target='https://api.example.com/', task_family='authz')
    assert hints['resolved_campaign_key'] == 'camp1'
    assert hints['preferred_vectors_for_target'] == ['authz']
    assert hints['deprioritized_task_families'] == ['secret_hunt']
    assert hints['target_profile']['target_type'] == 'api'
    assert hints['target_profile']['notes'] == ['high value']
    assert hints['candidate_targets'] == ['https://api.example.com/']
    assert hints['ambiguities'] == ['tenant edge']
    assert hints['interpretation_conflicts'] == ['api/web']
    assert hints['task_family_context']['preferred_for_target_match'] is True


def test_load_planner_hints_uses_active_campaign_binding_not_latest_mtime(tmp_path: Path, monkeypatch) -> None:
    registry_root = tmp_path / 'campaign_registry'
    camp1 = registry_root / 'camp1'
    camp2 = registry_root / 'camp2'
    v1 = camp1 / 'v1'
    v2 = camp2 / 'v1'
    v1.mkdir(parents=True)
    v2.mkdir(parents=True)
    (camp1 / 'latest.json').write_text('{"path": "%s"}' % str(v1), encoding='utf-8')
    (camp2 / 'latest.json').write_text('{"path": "%s"}' % str(v2), encoding='utf-8')
    (v1 / 'blueprint.json').write_text(
        '{"planner_hints": {"global_vectors": ["authz"]}, "aggression_profile": {}, "target_profiles": {"api.example.com": {"type": "api", "task_family_seeds": ["authz"]}}}',
        encoding='utf-8',
    )
    (v2 / 'blueprint.json').write_text(
        '{"planner_hints": {"global_vectors": ["recon"]}, "aggression_profile": {}, "target_profiles": {"api.example.com": {"target_type": "web", "task_family_seeds": ["recon"]}}}',
        encoding='utf-8',
    )
    monkeypatch.setattr(rps, 'PLANNER_REGISTRY_ROOT', registry_root)
    monkeypatch.setattr(rp, 'resolve_campaign_key', lambda selected_key='': 'camp1')
    hints = rp.load_planner_hints(target='https://api.example.com/', task_family='authz')
    assert hints['resolved_campaign_key'] == 'camp1'
    assert hints['suggested_attack_vectors'] == ['authz']
    assert hints['target_profile']['target_type'] == 'api'


def test_merge_intent_runtime_context_collects_cli_fields() -> None:
    args = argparse.Namespace(
        experiment_intent_id='intent-123',
        capability_candidates_json='["http_probe","response_diff"]',
        recommended_action_types_json='["differential_probe"]',
        hypothesis_candidates_json='["idor","tenant edge","compare insight2.tradepmr.com authz"]',
        planner_constraints_json='{"campaign_bound_context": true}',
        planner_preferences_json='{"preferred_vector_families": ["authz"]}',
        open_questions_json='["role inheritance unclear","why does insight2.tradepmr.com differ?"]',
    )
    merged = rp._merge_intent_runtime_context(args, {'target_profile': {'target_type': 'api', 'notes': ['high value', 'see insight2.tradepmr.com']}, 'preferred_vectors_for_target': ['authz'], 'ambiguities': ['tenant edge', 'compare insight2.tradepmr.com'], 'interpretation_conflicts': ['api/web', 'bitstamp vs insight2.tradepmr.com']}, target='https://api.example.com/')
    assert merged['experiment_intent_id'] == 'intent-123'
    assert merged['capability_candidates'] == ['http_probe', 'response_diff']
    assert merged['recommended_action_types'] == ['differential_probe']
    assert merged['planner_constraints']['campaign_bound_context'] is True
    assert merged['planner_constraints']['target_host_binding'] == 'api.example.com'
    assert merged['planner_preferences']['preferred_vector_families'] == ['authz']
    assert merged['open_questions'] == ['role inheritance unclear']
    assert merged['hypothesis_candidates'] == ['idor', 'tenant edge']
    assert merged['ambiguities'] == ['tenant edge']
    assert merged['interpretation_conflicts'] == ['api/web']
    assert merged['target_profile']['notes'] == ['high value']


def test_apply_intent_guidance_to_brain_backfills_capability_and_action_type(monkeypatch) -> None:
    monkeypatch.setattr(rp, 'preferred_tools_for_task_family', lambda *args, **kwargs: ['curl'])
    guided = rp.apply_intent_guidance_to_brain(
        {'intent': 'probe', 'target': 'https://api.example.com/'},
        {
            'experiment_intent_id': 'intent-123',
            'capability_candidates': ['http_probe'],
            'recommended_action_types': ['differential_probe'],
            'hypothesis_candidates': ['idor'],
            'planner_constraints': {'campaign_bound_context': True},
            'planner_preferences': {'preferred_vector_families': ['authz']},
        },
        objective='Probe target',
        target='https://api.example.com/',
        aggression=2,
        task_family='authz',
        recent_context=[],
    )
    assert guided['action_type'] == 'differential_probe'
    assert guided['capability'] == 'http_probe'
    assert guided['hypothesis'] == 'idor'
    assert guided['tool_preferences']['prefer_tool'] == 'curl'
    assert guided['experiment_intent_id'] == 'intent-123'
    assert guided['planner_alignment'] == 'aligned'


def test_apply_intent_guidance_to_brain_replaces_invalid_capability_with_intent_candidate(monkeypatch) -> None:
    monkeypatch.setattr(rp, 'preferred_tools_for_task_family', lambda *args, **kwargs: ['curl'])
    guided = rp.apply_intent_guidance_to_brain(
        {
            'intent': 'probe',
            'target': 'https://api.example.com/',
            'capability': 'single-request http/tls header fingerprinting',
            'action_type': 'fingerprint_probe',
            'experiment_shape': 'fingerprint_probe',
        },
        {
            'capability_candidates': ['http_fingerprint', 'service_enumeration'],
            'recommended_action_types': ['fingerprint_probe'],
        },
        objective='Probe target',
        target='https://api.example.com/',
        aggression=2,
        task_family='recon',
        recent_context=[],
    )
    assert guided['capability'] == 'http_fingerprint'
    assert guided['action_type'] == 'fingerprint_probe'
    assert guided['experiment_shape'] == 'fingerprint'


def test_build_raw_action_spec_maps_action_type_to_valid_experiment_shape() -> None:
    args = argparse.Namespace(
        target='https://api.example.com/',
        task_success_criteria='',
        campaign_success_criteria='',
    )
    raw = rp._build_raw_action_spec(
        {
            'action_type': 'fingerprint_probe',
            'capability': 'http_fingerprint',
            'tool': 'httpx',
            'args': ['https://api.example.com/'],
        },
        args=args,
        task_family='recon',
        execution_mode='safe',
        intent_runtime_context={},
    )
    assert raw['experiment_shape'] == 'fingerprint'
    assert raw['capability'] == 'http_fingerprint'


def test_build_raw_action_spec_demotes_explicit_tool_to_preference_in_normalized_mode() -> None:
    args = argparse.Namespace(
        target='https://api.example.com/',
        task_success_criteria='',
        campaign_success_criteria='',
    )
    raw = rp._build_raw_action_spec(
        {
            'action_type': 'single_probe',
            'capability': 'http_probe',
            'tool': 'curl',
            'args': ['https://api.example.com/'],
            'resolved_planner_profiles': ['core', 'extended'],
        },
        args=args,
        task_family='recon',
        execution_mode='normalized',
        intent_runtime_context={},
    )
    assert raw['tool'] == ''
    assert raw['tool_preferences']['prefer_tool'] == 'curl'
    assert raw['realization_decoupled'] is True


def test_build_raw_action_spec_keeps_explicit_tool_outside_normalized_mode() -> None:
    args = argparse.Namespace(
        target='https://api.example.com/',
        task_success_criteria='',
        campaign_success_criteria='',
    )
    raw = rp._build_raw_action_spec(
        {
            'action_type': 'single_probe',
            'capability': 'http_probe',
            'tool': 'curl',
            'args': ['https://api.example.com/'],
            'resolved_planner_profiles': ['core', 'extended'],
        },
        args=args,
        task_family='recon',
        execution_mode='safe',
        intent_runtime_context={},
    )
    assert raw['tool'] == 'curl'
    assert raw.get('realization_decoupled') is None


def test_build_raw_action_spec_normalizes_bounded_hypothesis_fanout() -> None:
    args = argparse.Namespace(
        target='https://api.example.com/',
        task_success_criteria='',
        campaign_success_criteria='',
    )
    raw = rp._build_raw_action_spec(
        {
            'action_type': 'single_probe',
            'capability': 'http_probe',
            'tool': 'curl',
            'args': ['https://api.example.com/'],
            'hypothesis': 'primary boundary probe',
            'resolved_planner_profiles': ['core', 'extended'],
            'sibling_hypotheses': [
                {'hypothesis': 'header differential variant', 'action_type': 'variant_probe', 'capability': 'http_probe', 'expected_signal': 'header-dependent delta', 'evidence_goal': 'differential response', 'tool': 'curl'},
                {'hypothesis': 'content-type differential', 'action_type': 'variant_probe', 'capability': 'http_probe', 'expected_signal': 'parser differential', 'evidence_goal': 'status/body divergence', 'prefer_tool': 'httpx'},
                {'hypothesis': 'should be clipped', 'action_type': 'variant_probe', 'capability': 'http_probe'},
            ],
        },
        args=args,
        task_family='authz',
        execution_mode='normalized',
        intent_runtime_context={},
    )
    assert raw['primary_hypothesis'] == 'primary boundary probe'
    assert raw['hypothesis_fanout_count'] == 2
    assert len(raw['hypothesis_fanout']) == 2
    assert raw['hypothesis_fanout'][0]['hypothesis'] == 'header differential variant'
    assert raw['hypothesis_fanout'][1]['hypothesis'] == 'content-type differential'
    assert raw['hypothesis_fanout_source'] == 'explicit_plus_motif'
    assert raw['hypothesis_fanout_summary']['fanout_count'] == 2
    assert raw['hypothesis_fanout_summary']['capability_diversity'] >= 1
    assert raw['hypothesis_fanout_summary']['action_diversity'] >= 1


def test_build_raw_action_spec_backfills_fanout_from_family_motifs() -> None:
    args = argparse.Namespace(
        target='https://api.example.com/',
        task_success_criteria='',
        campaign_success_criteria='',
    )
    raw = rp._build_raw_action_spec(
        {
            'action_type': 'single_probe',
            'capability': 'http_probe',
            'tool': 'curl',
            'args': ['https://api.example.com/'],
            'hypothesis': 'primary boundary probe',
            'resolved_planner_profiles': ['core', 'extended'],
        },
        args=args,
        task_family='authz',
        execution_mode='normalized',
        intent_runtime_context={},
    )
    assert raw['hypothesis_fanout_count'] == 2
    assert raw['hypothesis_fanout_source'] == 'motif_backfill'
    assert all(item['hypothesis'] != 'primary boundary probe' for item in raw['hypothesis_fanout'])


def test_build_auditor_prompt_prioritizes_canonical_prepared_spec() -> None:
    prepared = {
        'spec_version': '2026-03-18.prepared.v1',
        'target': 'https://api.example.com/',
        'target_host': 'api.example.com',
        'target_in_scope': True,
        'task_family': 'recon',
        'action_type': 'single_probe',
        'capability': 'http_probe',
        'execution_mode': 'normalized',
        'resolved_tool': 'curl',
        'resolved_planner_profiles': ['core'],
        'normalized_args': ['-I', 'https://api.example.com/'],
        'execution_plan': [{'tool': 'curl', 'role': 'probe', 'args': ['-I', 'https://api.example.com/']}],
        'request_decoration': {'headers': [{'name': 'X-Bug-Bounty', 'value': 'hunter1'}]},
        'scope_facts': {'target_in_scope': True},
        'credentials_policy_snapshot': {'credentials_required': True},
        'arg_hosts_detected': ['api.example.com'],
        'execution_plan_hosts_detected': ['api.example.com'],
        'all_hosts_detected': ['api.example.com'],
        'mismatched_hosts_detected': [],
        'target_host_match_status': 'exact',
        'request_shape_hygiene_status': 'clean',
        'request_shape_hygiene_reason': 'all_detected_hosts_match_target',
        'request_shape_hygiene_source': 'normalized_args+execution_plan',
        'compiler': {'semantic_loss_policy': {'policy_response': 'proceed'}},
    }
    compact = rp._compact_prepared_execution_spec_for_auditor(prepared)
    context = rp._build_auditor_context_summary(
        args=argparse.Namespace(
            objective='Probe target',
            target='https://api.example.com/',
            task_family='recon',
            aggression=2,
            owner_override=False,
            owner_approved_auth=False,
            task_success_criteria='',
            campaign_success_criteria='',
            acceptance_checks='',
            evidence_required='',
        ),
        target_in_scope=True,
        recent_runtime_summary='same_host_recent=0',
        planner_hints={'preferred_vectors_for_target': ['recon'], 'target_profile': {'target_type': 'api'}},
        brain_reasoning={'hypothesis': 'host reachable', 'why_now': 'baseline', 'expected_signal': 'headers', 'evidence_goal': 'baseline evidence', 'planner_alignment': 'aligned', 'redundancy_risk': 'low'},
        semantic_loss_policy={'policy_response': 'proceed'},
        intent_runtime_context={'experiment_intent_id': 'intent-1', 'capability_candidates': ['http_probe']},
    )
    prompt = rp._build_auditor_prompt(prepared_execution_spec=compact, context_summary=context)
    assert 'CANONICAL_PREPARED_EXECUTION_SPEC=' in prompt
    assert 'DECISION_CONTEXT=' in prompt
    assert prompt.index('CANONICAL_PREPARED_EXECUTION_SPEC=') < prompt.index('DECISION_CONTEXT=')
    assert 'If the CANONICAL_PREPARED_EXECUTION_SPEC block is present, do not claim it is missing.' in prompt
    canon_line = prompt.split('CANONICAL_PREPARED_EXECUTION_SPEC=', 1)[1].split('\nDECISION_CONTEXT=', 1)[0]
    canon = json.loads(canon_line)
    assert canon['target'] == 'https://api.example.com/'
    assert canon['resolved_tool'] == 'curl'
    assert canon['target_in_scope'] is True
    assert canon['arg_hosts_detected'] == ['api.example.com']
    assert canon['target_host_match_status'] == 'exact'
    assert canon['request_shape_hygiene_status'] == 'clean'


def test_compact_prepared_execution_spec_preserves_execution_plan_only_mismatch_fields() -> None:
    prepared = {
        'target': 'https://www.bitstamp.net/',
        'target_host': 'www.bitstamp.net',
        'target_in_scope': True,
        'resolved_tool': 'curl',
        'normalized_args': ['curl', '--max-time', '5'],
        'execution_plan': [{'tool': 'curl', 'role': 'probe', 'args': ['https://insight2.tradepmr.com/health']}],
        'request_decoration': {},
        'scope_facts': {'target_in_scope': True},
        'credentials_policy_snapshot': {},
        'arg_hosts_detected': [],
        'execution_plan_hosts_detected': ['insight2.tradepmr.com'],
        'all_hosts_detected': ['insight2.tradepmr.com'],
        'mismatched_hosts_detected': ['insight2.tradepmr.com'],
        'target_host_match_status': 'mixed',
        'request_shape_hygiene_status': 'cross_host_mismatch',
        'request_shape_hygiene_reason': 'mismatched_hosts_detected:insight2.tradepmr.com',
        'request_shape_hygiene_source': 'execution_plan',
        'compiler': {},
    }
    compact = rp._compact_prepared_execution_spec_for_auditor(prepared)
    assert compact['arg_hosts_detected'] == []
    assert compact['execution_plan_hosts_detected'] == ['insight2.tradepmr.com']
    assert compact['mismatched_hosts_detected'] == ['insight2.tradepmr.com']
    assert compact['target_host_match_status'] == 'mixed'
    assert compact['request_shape_hygiene_status'] == 'cross_host_mismatch'
    assert compact['request_shape_hygiene_source'] == 'execution_plan'


def test_request_shape_hygiene_record_and_context_summary_are_deterministic() -> None:
    prepared = {
        'target_host': 'www.bitstamp.net',
        'arg_hosts_detected': ['insight2.tradepmr.com'],
        'execution_plan_hosts_detected': ['insight2.tradepmr.com'],
        'all_hosts_detected': ['insight2.tradepmr.com'],
        'mismatched_hosts_detected': ['insight2.tradepmr.com'],
        'target_host_match_status': 'mixed',
        'request_shape_hygiene_status': 'cross_host_mismatch',
        'request_shape_hygiene_reason': 'mismatched_hosts_detected:insight2.tradepmr.com',
        'request_shape_hygiene_source': 'normalized_args+execution_plan',
    }
    hygiene = rp._request_shape_hygiene_record(prepared)
    assert hygiene['deterministic'] is True
    assert hygiene['classification_timing'] == 'pre_auditor'
    assert hygiene['request_shape_hygiene_status'] == 'cross_host_mismatch'
    context = rp._build_auditor_context_summary(
        args=argparse.Namespace(
            objective='Probe target',
            target='https://www.bitstamp.net/',
            task_family='recon',
            aggression=2,
            owner_override=False,
            owner_approved_auth=False,
            task_success_criteria='',
            campaign_success_criteria='',
            acceptance_checks='',
            evidence_required='',
        ),
        target_in_scope=True,
        recent_runtime_summary='same_host_recent=0',
        planner_hints={'preferred_vectors_for_target': [], 'target_profile': {}},
        brain_reasoning={'hypothesis': '', 'why_now': '', 'expected_signal': '', 'evidence_goal': '', 'planner_alignment': 'aligned', 'redundancy_risk': 'low'},
        semantic_loss_policy={'policy_response': 'proceed'},
        intent_runtime_context={'experiment_intent_id': 'intent-2', 'capability_candidates': ['http_probe']},
        request_shape_hygiene=hygiene,
    )
    assert context['request_shape_hygiene']['classification_timing'] == 'pre_auditor'
    assert context['request_shape_hygiene']['request_shape_hygiene_status'] == 'cross_host_mismatch'
    assert context['request_shape_hygiene']['mismatched_hosts_detected'] == ['insight2.tradepmr.com']


def test_request_shape_hygiene_context_handles_ambiguous_non_host_case() -> None:
    hygiene = rp._request_shape_hygiene_record({
        'target_host': 'api.example.com',
        'arg_hosts_detected': [],
        'execution_plan_hosts_detected': [],
        'all_hosts_detected': [],
        'mismatched_hosts_detected': [],
        'target_host_match_status': 'none_detected',
        'request_shape_hygiene_status': 'ambiguous',
        'request_shape_hygiene_reason': 'no_hosts_detected_in_prepared_shape',
        'request_shape_hygiene_source': 'none',
    })
    context = rp._build_auditor_context_summary(
        args=argparse.Namespace(
            objective='Probe target',
            target='https://api.example.com/',
            task_family='recon',
            aggression=2,
            owner_override=False,
            owner_approved_auth=False,
            task_success_criteria='',
            campaign_success_criteria='',
            acceptance_checks='',
            evidence_required='',
        ),
        target_in_scope=True,
        recent_runtime_summary='same_host_recent=0',
        planner_hints={'preferred_vectors_for_target': [], 'target_profile': {}},
        brain_reasoning={'hypothesis': '', 'why_now': '', 'expected_signal': '', 'evidence_goal': '', 'planner_alignment': 'aligned', 'redundancy_risk': 'low'},
        semantic_loss_policy={'policy_response': 'proceed'},
        intent_runtime_context={'experiment_intent_id': 'intent-3'},
        request_shape_hygiene=hygiene,
    )
    assert context['request_shape_hygiene']['request_shape_hygiene_status'] == 'ambiguous'
    assert context['request_shape_hygiene']['target_host_match_status'] == 'none_detected'
    assert context['request_shape_hygiene']['mismatched_hosts_detected'] == []


def test_log_request_shape_hygiene_emits_interpreter_and_policy_diag_for_mismatch() -> None:
    events = []
    rp._log_request_shape_hygiene(
        log_stage_fn=lambda stage, decision, status, result: events.append((stage, decision, status, result)),
        request_shape_hygiene={
            'target_host': 'www.bitstamp.net',
            'target_host_match_status': 'mixed',
            'request_shape_hygiene_status': 'cross_host_mismatch',
            'request_shape_hygiene_reason': 'mismatched_hosts_detected:insight2.tradepmr.com',
            'request_shape_hygiene_source': 'normalized_args+execution_plan',
            'all_hosts_detected': ['insight2.tradepmr.com'],
            'mismatched_hosts_detected': ['insight2.tradepmr.com'],
        },
        target_in_scope=True,
    )
    assert events[0][0:3] == ('INTERPRETER', 'request_shape_hygiene', 'warning')
    assert 'status=cross_host_mismatch' in events[0][3]
    assert events[1][0:3] == ('POLICY', 'request_shape_hygiene_diag', 'warning')
    assert 'in_scope_target_with_cross_host_mismatch' in events[1][3]


def test_execute_flow_blocks_on_required_replan_semantic_loss(monkeypatch) -> None:
    def fake_ask_json(agent, **kwargs):
        if agent == 'brain':
            return {
                'action_type': 'single_probe',
                'capability': 'http_probe',
                'tool': 'curl',
                'args': ['-I', 'https://api.example.com/'],
                'constraints': {'aggression': 2},
            }
        raise AssertionError('auditor should not be called when semantic loss requires replan')

    def fake_prepare(raw_action_spec, *, target, creds, execution_mode):
        final_spec = dict(raw_action_spec)
        final_spec['tool'] = 'curl'
        final_spec['args'] = ['-I', target]
        final_spec['tool_chain'] = [{'tool': 'curl', 'role': 'probe', 'args': ['-I', target]}]
        compiled = {
            'action_type': 'single_probe',
            'capability': 'http_probe',
            'compiler_strategy': 'passthrough',
            'compiler_tool_choice': 'curl',
            'compiler_tool_choice_source': 'explicit_tool',
            'compiler_variant_count': 1,
            'recipe_name': '',
            'semantic_loss_detected': True,
            'normalization_reason': 'unknown_action_type_lowered_to_passthrough',
            'semantic_loss_policy': {
                'loss_class': 'unacceptable_flattening',
                'severity': 'high',
                'policy_response': 'required_replan',
                'approved_under_degradation': False,
                'operator_visibility': 'prominent',
                'reason_code': 'semantic_loss_unknown_action_flattened',
                'normalization_reason': 'unknown_action_type_lowered_to_passthrough',
            },
            'execution_mode': execution_mode,
            'tool_candidates': ['curl'],
        }
        return final_spec, compiled

    monkeypatch.setattr(rp, 'ask_json', fake_ask_json)
    monkeypatch.setattr(rp, 'prepare_action_spec_for_execution', fake_prepare)
    monkeypatch.setattr(rp, 'evaluate_action_spec', lambda *args, **kwargs: {'pass': True, 'reason': 'ok'})
    monkeypatch.setattr(rp, 'load_credentials_runtime_policy', lambda: {})
    monkeypatch.setattr(rp, 'load_planner_hints', lambda **kwargs: {'preferred_vectors_for_target': [], 'deprioritized_task_families': [], 'ambiguities': [], 'interpretation_conflicts': [], 'task_family_context': {}, 'target_profile': {}})

    args = argparse.Namespace(
        objective='Probe target',
        target='https://api.example.com/',
        aggression=2,
        task_family='authz',
        task_success_criteria='',
        campaign_success_criteria='',
        acceptance_checks='',
        evidence_required='',
        success_semantics_json='',
        experiment_intent_id='',
        capability_candidates_json='',
        recommended_action_types_json='',
        hypothesis_candidates_json='',
        planner_constraints_json='',
        planner_preferences_json='',
        open_questions_json='',
        owner_override=False,
        owner_approved_auth=False,
        dry_run=False,
        cost_band='',
    )
    cfg = {
        'execution_mode': 'normalized',
        'json_contract_retries': 0,
        'experimental_payloads': False,
        'strict_deterministic': True,
        'prompt_token_budget': 0,
        'verbose_commands': False,
    }
    output, status, reason = rp.execute_flow(args, cfg, recent_context=[], context_limit=0)
    assert status == 'blocked'
    assert 'semantic_loss_policy:required_replan:unacceptable_flattening' in reason
    assert output['reason_code'] == 'semantic_loss_unknown_action_flattened'
    assert output['semantic_loss_policy']['loss_class'] == 'unacceptable_flattening'
    assert output['auditor']['decision'] == 'reject'
    assert output['request_shape_hygiene']['classification_timing'] == 'pre_auditor'
    assert output['request_shape_hygiene']['request_shape_hygiene_status'] == 'clean'
