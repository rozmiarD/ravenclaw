from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from planer.parser import parse_program_text  # type: ignore
from planer.interpretation import build_interpretations  # type: ignore
from planer.blueprint import build_blueprint  # type: ignore
from planer.llm_interpreter import reconcile_with_deterministic  # type: ignore


SCOPE_TEXT = """
Program Rules

In Scope:
*.x.com Wildcard High
chat.x.com Domain Critical
money.x.com Domain Critical
x.com Domain Critical
twimg.com Domain Medium
*.twimg.com Wildcard Medium
gnip.com Domain Medium

Out of scope:
ads.x.com

Allowed findings: xss, ssrf, csrf, idor, recon
Disallowed: brute force, dos, phishing, spam
"""


def test_parse_program_text_preserves_wildcards_and_out_of_scope() -> None:
    parsed = parse_program_text(SCOPE_TEXT, {})
    assert '*.x.com' in parsed['domains']
    assert '*.twimg.com' in parsed['domains']
    assert 'chat.x.com' in parsed['domains']
    assert 'money.x.com' in parsed['domains']
    assert 'ads.x.com' in parsed['out_of_scope_targets']
    assert 'ads.x.com' not in parsed['domains']


def test_build_blueprint_from_scope_with_wildcards_is_not_target_taxonomy_flat() -> None:
    parsed = parse_program_text(SCOPE_TEXT, {})
    interpretations = build_interpretations(parsed, SCOPE_TEXT)
    blueprint = build_blueprint(parsed, {'flags': {'llm_interpret': False}}, interpretations)
    counts = (blueprint.get('target_taxonomy') or {}).get('counts') or {}
    assert counts.get('total', 0) >= 5
    assert counts.get('web', 0) >= 1
    assert (counts.get('static', 0) + counts.get('integration', 0) + counts.get('auth', 0)) >= 1
    assert '*.x.com' in ((blueprint.get('structured_scope') or {}).get('domains') or [])


def test_parser_enriches_money_and_chat_surfaces_with_stateful_family_bias() -> None:
    parsed = parse_program_text(SCOPE_TEXT, {})
    money = parsed['target_profiles']['money.x.com']
    chat = parsed['target_profiles']['chat.x.com']
    wildcard_core = parsed['target_profiles']['*.x.com']
    static = parsed['target_profiles']['*.twimg.com']
    assert 'billing' in money['surface_keywords']
    assert 'wallet' in money['surface_keywords']
    assert money['priority_tier'] == 'high'
    assert money['expected_depth'] == 'deep'
    assert money['surface_role'] == 'primary'
    assert money['target_cluster'] == 'money'
    assert 'authz' in money['task_family_seeds']
    assert 'workflow' in money['task_family_seeds']
    assert 'state_transition' in money['task_family_seeds']
    assert 'chat' in chat['surface_keywords']
    assert 'session' in chat['surface_keywords']
    assert chat['priority_tier'] == 'high'
    assert chat['expected_depth'] == 'deep'
    assert chat['target_cluster'] == 'ai_chat'
    assert 'auth_flow' in chat['task_family_seeds']
    assert 'workflow' in chat['task_family_seeds']
    assert 'client_input' in chat['task_family_seeds']
    assert wildcard_core['priority_tier'] == 'medium'
    assert wildcard_core['surface_role'] == 'supporting'
    assert wildcard_core['expected_depth'] in {'light', 'medium'}
    assert len(wildcard_core['task_family_seeds']) <= 4
    assert static['surface_role'] in {'supporting', 'background'}
    assert static['expected_depth'] == 'light'


def test_blueprint_fallback_global_vectors_prioritize_stateful_research_over_broad_recon() -> None:
    parsed = parse_program_text(SCOPE_TEXT, {})
    interpretations = build_interpretations(parsed, SCOPE_TEXT)
    blueprint = build_blueprint(parsed, {'flags': {'llm_interpret': False}}, interpretations)
    vectors = ((blueprint.get('planner_hints') or {}).get('global_vectors') or [])
    clusters = ((blueprint.get('planner_hints') or {}).get('target_clusters') or {})
    intents = blueprint.get('experiment_intents') or []
    money_intent = next(intent for intent in intents if intent['target_host'] == 'money.x.com' and intent['task_family'] == 'authz')
    chat_discovery_intent = next(intent for intent in intents if intent['target_host'] == 'chat.x.com' and intent['task_family'] == 'content_discovery')
    static_intent = next(intent for intent in intents if intent['target_host'] == '*.twimg.com' and intent['task_family'] == 'content_discovery')
    wildcard_core_families = [intent['task_family'] for intent in intents if intent['target_host'] == '*.x.com']
    integration_families = [intent['task_family'] for intent in intents if intent['target_host'] == 'gnip.com']
    apex_families = [intent['task_family'] for intent in intents if intent['target_host'] == 'x.com']
    chat_families = [intent['task_family'] for intent in intents if intent['target_host'] == 'chat.x.com']
    assert 'auth_flow' in vectors
    assert 'workflow' in vectors
    assert 'client_input' in vectors
    assert 'recon' not in vectors or vectors.index('auth_flow') < vectors.index('recon')
    assert clusters['money']['hosts'] == ['money.x.com']
    assert clusters['money']['primary_hosts'] == ['money.x.com']
    assert 'workflow' in clusters['money']['family_bias']
    assert money_intent['priority_tier'] == 'high'
    assert money_intent['activation_phase'] == 1
    assert money_intent['activation_mode'] == 'immediate'
    assert money_intent['target_cluster'] == 'money'
    assert chat_discovery_intent['activation_phase'] == 2
    assert chat_discovery_intent['activation_mode'] == 'if_signal'
    assert chat_discovery_intent['conditional_gate'] == 'surface_mapping_after_primary_signal'
    assert 'workflow' not in wildcard_core_families
    assert 'state_transition' not in wildcard_core_families
    assert len(wildcard_core_families) <= 4
    assert 'recon' not in integration_families
    assert 'tls_assessment' not in integration_families
    assert 'historical_url_mining' not in apex_families
    assert 'recon' not in apex_families
    assert 'recon' not in chat_families
    assert 'historical_url_mining' not in chat_families
    assert static_intent['surface_role'] in {'supporting', 'background'}
    assert static_intent['activation_mode'] in {'if_signal', 'background'}


def test_parse_program_text_ignores_incidental_reporting_domains_and_email_domains() -> None:
    scope = """
Program Rules

In Scope:
https://www.oppo.com/th/store
cloud.oppo.com

Out of scope:
ads.oppo.com

Response Targets:
https://security.oppo.com/report
Email: security@wearehackerone.com
"""
    parsed = parse_program_text(scope, {})
    assert 'www.oppo.com' in parsed['domains']
    assert 'cloud.oppo.com' in parsed['domains']
    assert 'security.oppo.com' not in parsed['domains']
    assert 'wearehackerone.com' not in parsed['domains']
    assets = parsed['authoritative_assets']
    assert any(item['asset_kind'] == 'url' and item['target'] == 'https://www.oppo.com/th/store' for item in assets)


def test_blueprint_preserves_exact_url_assets_and_narrows_broad_host_families() -> None:
    scope = """
In Scope:
https://www.oppo.com/th/store
https://www.oppo.com/id/store
api.oppo.com

Allowed findings: xss, csrf, ssrf
Disallowed: phishing
"""
    parsed = parse_program_text(scope, {})
    blueprint = build_blueprint(parsed, {'flags': {'llm_interpret': False}}, build_interpretations(parsed, scope))
    assets = ((blueprint.get('structured_scope') or {}).get('authoritative_assets') or [])
    assert any(item.get('asset_kind') == 'url' and item.get('target') == 'https://www.oppo.com/th/store' for item in assets)
    intents = blueprint.get('experiment_intents') or []
    th_targets = [intent for intent in intents if intent.get('target') == 'https://www.oppo.com/th/store']
    assert th_targets
    th_families = [str(intent.get('task_family') or '') for intent in th_targets]
    assert 'recon' not in th_families
    assert 'tls_assessment' not in th_families
    assert 'historical_url_mining' not in th_families
    assert any(fam in th_families for fam in ['content_discovery', 'auth_flow', 'client_input'])


def test_blueprint_url_asset_shaping_uses_path_and_allowed_vectors_for_generic_hosts() -> None:
    scope = """
In Scope:
https://cloud.example.com/
https://www.example.com/store

Allowed findings: xss, csrf, ssrf
"""
    parsed = parse_program_text(scope, {})
    blueprint = build_blueprint(parsed, {'flags': {'llm_interpret': False}}, build_interpretations(parsed, scope))
    intents = blueprint.get('experiment_intents') or []

    cloud_families = sorted({str(intent.get('task_family') or '') for intent in intents if intent.get('target') == 'https://cloud.example.com/'})
    assert 'content_discovery' in cloud_families
    assert 'input_tamper' in cloud_families
    assert 'recon' not in cloud_families
    assert 'tls_assessment' not in cloud_families

    store_families = sorted({str(intent.get('task_family') or '') for intent in intents if intent.get('target') == 'https://www.example.com/store'})
    assert 'content_discovery' in store_families
    assert 'auth_flow' in store_families
    assert 'client_input' in store_families


def test_parser_classifies_identity_hosts_as_auth_surfaces() -> None:
    scope = """
In Scope:
id.heytap.com
id.oppo.com
"""
    parsed = parse_program_text(scope, {})
    id_heytap = parsed['target_profiles']['id.heytap.com']
    id_oppo = parsed['target_profiles']['id.oppo.com']
    assert id_heytap['target_type'] == 'auth'
    assert id_oppo['target_type'] == 'auth'
    assert id_heytap['target_cluster'] == 'identity_auth'
    assert id_oppo['target_cluster'] == 'identity_auth'
    assert 'auth_flow' in id_heytap['task_family_seeds']
    assert 'authz' in id_heytap['task_family_seeds']
    assert 'auth' in id_heytap['surface_keywords']


def test_blueprint_url_asset_shaping_avoids_auth_and_xss_broadcast_on_generic_root_urls() -> None:
    scope = """
In Scope:
https://zhongbao.heytap.com/

Allowed findings: xss, csrf, ssrf
"""
    parsed = parse_program_text(scope, {})
    blueprint = build_blueprint(parsed, {'flags': {'llm_interpret': False}}, build_interpretations(parsed, scope))
    intents = blueprint.get('experiment_intents') or []
    target_intents = [intent for intent in intents if intent.get('target') == 'https://zhongbao.heytap.com/']
    root_families = sorted({str(intent.get('task_family') or '') for intent in target_intents})
    assert root_families == ['content_discovery']
    prefs = (target_intents[0].get('planner_preferences') or {}) if target_intents else {}
    suppressed = prefs.get('suppressed_task_families') or []
    reasons = {entry.get('family'): entry.get('reason') for entry in suppressed if isinstance(entry, dict)}
    assert reasons.get('auth_flow') == 'suppressed_no_stateful_or_auth_signal'
    assert reasons.get('client_input') == 'suppressed_no_client_render_or_specific_path_signal'


def test_reconcile_with_deterministic_normalizes_llm_attack_vectors_to_canonical_tags() -> None:
    parsed = parse_program_text('In Scope:\nwww.example.com\nAllowed findings: xss, csrf, ssrf, idor', {})
    llm_data = {
        'suggested_attack_vectors': [
            'impact-proven authz/idor-style unauthorized operations',
            'stored/reflected xss with demonstrated user impact',
            'csrf with sensitive-action exploit proof',
            'ssrf and server-side trust-boundary flaws',
            'high-impact logic flaws in account/order/password flows',
            'validated low-noise recon/fuzz on listed in-scope assets',
        ]
    }
    _merged, meta = reconcile_with_deterministic(parsed, llm_data)
    vectors = ((meta.get('hints') or {}).get('global_vectors') or [])
    assert 'authz' in vectors
    assert 'client_input' in vectors
    assert 'auth_flow' in vectors
    assert 'input_tamper' in vectors
    assert 'workflow' in vectors
    assert 'content_discovery' in vectors


def test_blueprint_identity_cluster_keeps_symmetric_auth_family_bias_for_related_hosts() -> None:
    scope = """
In Scope:
id.heytap.com
id.oppo.com

Allowed findings: xss, csrf, idor
"""
    parsed = parse_program_text(scope, {})
    blueprint = build_blueprint(parsed, {'flags': {'llm_interpret': False}}, build_interpretations(parsed, scope))
    clusters = ((blueprint.get('planner_hints') or {}).get('target_clusters') or {})
    identity = clusters.get('identity_auth') or {}
    assert sorted(identity.get('hosts') or []) == ['id.heytap.com', 'id.oppo.com']
    assert sorted(identity.get('primary_hosts') or []) == ['id.heytap.com', 'id.oppo.com']
    assert 'authz' in (identity.get('family_bias') or [])
    assert 'auth_flow' in (identity.get('family_bias') or [])

    per_target = ((blueprint.get('planner_hints') or {}).get('per_target_vectors') or {})
    assert 'authz' in (per_target.get('id.heytap.com') or [])
    assert 'authz' in (per_target.get('id.oppo.com') or [])


def test_identity_domain_assets_trim_residual_recon_and_tls_families() -> None:
    scope = """
In Scope:
id.heytap.com

Allowed findings: xss, csrf, idor
"""
    parsed = parse_program_text(scope, {})
    blueprint = build_blueprint(parsed, {'flags': {'llm_interpret': False}}, build_interpretations(parsed, scope))
    intents = [intent for intent in (blueprint.get('experiment_intents') or []) if intent.get('target') == 'id.heytap.com']
    families = sorted({str(intent.get('task_family') or '') for intent in intents})
    assert 'authz' in families
    assert 'auth_flow' in families
    assert 'recon' not in families
    assert 'tls_assessment' not in families


def test_suppression_entries_include_score_threshold_and_are_unique() -> None:
    scope = """
In Scope:
https://zhongbao.heytap.com/

Allowed findings: xss, csrf, ssrf
"""
    parsed = parse_program_text(scope, {})
    blueprint = build_blueprint(parsed, {'flags': {'llm_interpret': False}}, build_interpretations(parsed, scope))
    intents = [intent for intent in (blueprint.get('experiment_intents') or []) if intent.get('target') == 'https://zhongbao.heytap.com/']
    prefs = (intents[0].get('planner_preferences') or {}) if intents else {}
    suppressed = prefs.get('suppressed_task_families') or []
    pairs = [(entry.get('family'), entry.get('reason')) for entry in suppressed if isinstance(entry, dict)]
    assert len(pairs) == len(set(pairs))
    for entry in suppressed:
        assert 'score' in entry
        assert 'threshold' in entry
        assert float(entry['threshold']) == 0.58
