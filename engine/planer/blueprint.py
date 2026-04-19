from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List

from .schema import validate_blueprint
from .identity import build_planner_identity

try:
    from capability_recipes import suggest_capabilities_for_task_family  # type: ignore
except Exception:  # pragma: no cover - fallback only
    def suggest_capabilities_for_task_family(task_family: str) -> List[str]:
        return []

try:
    from runtime_task_schema import normalize_runtime_task_v2  # type: ignore
    from .planner_intent_contract import compose_experiment_intent_contract
except Exception:  # pragma: no cover - fallback only
    def normalize_runtime_task_v2(task: dict[str, Any] | None, runtime_task: dict[str, Any] | None = None) -> dict[str, Any]:
        base = dict(runtime_task or {})
        if isinstance(task, dict):
            base.update(task)
        return base

    def compose_experiment_intent_contract(*, base_intent: dict[str, Any], runtime_task_contract: dict[str, Any] | None, success_model: str = '') -> dict[str, Any]:
        out = dict(base_intent or {})
        out['runtime_task_contract'] = normalize_runtime_task_v2(out, runtime_task_contract)
        return out


NAMESPACE_UUID = uuid.UUID("12345678-1234-5678-1234-567812345678")


@dataclass(frozen=True)
class Variant:
    name: str
    summary: str
    suggested_aggression: int
    first_vectors: List[str]
    budget_usd: int
    success_criteria: str


def _stable_hash(payload: Dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _build_variants(domain_count: int) -> List[Variant]:
    return [
        Variant(
            name="cost_effective",
            summary="Prioritize low-cost, high-signal recon and validation checks.",
            suggested_aggression=3,
            first_vectors=["robots/sitemap", "passive endpoint mapping", "safe input probes"],
            budget_usd=max(5, domain_count * 2),
            success_criteria="At least one validated medium-signal finding or hardening recommendation per target group.",
        ),
        Variant(
            name="easy_to_hard",
            summary="Progress from easy checks to deeper vectors in deterministic order.",
            suggested_aggression=5,
            first_vectors=["recon", "authz checks", "safe XSS/redirect probes"],
            budget_usd=max(10, domain_count * 4),
            success_criteria="Complete all low-risk vectors before medium/high-effort vectors.",
        ),
        Variant(
            name="high_reward_high_effort",
            summary="Focus on complex high-value vectors and deep chaining.",
            suggested_aggression=7,
            first_vectors=["complex auth flows", "state-change abuse", "multi-step exploitability checks"],
            budget_usd=max(20, domain_count * 7),
            success_criteria="Demonstrate at least one high-impact exploit path or produce high-confidence negative proof.",
        ),
    ]


def _sanitize_name_part(value: str, default: str) -> str:
    raw = (value or "").strip().upper()
    safe = "".join(ch if ch.isalnum() else "_" for ch in raw).strip("_")
    return safe or default



def _intent_execution_hints(*, profile: dict[str, Any], fam: str) -> dict[str, Any]:
    priority_tier = str(profile.get('priority_tier') or 'medium').strip().lower() or 'medium'
    expected_depth = str(profile.get('expected_depth') or 'medium').strip().lower() or 'medium'
    surface_role = str(profile.get('surface_role') or 'primary').strip().lower() or 'primary'
    fam = str(fam or '').strip().lower()
    activation_phase = 1
    activation_mode = 'immediate'
    conditional_gate = 'none'
    if fam in {'recon', 'historical_url_mining', 'content_discovery', 'tls_assessment', 'subdomain_expansion'}:
        activation_phase = 1
        activation_mode = 'immediate' if surface_role == 'primary' else 'background'
        conditional_gate = 'supporting_surface_only' if surface_role != 'primary' else 'none'
        if priority_tier == 'high' and expected_depth == 'deep' and fam in {'historical_url_mining', 'content_discovery', 'tls_assessment'}:
            activation_phase = 2
            activation_mode = 'if_signal'
            conditional_gate = 'surface_mapping_after_primary_signal'
    elif fam in {'auth_flow', 'authz'}:
        activation_phase = 1 if priority_tier == 'high' else 2
        activation_mode = 'immediate' if priority_tier == 'high' else 'if_signal'
        conditional_gate = 'authenticated_or_boundary_mapping'
    elif fam in {'workflow', 'logic', 'state_transition'}:
        activation_phase = 2
        activation_mode = 'if_signal'
        conditional_gate = 'stateful_or_boundary_signal'
    elif fam in {'redirect_trust', 'client_input', 'input_tamper'}:
        activation_phase = 2 if priority_tier == 'high' else 3
        activation_mode = 'if_signal' if fam != 'redirect_trust' else 'if_confirmed'
        conditional_gate = 'chainable_impact_or_confirmed_signal' if fam == 'redirect_trust' else 'high_value_surface_signal'
    if surface_role == 'background':
        activation_phase = max(activation_phase, 3)
        activation_mode = 'background'
        conditional_gate = conditional_gate or 'background_surface_only'
    elif surface_role == 'supporting':
        activation_phase = max(activation_phase, 2)
        if activation_mode == 'immediate':
            activation_mode = 'if_signal'
        conditional_gate = conditional_gate or 'supporting_surface_only'
    return {
        'priority_tier': priority_tier,
        'expected_depth': expected_depth,
        'surface_role': surface_role,
        'target_cluster': str(profile.get('target_cluster') or 'general').strip().lower() or 'general',
        'activation_phase': activation_phase,
        'activation_mode': activation_mode,
        'conditional_gate': conditional_gate,
    }



def _cluster_primary_limit(cluster_name: str) -> int:
    return {
        'money': 1,
        'identity_auth': 2,
        'commerce_store': 2,
        'integration_api': 1,
        'infra_edge': 1,
        'consumer_web': 2,
        'core_social': 1,
        'ai_chat': 2,
        'static_media': 0,
        'general': 1,
    }.get(str(cluster_name or 'general').strip().lower() or 'general', 1)



def _host_cluster_rank(host: str, profile: dict[str, Any]) -> tuple[int, int, int, int, str]:
    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    depth_order = {'deep': 0, 'medium': 1, 'light': 2}
    role_order = {'primary': 0, 'supporting': 1, 'background': 2}
    wildcard_penalty = 1 if str(host or '').startswith('*.') else 0
    return (
        wildcard_penalty,
        priority_order.get(str(profile.get('priority_tier') or 'medium').strip().lower(), 1),
        depth_order.get(str(profile.get('expected_depth') or 'medium').strip().lower(), 1),
        role_order.get(str(profile.get('surface_role') or 'primary').strip().lower(), 1),
        str(host or ''),
    )



def _prune_cluster_secondary_families(*, host: str, profile: dict[str, Any], primary_hosts: list[str]) -> list[str]:
    fams = [str(x or '').strip().lower() for x in (profile.get('task_family_seeds') or []) if str(x or '').strip()]
    cluster_name = str(profile.get('target_cluster') or 'general').strip().lower() or 'general'
    if host in primary_hosts or not primary_hosts:
        return fams
    support_sets = {
        'core_social': ['auth_flow', 'redirect_trust', 'content_discovery', 'historical_url_mining'],
        'ai_chat': ['auth_flow', 'content_discovery', 'historical_url_mining', 'redirect_trust'],
        'integration_api': ['authz', 'auth_flow', 'content_discovery'],
        'money': ['auth_flow', 'content_discovery', 'historical_url_mining'],
        'identity_auth': ['authz', 'auth_flow', 'client_input', 'content_discovery'],
        'commerce_store': ['auth_flow', 'client_input', 'content_discovery', 'workflow'],
        'infra_edge': ['auth_flow', 'input_tamper', 'content_discovery'],
        'consumer_web': ['content_discovery', 'client_input', 'auth_flow', 'historical_url_mining'],
        'static_media': ['content_discovery', 'historical_url_mining', 'recon', 'tls_assessment'],
        'general': ['auth_flow', 'content_discovery', 'historical_url_mining', 'redirect_trust'],
    }
    allowed = support_sets.get(cluster_name, support_sets['general'])
    pruned = [fam for fam in fams if fam in allowed]
    if not pruned:
        pruned = fams[:2]
    return pruned[:4]



def _build_target_clusters(target_profiles: dict[str, Any]) -> dict[str, Any]:
    clusters: dict[str, dict[str, Any]] = {}
    grouped: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    for host, profile in (target_profiles or {}).items():
        if not isinstance(profile, dict):
            continue
        cluster_name = str(profile.get('target_cluster') or 'general').strip().lower() or 'general'
        grouped.setdefault(cluster_name, []).append((host, profile))
    for cluster_name, items in grouped.items():
        ranked = sorted(items, key=lambda hp: _host_cluster_rank(hp[0], hp[1]))
        primary_limit = _cluster_primary_limit(cluster_name)
        primary_hosts = [host for host, _ in ranked[:primary_limit]] if primary_limit > 0 else []
        secondary_hosts = [host for host, _ in ranked if host not in primary_hosts]
        entry = {
            'hosts': sorted([host for host, _ in ranked]),
            'primary_hosts': sorted(primary_hosts),
            'secondary_hosts': sorted(secondary_hosts),
            'priority_tiers': [],
            'surface_roles': [],
            'family_bias': [],
        }
        for host, profile in ranked:
            pt = str(profile.get('priority_tier') or '').strip().lower()
            sr = str(profile.get('surface_role') or '').strip().lower()
            if pt and pt not in entry['priority_tiers']:
                entry['priority_tiers'].append(pt)
            if sr and sr not in entry['surface_roles']:
                entry['surface_roles'].append(sr)
            fam_source = profile.get('cluster_adjusted_task_family_seeds') if isinstance(profile.get('cluster_adjusted_task_family_seeds'), list) else profile.get('task_family_seeds')
            for fam in list(fam_source or [])[:4]:
                ff = str(fam or '').strip().lower()
                if ff and ff not in entry['family_bias']:
                    entry['family_bias'].append(ff)
        entry['family_bias'] = entry['family_bias'][:6]
        clusters[cluster_name] = entry
    return clusters



def _fallback_global_vectors(*, allow_keywords: list[str], target_profiles: dict[str, Any]) -> list[str]:
    allow = {str(x or '').strip().lower() for x in (allow_keywords or []) if str(x or '').strip()}
    vectors: list[str] = []
    seeded: set[str] = set()
    if 'idor' in allow:
        vectors.append('authz')
        seeded.add('authz')
    if 'csrf' in allow:
        vectors.append('auth_flow')
        seeded.add('auth_flow')
    if 'xss' in allow:
        vectors.append('client_input')
        seeded.add('client_input')
    if 'ssrf' in allow:
        vectors.append('input_tamper')
        seeded.add('input_tamper')
    if 'open redirect' in allow:
        vectors.append('redirect_trust')
        seeded.add('redirect_trust')
    priority = {
        'authz': 100,
        'auth_flow': 95,
        'workflow': 90,
        'logic': 88,
        'state_transition': 86,
        'redirect_trust': 84,
        'client_input': 82,
        'input_tamper': 80,
        'content_discovery': 50,
        'historical_url_mining': 45,
        'subdomain_expansion': 42,
        'recon': 20,
        'tls_assessment': 10,
    }
    scored: dict[str, int] = {v: priority.get(v, 30) + (1000 if v in seeded else 0) for v in vectors}
    for profile in (target_profiles or {}).values():
        if not isinstance(profile, dict):
            continue
        for idx, candidate in enumerate(profile.get('candidate_vectors') or []):
            c = str(candidate or '').strip().lower()
            if not c:
                continue
            score = priority.get(c, 30) - min(idx, 6)
            scored[c] = max(scored.get(c, -999), score)
    ordered = sorted(scored, key=lambda c: (-scored[c], c))
    if len(ordered) > 6 and 'recon' in ordered:
        ordered = [c for c in ordered if c != 'recon'] + ['recon']
    if len(ordered) > 6 and 'tls_assessment' in ordered:
        ordered = [c for c in ordered if c != 'tls_assessment'] + ['tls_assessment']
    return ordered[:8]


def _target_type(entry: Dict[str, Any]) -> str:
    if not isinstance(entry, dict):
        return ''
    return str(entry.get('target_type') or entry.get('type') or '').strip().lower()


def _family_objective(fam: str) -> str:
    family_objectives = {
        'recon': 'Passive recon and endpoint discovery',
        'subdomain_expansion': 'Subdomain expansion and passive asset enumeration',
        'historical_url_mining': 'Historical URL and legacy endpoint mining',
        'content_discovery': 'Content discovery and path surface mapping',
        'tls_assessment': 'TLS/certificate and HTTPS posture checks',
        'secret_hunt': 'Client-side secret exposure surface review',
        'authz': 'AuthN/AuthZ boundary probing (safe)',
        'auth_flow': 'Authentication flow hardening checks (state/nonce/session)',
        'logic': 'Business-logic flow consistency checks',
        'client_input': 'Reflected/stored XSS safe probe paths',
        'input_tamper': 'Input validation and parameter tampering checks',
        'redirect_trust': 'Open redirect and redirect-trust boundary checks',
    }
    return str(family_objectives.get(str(fam or '').strip().lower()) or 'Passive recon and endpoint discovery')


def _recommended_action_types_for_family(fam: str) -> List[str]:
    fam = str(fam or '').strip().lower()
    if fam in {'authz', 'auth_flow'}:
        return ['differential_probe', 'state_transition_probe', 'confirmatory_probe']
    if fam in {'logic', 'redirect_trust'}:
        return ['differential_probe', 'confirmatory_probe', 'variant_probe']
    if fam in {'client_input', 'input_tamper'}:
        return ['variant_probe', 'confirmatory_probe', 'single_probe']
    if fam in {'content_discovery', 'historical_url_mining', 'subdomain_expansion'}:
        return ['enumeration_probe', 'confirmatory_probe']
    if fam in {'tls_assessment'}:
        return ['fingerprint_probe', 'confirmatory_probe']
    if fam in {'secret_hunt'}:
        return ['enumeration_probe', 'confirmatory_probe']
    if fam in {'recon'}:
        return ['fingerprint_probe', 'enumeration_probe']
    return ['single_probe']



def _target_specific_action_types_for_family(fam: str, *, target_type: str, auth_available: bool, surface_keywords: List[str]) -> List[str]:
    fam = str(fam or '').strip().lower()
    target_type = str(target_type or 'host').strip().lower()
    base = list(_recommended_action_types_for_family(fam))
    if fam in {'authz', 'idor'} and target_type in {'api', 'auth', 'integration'}:
        return ['differential_probe', 'state_transition_probe', 'confirmatory_probe']
    if fam in {'auth_flow'} and target_type in {'auth', 'api'}:
        return ['state_transition_probe', 'differential_probe', 'confirmatory_probe']
    if fam in {'logic', 'workflow', 'state_transition'} and target_type in {'api', 'web', 'auth'}:
        return ['state_transition_probe', 'differential_probe', 'confirmatory_probe']
    if fam in {'content_discovery', 'recon'} and target_type in {'api', 'integration'}:
        return ['enumeration_probe', 'fingerprint_probe', 'confirmatory_probe']
    if fam in {'content_discovery', 'historical_url_mining', 'recon'} and target_type in {'static', 'support'}:
        return ['fingerprint_probe', 'enumeration_probe', 'confirmatory_probe']
    if fam in {'tls_assessment', 'secret_hunt'} and target_type in {'static', 'support'}:
        return ['fingerprint_probe', 'enumeration_probe', 'confirmatory_probe']
    if auth_available and any(k in surface_keywords for k in ['admin', 'billing', 'tenant', 'organization']):
        return list(dict.fromkeys(['differential_probe', 'state_transition_probe'] + base))[:4]
    return base


def _success_semantics_for_family(fam: str) -> Dict[str, Any]:
    fam = str(fam or '').strip().lower()
    if fam in {'authz', 'auth_flow', 'logic', 'redirect_trust'}:
        return {'success_model': 'differential_or_stateful_signal', 'expected_signal_type': 'behavior_delta', 'evidence_goal_type': 'controlled_comparison'}
    if fam in {'content_discovery', 'historical_url_mining', 'subdomain_expansion', 'recon'}:
        return {'success_model': 'surface_expansion', 'expected_signal_type': 'novel_asset_or_endpoint', 'evidence_goal_type': 'enumeration_gain'}
    if fam in {'tls_assessment', 'secret_hunt'}:
        return {'success_model': 'fingerprint_or_exposure_signal', 'expected_signal_type': 'configuration_or_exposure_clue', 'evidence_goal_type': 'evidence_capture'}
    return {'success_model': 'generic_signal', 'expected_signal_type': 'technical_signal', 'evidence_goal_type': 'evidence_capture'}


def _evidence_contract_for_family(fam: str) -> Dict[str, Any]:
    fam = str(fam or '').strip().lower()
    acceptance_checks: List[str] = []
    evidence_required: List[str] = []
    negative_control_requirements: List[str] = []
    if fam in {'authz', 'auth_flow'}:
        acceptance_checks = ['negative_control', 'allow_deny_delta']
        evidence_required = ['http_status', 'response_diff']
        negative_control_requirements = ['negative_control']
    elif fam in {'logic', 'workflow', 'state_transition'}:
        acceptance_checks = ['state_consistency', 'transition_guard']
        evidence_required = ['response_diff', 'state_transition_artifact']
        negative_control_requirements = ['negative_control']
    elif fam in {'client_input', 'input_tamper', 'redirect_trust'}:
        acceptance_checks = ['safe_probe_only', 'false_positive_guard']
        evidence_required = ['reflection_or_behavior_delta']
    elif fam in {'content_discovery', 'historical_url_mining', 'subdomain_expansion'}:
        acceptance_checks = ['novelty_confirmation']
        evidence_required = ['novel_endpoint_or_asset']
    elif fam == 'recon':
        acceptance_checks = ['signal_inventory']
        evidence_required = ['endpoint_or_header_inventory']
    return {
        'acceptance_checks': acceptance_checks,
        'evidence_required': evidence_required,
        'negative_control_requirements': negative_control_requirements,
        **_success_semantics_for_family(fam),
    }



def _task_success_criteria_for_family(fam: str, *, target_type: str, credentials_required: bool) -> str:
    fam = str(fam or '').strip().lower()
    if fam in {'authz', 'idor'}:
        return 'Demonstrate a stable actor or object-boundary delta with a valid negative control.'
    if fam in {'auth_flow'}:
        return 'Demonstrate a stable authentication-state handling flaw without leaving scope-safe control paths.'
    if fam in {'logic', 'workflow', 'state_transition'}:
        return 'Demonstrate a reproducible forbidden transition or invariant break with bounded state evidence.'
    if fam in {'client_input', 'input_tamper', 'redirect_trust'}:
        return 'Capture a bounded trust or input-handling differential that survives false-positive guards.'
    if fam in {'content_discovery', 'historical_url_mining', 'subdomain_expansion', 'recon'}:
        return 'Capture a novel and actionable surface expansion that can justify a higher-leverage pivot.'
    if fam in {'tls_assessment', 'secret_hunt'}:
        return 'Capture a reportable exposure or posture artifact with enough context for operator review.'
    suffix = ' with authenticated context' if credentials_required and target_type in {'app', 'api'} else ''
    return f'Capture a reproducible technical signal{suffix}.'



def _target_specific_exploit_ladder_for_family(*, fam: str, target_type: str, auth_available: bool, surface_keywords: List[str], focus_keywords: List[str], ambiguities: List[str], open_questions: List[str]) -> Dict[str, Any]:
    fam = str(fam or '').strip().lower()
    target_type = str(target_type or 'host').strip().lower()
    ladder: Dict[str, Any]
    if fam in {'authz', 'idor'}:
        ladder = {
            'stage': 'control_boundary_confirmation',
            'progression': ['discovery', 'validation', 'control_boundary_confirmation', 'bounded_exploit_proof', 'report_artifact_capture'],
            'proof_strategy': 'actor_or_object_boundary_delta' if target_type != 'auth' else 'authentication_boundary_delta',
        }
    elif fam in {'auth_flow'}:
        ladder = {
            'stage': 'state_transition_confirmation',
            'progression': ['discovery', 'validation', 'state_transition_confirmation', 'bounded_exploit_proof', 'report_artifact_capture'],
            'proof_strategy': 'authentication_state_transition_validation',
        }
    elif fam in {'logic', 'workflow', 'state_transition'}:
        ladder = {
            'stage': 'state_transition_confirmation',
            'progression': ['discovery', 'validation', 'state_transition_confirmation', 'bounded_exploit_proof', 'report_artifact_capture'],
            'proof_strategy': 'forbidden_transition_or_invariant_break',
        }
    elif fam in {'client_input', 'input_tamper', 'redirect_trust'}:
        ladder = {
            'stage': 'validation',
            'progression': ['discovery', 'validation', 'bounded_exploit_proof', 'report_artifact_capture'],
            'proof_strategy': 'safe_input_or_trust_boundary_validation',
        }
    elif fam in {'content_discovery', 'historical_url_mining', 'subdomain_expansion', 'recon'}:
        progression = ['discovery', 'validation', 'report_artifact_capture'] if target_type in {'api', 'auth', 'integration', 'web'} else ['discovery', 'report_artifact_capture']
        ladder = {
            'stage': 'discovery',
            'progression': progression,
            'proof_strategy': 'surface_expansion_and_pivot_selection' if target_type not in {'static', 'support'} else 'surface_capture_and_contextualization',
        }
    elif fam in {'tls_assessment', 'secret_hunt'}:
        ladder = {
            'stage': 'discovery',
            'progression': ['discovery', 'report_artifact_capture'] if target_type in {'static', 'support'} else ['discovery', 'validation', 'report_artifact_capture'],
            'proof_strategy': 'reportable_artifact_capture',
        }
    else:
        ladder = {
            'stage': 'validation',
            'progression': ['discovery', 'validation', 'bounded_exploit_proof', 'report_artifact_capture'],
            'proof_strategy': 'bounded_validation',
        }
    if auth_available and target_type in {'api', 'auth', 'integration'} and fam in {'authz', 'logic', 'workflow', 'state_transition'}:
        ladder['proof_strategy'] = 'authenticated_boundary_or_state_delta'
    if any(k in surface_keywords for k in ['billing', 'tenant', 'admin', 'organization']):
        ladder['proof_strategy'] = 'high_leverage_boundary_delta'
    if focus_keywords and target_type in {'api', 'integration'} and 'validation' not in list(ladder.get('progression') or []):
        ladder['progression'] = ['discovery', 'validation'] + [x for x in list(ladder.get('progression') or []) if x not in {'discovery', 'validation'}]
    if ambiguities or open_questions:
        ladder['progression'] = [x for x in list(ladder.get('progression') or []) if x != 'report_artifact_capture'] + ['report_artifact_capture']
    return ladder



def _runtime_task_contract_for_intent(*, host: str, target: str, fam: str, target_type: str, capability_candidates: List[str], recommended_action_types: List[str], hypothesis_candidates: List[str], evidence_contract: Dict[str, Any], planner_constraints: Dict[str, Any], planner_preferences: Dict[str, Any], intent_id: str, ambiguities: List[str], open_questions: List[str], execution_hints: Dict[str, Any]) -> Dict[str, Any]:
    fam = str(fam or '').strip().lower()
    target_type = str(target_type or 'host').strip().lower()
    surface_keywords = [str(x).strip().lower() for x in (planner_preferences.get('surface_keywords') or []) if str(x).strip()]
    focus_keywords = [str(x).strip().lower() for x in (planner_preferences.get('focus_allow_keywords') or []) if str(x).strip()]
    credentials_required = bool(planner_constraints.get('credentials_required', False))
    auth_available = bool(planner_constraints.get('allow_auth_header') or planner_constraints.get('allow_cookie_header') or planner_constraints.get('allow_basic_auth') or credentials_required)

    actor_requirements: Dict[str, Any] = {}
    session_requirements: Dict[str, Any] = {}
    promotion_policy: Dict[str, Any] = {}
    exploit_ladder: Dict[str, Any] = {}
    approval_sensitivity: Dict[str, Any] = {}

    recommended_action_types = _target_specific_action_types_for_family(
        fam,
        target_type=target_type,
        auth_available=auth_available,
        surface_keywords=surface_keywords,
    )

    if fam in {'authz', 'idor'}:
        actor_requirements = {
            'required': True,
            'differential': True,
            'preferred_roles': ['anonymous', 'baseline_user'] if not auth_available else ['baseline_user', 'elevated_user'],
        }
        session_requirements = {
            'stateful': False,
            'auth_context': auth_available,
            'prerequisites': ['establish comparison identities'] if auth_available else ['capture anonymous vs authenticated boundary'],
        }
        promotion_policy = {'followup_allowed': True, 'confirm_preferred': True, 'bounded_only': True}
        approval_sensitivity = {'auth_sensitive': auth_available, 'owner_approval_required': bool(planner_constraints.get('owner_approval_required', True))}
    elif fam in {'auth_flow'}:
        actor_requirements = {'required': True, 'differential': False, 'preferred_roles': ['baseline_user'] if auth_available else ['anonymous']}
        session_requirements = {'stateful': True, 'auth_context': auth_available, 'prerequisites': ['capture anti-csrf/state tokens', 'establish authenticated session'] if auth_available else ['capture anti-csrf/state tokens']}
        promotion_policy = {'followup_allowed': True, 'confirm_preferred': True, 'bounded_only': True}
        approval_sensitivity = {'auth_sensitive': True, 'owner_approval_required': bool(planner_constraints.get('owner_approval_required', True))}
    elif fam in {'logic', 'workflow', 'state_transition'}:
        actor_requirements = {'required': auth_available, 'differential': fam == 'logic', 'preferred_roles': ['baseline_user'] if auth_available else []}
        session_requirements = {'stateful': True, 'auth_context': auth_available, 'prerequisites': ['capture workflow state markers', 'establish authenticated session'] if auth_available else ['capture workflow state markers']}
        promotion_policy = {'followup_allowed': True, 'confirm_preferred': True, 'bounded_only': True}
        approval_sensitivity = {'auth_sensitive': auth_available, 'owner_approval_required': bool(planner_constraints.get('owner_approval_required', True))}
    elif fam in {'client_input', 'input_tamper', 'redirect_trust'}:
        actor_requirements = {'required': False, 'differential': False, 'preferred_roles': []}
        session_requirements = {'stateful': False, 'auth_context': auth_available and target_type in {'app', 'api', 'auth', 'integration'}, 'prerequisites': []}
        promotion_policy = {'followup_allowed': True, 'confirm_preferred': False, 'bounded_only': True}
        approval_sensitivity = {'auth_sensitive': bool(auth_available and 'account' in surface_keywords), 'owner_approval_required': bool(planner_constraints.get('owner_approval_required', True))}
    elif fam in {'content_discovery', 'historical_url_mining', 'subdomain_expansion', 'recon'}:
        actor_requirements = {'required': False, 'differential': False, 'preferred_roles': []}
        session_requirements = {'stateful': False, 'auth_context': False, 'prerequisites': []}
        promotion_policy = {'followup_allowed': bool(target_type in {'app', 'api', 'auth', 'integration'} or any(k in focus_keywords for k in ['admin', 'api', 'auth', 'account'])), 'confirm_preferred': False, 'bounded_only': True}
        approval_sensitivity = {'auth_sensitive': False, 'owner_approval_required': False}
    else:
        actor_requirements = {'required': False, 'differential': False, 'preferred_roles': []}
        session_requirements = {'stateful': False, 'auth_context': auth_available and target_type in {'app', 'api', 'auth', 'integration'}, 'prerequisites': []}
        promotion_policy = {'followup_allowed': True, 'confirm_preferred': False, 'bounded_only': True}
        approval_sensitivity = {'auth_sensitive': bool(auth_available), 'owner_approval_required': bool(planner_constraints.get('owner_approval_required', True))}

    if ambiguities or open_questions:
        promotion_policy['bounded_only'] = True

    exploit_ladder = _target_specific_exploit_ladder_for_family(
        fam=fam,
        target_type=target_type,
        auth_available=auth_available,
        surface_keywords=surface_keywords,
        focus_keywords=focus_keywords,
        ambiguities=ambiguities,
        open_questions=open_questions,
    )

    priority_tier = str(execution_hints.get('priority_tier') or 'medium').strip().lower() or 'medium'
    priority_score = 1.25 if priority_tier == 'high' else 0.8 if priority_tier == 'low' else 1.0
    runtime_task_contract = normalize_runtime_task_v2({
        'objective': _family_objective(fam),
        'target': str(target or f'https://{host}/'),
        'task_family': fam,
        'task_success_criteria': _task_success_criteria_for_family(fam, target_type=target_type, credentials_required=credentials_required),
        'campaign_success_criteria': 'Complete all low-risk vectors before medium/high-effort vectors.',
        'acceptance_checks': list(evidence_contract.get('acceptance_checks') or []),
        'evidence_required': list(evidence_contract.get('evidence_required') or []),
        'success_semantics': {
            'success_model': str(evidence_contract.get('success_model') or ''),
            'expected_signal_type': str(evidence_contract.get('expected_signal_type') or ''),
            'evidence_goal_type': str(evidence_contract.get('evidence_goal_type') or ''),
        },
        'capability_candidates': capability_candidates[:6],
        'recommended_action_types': recommended_action_types[:6],
        'hypothesis_candidates': hypothesis_candidates,
        'experiment_intent_id': intent_id,
        'planner_constraints': planner_constraints,
        'planner_preferences': planner_preferences,
        'planner_input_source': 'planner_experiment_intent',
        'priority_score': priority_score,
        'cost_band': 'medium' if fam in {'authz', 'auth_flow', 'logic', 'client_input', 'input_tamper', 'redirect_trust', 'workflow', 'state_transition'} else 'low',
        'priority_tier': execution_hints.get('priority_tier'),
        'expected_depth': execution_hints.get('expected_depth'),
        'activation_phase': execution_hints.get('activation_phase'),
        'activation_mode': execution_hints.get('activation_mode'),
        'conditional_gate': execution_hints.get('conditional_gate'),
        'surface_role': execution_hints.get('surface_role'),
        'target_cluster': execution_hints.get('target_cluster'),
        'actor_requirements': actor_requirements,
        'session_requirements': session_requirements,
        'promotion_policy': promotion_policy,
        'exploit_ladder': exploit_ladder,
        'approval_sensitivity': approval_sensitivity,
        'open_questions': open_questions[:4],
    })
    return runtime_task_contract


def _build_planner_directives(
    *,
    task_family_seeds: Dict[str, List[str]],
    target_profiles: Dict[str, Any],
    global_vectors: List[str],
    candidate_targets: List[str],
    llm_meta: Dict[str, Any],
    aggression_profile: Dict[str, Any],
    credentials_policy: Dict[str, Any],
    allow_keywords: List[str],
) -> Dict[str, Any]:
    per_target_vectors = {host: fams[:3] for host, fams in task_family_seeds.items()}
    recommended_families = sorted({fam for fams in task_family_seeds.values() for fam in fams})
    deprioritized = ['secret_hunt'] if credentials_policy.get('credentials_required') else []
    target_clusters = _build_target_clusters(target_profiles)
    per_target_execution_hints = {
        host: {
            'priority_tier': str((profile or {}).get('priority_tier') or 'medium').strip().lower(),
            'expected_depth': str((profile or {}).get('expected_depth') or 'medium').strip().lower(),
            'surface_role': str((profile or {}).get('surface_role') or 'primary').strip().lower(),
            'target_cluster': str((profile or {}).get('target_cluster') or 'general').strip().lower(),
        }
        for host, profile in target_profiles.items()
        if isinstance(profile, dict)
    }
    return {
        'constraints': {
            'campaign_bound_context': True,
            'in_scope_only': True,
            'credentials_required': bool(credentials_policy.get('credentials_required', False)),
            'allow_auth_header': bool(credentials_policy.get('allow_auth_header', False)),
            'allow_cookie_header': bool(credentials_policy.get('allow_cookie_header', False)),
            'allow_basic_auth': bool(credentials_policy.get('allow_basic_auth', False)),
            'owner_approval_required': bool(credentials_policy.get('owner_approval_required', True)),
            'recommended_aggression_min': aggression_profile.get('recommended_min'),
            'recommended_aggression_max': aggression_profile.get('recommended_max'),
        },
        'preferences': {
            'global_vectors': list(global_vectors or [])[:8],
            'per_target_vectors': per_target_vectors,
            'recommended_task_families': recommended_families,
            'deprioritized_task_families': deprioritized,
            'focus_allow_keywords': [str(x).strip().lower() for x in (allow_keywords or []) if str(x).strip()][:8],
            'target_surface_keywords': {
                host: [str(x).strip().lower() for x in ((profile or {}).get('surface_keywords') or []) if str(x).strip()][:6]
                for host, profile in target_profiles.items()
                if isinstance(profile, dict)
            },
            'per_target_execution_hints': per_target_execution_hints,
        },
        'unknowns': {
            'candidate_targets': list(candidate_targets or [])[:8],
            'ambiguities': list(llm_meta.get('ambiguities', []) or [])[:8],
            'interpretation_conflicts': list(llm_meta.get('conflicts', []) or [])[:8],
        },
    }


def _normalized_authoritative_assets(*, authoritative_assets: List[Dict[str, Any]] | None, domains: List[str]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for raw in list(authoritative_assets or []):
        if not isinstance(raw, dict):
            continue
        asset_kind = str(raw.get('asset_kind') or 'domain').strip().lower() or 'domain'
        host = str(raw.get('host') or '').strip().lower()
        target = str(raw.get('target') or '').strip()
        if not host:
            continue
        if asset_kind == 'url' and not target:
            continue
        if asset_kind != 'url':
            asset_kind = 'domain'
            target = target or host
        key = (asset_kind, target.lower() if asset_kind == 'url' else host)
        if key in seen:
            continue
        seen.add(key)
        items.append({
            'asset_kind': asset_kind,
            'host': host,
            'target': target or host,
            'path_prefix': str(raw.get('path_prefix') or '/'),
            'scope_source': str(raw.get('scope_source') or 'authoritative'),
            'source_line': str(raw.get('source_line') or ''),
        })
    if items:
        return items
    for host in sorted({str(d).strip().lower() for d in (domains or []) if str(d).strip()}):
        items.append({'asset_kind': 'domain', 'host': host, 'target': host, 'path_prefix': '/', 'scope_source': 'authoritative', 'source_line': ''})
    return items


def _family_decision_for_scope_asset(*, asset: Dict[str, Any], families: List[str], target_type: str, target_cluster: str, surface_keywords: List[str], focus_allow_keywords: List[str], global_vectors: List[str]) -> Dict[str, Any]:
    fams = [str(x).strip().lower() for x in (families or []) if str(x).strip()] or ['recon', 'tls_assessment']
    asset_kind = str((asset or {}).get('asset_kind') or 'domain').strip().lower()
    path_prefix = str((asset or {}).get('path_prefix') or '/').strip().lower()
    host = str((asset or {}).get('host') or '').strip().lower()
    allow = {str(x).strip().lower() for x in (focus_allow_keywords or []) if str(x).strip()}
    vectors = {str(x).strip().lower() for x in (global_vectors or []) if str(x).strip()}
    surface = {str(x).strip().lower() for x in (surface_keywords or []) if str(x).strip()}
    lexical = set(surface)
    lexical.update(part for part in path_prefix.replace('-', '/').replace('_', '/').split('/') if part)
    lexical.update(part for part in host.replace('-', '.').split('.') if part)
    has_specific_path = path_prefix not in {'', '/'}
    stateful_markers = {'auth', 'login', 'signin', 'session', 'account', 'profile', 'id', 'oauth', 'token', 'store', 'shop', 'cart', 'checkout', 'order', 'wallet', 'billing', 'payment', 'payments'}
    client_markers = {'store', 'shop', 'portal', 'page', 'help', 'support', 'content', 'search', 'blog', 'news', 'docs', 'forum'}
    infra_markers = {'cloud', 'proxy', 'internal', 'callback', 'partner', 'integration', 'safe', 'api'}
    stateful_signal = bool(lexical & stateful_markers)
    client_signal = bool(lexical & client_markers) or has_specific_path
    infra_signal = bool(lexical & infra_markers)

    effective_target_type = str(target_type or 'host').strip().lower() or 'host'
    if effective_target_type == 'host':
        effective_target_type = 'web'
        if any(k in lexical for k in {'api', 'json', 'callback', 'oauth', 'token', 'partner', 'integration'}):
            effective_target_type = 'integration'
        elif any(k in lexical for k in {'auth', 'login', 'signin', 'account', 'id', 'sso'}):
            effective_target_type = 'auth'

    broad_host_only = {'recon', 'tls_assessment', 'subdomain_expansion', 'historical_url_mining'}
    narrowed = [fam for fam in fams if fam not in broad_host_only]
    all_candidates = set(narrowed)
    all_candidates.update({'content_discovery'})
    if effective_target_type in {'auth', 'api', 'integration'} or stateful_signal or 'auth_flow' in vectors or 'auth_flow' in narrowed:
        all_candidates.add('auth_flow')
    if effective_target_type == 'auth' or target_cluster == 'identity_auth' or 'authz' in vectors or 'authz' in narrowed:
        all_candidates.add('authz')
    if ('xss' in allow or 'client_input' in vectors or 'client_input' in narrowed) and (client_signal or effective_target_type == 'auth'):
        all_candidates.add('client_input')
    if ('ssrf' in allow or 'input_tamper' in vectors or 'input_tamper' in narrowed) and (infra_signal or effective_target_type in {'api', 'integration'}):
        all_candidates.add('input_tamper')
    if ('workflow' in vectors or 'workflow' in narrowed or target_cluster == 'commerce_store') and (stateful_signal or any(k in lexical for k in {'store', 'cart', 'checkout', 'order', 'payment', 'reset', 'password'})):
        all_candidates.add('workflow')
    if ('open redirect' in allow or 'redirect_trust' in vectors or 'redirect_trust' in narrowed) and any(k in lexical for k in {'redirect', 'callback', 'return', 'next', 'continue'}):
        all_candidates.add('redirect_trust')
    if effective_target_type in {'static', 'support'} or 'tls_assessment' in fams:
        all_candidates.add('tls_assessment')

    scores: Dict[str, float] = {}
    reasons: Dict[str, List[str]] = {}

    def boost(family: str, amount: float, reason: str) -> None:
        fam = str(family or '').strip().lower()
        if not fam:
            return
        scores[fam] = max(scores.get(fam, 0.0), 0.0) + amount
        reasons.setdefault(fam, []).append(reason)

    for fam in narrowed:
        boost(fam, 0.52, 'seeded_from_target_profile')
    if 'content_discovery' in all_candidates:
        boost('content_discovery', 0.58, 'baseline_surface_mapping')
        if has_specific_path:
            boost('content_discovery', 0.1, 'exact_path_scope')
    if 'tls_assessment' in all_candidates and (effective_target_type in {'static', 'support'} or target_cluster == 'static_media'):
        boost('tls_assessment', 0.72 if asset_kind == 'domain' else 0.68, 'static_or_support_posture_signal')
    if 'auth_flow' in all_candidates and (effective_target_type in {'auth', 'api', 'integration'} or stateful_signal):
        boost('auth_flow', 0.74 if effective_target_type == 'auth' or target_cluster == 'identity_auth' else 0.64, 'stateful_or_boundary_signal')
    if 'authz' in all_candidates and (effective_target_type == 'auth' or target_cluster == 'identity_auth'):
        boost('authz', 0.76, 'identity_or_auth_surface')
    if 'client_input' in all_candidates and ('xss' in allow or 'client_input' in vectors):
        if client_signal:
            boost('client_input', 0.7 if has_specific_path else 0.6, 'client_render_or_specific_path_signal')
    if 'input_tamper' in all_candidates and ('ssrf' in allow or 'input_tamper' in vectors):
        if infra_signal or effective_target_type in {'api', 'integration'} or target_cluster == 'infra_edge':
            boost('input_tamper', 0.72, 'infra_or_trust_boundary_signal')
    if 'workflow' in all_candidates and ('workflow' in vectors or target_cluster in {'commerce_store', 'money'}):
        if stateful_signal or any(k in lexical for k in {'store', 'cart', 'checkout', 'order', 'payment', 'reset', 'password'}):
            boost('workflow', 0.68, 'stateful_business_flow_signal')
    if 'redirect_trust' in all_candidates and ('redirect_trust' in vectors or 'open redirect' in allow):
        if any(k in lexical for k in {'redirect', 'callback', 'return', 'next', 'continue'}):
            boost('redirect_trust', 0.66, 'redirect_flow_signal')

    if target_cluster == 'identity_auth':
        boost('auth_flow', 0.08, 'identity_cluster_bias')
        boost('authz', 0.08, 'identity_cluster_bias')
    elif target_cluster == 'money':
        boost('authz', 0.1, 'money_cluster_bias')
        boost('auth_flow', 0.08, 'money_cluster_bias')
        boost('workflow', 0.08, 'money_cluster_bias')
    elif target_cluster == 'commerce_store':
        boost('workflow', 0.08, 'commerce_cluster_bias')
        boost('content_discovery', 0.05, 'commerce_cluster_bias')
    elif target_cluster == 'infra_edge':
        boost('input_tamper', 0.08, 'infra_cluster_bias')
    elif target_cluster == 'consumer_web':
        boost('content_discovery', 0.05, 'consumer_web_cluster_bias')
    elif target_cluster == 'ai_chat':
        boost('auth_flow', 0.08, 'ai_chat_cluster_bias')
        if 'client_input' in all_candidates:
            boost('client_input', 0.06, 'ai_chat_cluster_bias')
    elif target_cluster == 'integration_api':
        boost('authz', 0.08, 'integration_api_cluster_bias')
        boost('input_tamper', 0.08, 'integration_api_cluster_bias')

    if asset_kind != 'url' and target_cluster == 'identity_auth':
        scores['recon'] = min(scores.get('recon', 0.0), 0.34)
        scores['tls_assessment'] = min(scores.get('tls_assessment', 0.0), 0.3)
    if asset_kind != 'url' and target_cluster in {'consumer_web', 'commerce_store'} and not stateful_signal:
        scores['recon'] = min(scores.get('recon', 0.0), 0.36)
        scores['tls_assessment'] = min(scores.get('tls_assessment', 0.0), 0.31)

    if not has_specific_path and effective_target_type == 'web' and not stateful_signal and not infra_signal:
        scores['auth_flow'] = min(scores.get('auth_flow', 0.0), 0.34)
        scores['client_input'] = min(scores.get('client_input', 0.0), 0.29)
        scores['input_tamper'] = min(scores.get('input_tamper', 0.0), 0.25)

    selection_threshold = 0.58
    max_selected = 4
    if asset_kind == 'domain' and target_cluster == 'identity_auth':
        max_selected = 3
    elif asset_kind == 'url' and not has_specific_path and target_cluster in {'consumer_web', 'general'}:
        max_selected = 2

    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    selected = [fam for fam, score in ranked if score >= selection_threshold][:max_selected]
    if len(selected) >= 3:
        weakest = selected[-1]
        weakest_score = float(scores.get(weakest, 0.0))
        strongest_score = float(scores.get(selected[0], 0.0))
        preserve_boundary_family = weakest in {'authz', 'auth_flow'} and effective_target_type in {'api', 'auth', 'integration'}
        if not preserve_boundary_family and weakest_score < 0.67 and (strongest_score - weakest_score) >= 0.26:
            selected = selected[:-1]
    if not selected:
        selected = ['content_discovery']
        scores.setdefault('content_discovery', 0.6)
        reasons.setdefault('content_discovery', []).append('safe_default')

    suppressed: List[Dict[str, Any]] = []
    seen_suppressed: set[tuple[str, str]] = set()
    for fam in sorted(all_candidates):
        if fam in selected:
            continue
        reason = 'suppressed_low_confidence'
        if fam == 'auth_flow' and not stateful_signal:
            reason = 'suppressed_no_stateful_or_auth_signal'
        elif fam == 'authz' and target_cluster != 'identity_auth' and effective_target_type != 'auth':
            reason = 'suppressed_no_identity_or_auth_boundary_signal'
        elif fam == 'client_input' and not client_signal:
            reason = 'suppressed_no_client_render_or_specific_path_signal'
        elif fam == 'input_tamper' and not infra_signal and effective_target_type not in {'api', 'integration'}:
            reason = 'suppressed_no_infra_or_trust_boundary_signal'
        elif fam == 'workflow' and not stateful_signal:
            reason = 'suppressed_no_stateful_business_flow_signal'
        key = (fam, reason)
        if key in seen_suppressed:
            continue
        seen_suppressed.add(key)
        suppressed.append({
            'family': fam,
            'reason': reason,
            'score': round(float(scores.get(fam, 0.0)), 2),
            'threshold': selection_threshold,
        })

    return {
        'selected_families': selected,
        'family_confidence': {fam: round(float(scores.get(fam, 0.0)), 2) for fam in selected},
        'suppressed_task_families': suppressed[:6],
    }


def _families_for_scope_asset(*, asset: Dict[str, Any], families: List[str], target_type: str, target_cluster: str, surface_keywords: List[str], focus_allow_keywords: List[str], global_vectors: List[str]) -> List[str]:
    decision = _family_decision_for_scope_asset(
        asset=asset,
        families=families,
        target_type=target_type,
        target_cluster=target_cluster,
        surface_keywords=surface_keywords,
        focus_allow_keywords=focus_allow_keywords,
        global_vectors=global_vectors,
    )
    return [str(x).strip().lower() for x in (decision.get('selected_families') or []) if str(x).strip()]


def _build_experiment_intents(
    *,
    domains: List[str],
    authoritative_assets: List[Dict[str, Any]],
    target_profiles: Dict[str, Any],
    task_family_seeds: Dict[str, List[str]],
    planner_directives: Dict[str, Any],
    credentials_policy: Dict[str, Any],
) -> List[Dict[str, Any]]:
    preferences = planner_directives.get('preferences') if isinstance(planner_directives.get('preferences'), dict) else {}
    constraints = planner_directives.get('constraints') if isinstance(planner_directives.get('constraints'), dict) else {}
    unknowns = planner_directives.get('unknowns') if isinstance(planner_directives.get('unknowns'), dict) else {}
    per_target_vectors = preferences.get('per_target_vectors') if isinstance(preferences.get('per_target_vectors'), dict) else {}
    per_target_execution_hints = preferences.get('per_target_execution_hints') if isinstance(preferences.get('per_target_execution_hints'), dict) else {}
    recommended_families = [str(x).strip().lower() for x in (preferences.get('recommended_task_families') or []) if str(x).strip()]
    deprioritized = [str(x).strip().lower() for x in (preferences.get('deprioritized_task_families') or []) if str(x).strip()]
    global_vectors = [str(x).strip().lower() for x in (preferences.get('global_vectors') or []) if str(x).strip()]
    focus_allow_keywords = [str(x).strip().lower() for x in (preferences.get('focus_allow_keywords') or []) if str(x).strip()]
    surface_map = preferences.get('target_surface_keywords') if isinstance(preferences.get('target_surface_keywords'), dict) else {}
    ambiguities = [str(x).strip() for x in (unknowns.get('ambiguities') or []) if str(x).strip()]
    interpretation_conflicts = [str(x).strip() for x in (unknowns.get('interpretation_conflicts') or []) if str(x).strip()]
    asset_entries = _normalized_authoritative_assets(authoritative_assets=authoritative_assets, domains=domains)

    intents: List[Dict[str, Any]] = []
    for asset in asset_entries:
        host = str(asset.get('host') or '').strip().lower()
        if not host:
            continue
        explicit_target = str(asset.get('target') or '').strip()
        profile = target_profiles.get(host) if isinstance(target_profiles.get(host), dict) else {}
        fams = task_family_seeds.get(host) if isinstance(task_family_seeds.get(host), list) else profile.get('task_family_seeds', [])
        target_type = str(profile.get('target_type') or profile.get('type') or 'host')
        target_cluster = str(profile.get('target_cluster') or 'general').strip().lower() or 'general'
        family_decision = _family_decision_for_scope_asset(
            asset=asset,
            families=list(fams or []),
            target_type=target_type,
            target_cluster=target_cluster,
            surface_keywords=[str(x).strip().lower() for x in (surface_map.get(host) or []) if str(x).strip()],
            focus_allow_keywords=focus_allow_keywords,
            global_vectors=global_vectors,
        )
        families = [str(x).strip().lower() for x in (family_decision.get('selected_families') or []) if str(x).strip()]
        for fam in families:
            evidence_contract = _evidence_contract_for_family(fam)
            capability_candidates = [str(x).strip().lower() for x in (suggest_capabilities_for_task_family(fam) or []) if str(x).strip()]
            if not capability_candidates:
                success_model = str(evidence_contract.get('success_model') or '')
                if success_model == 'surface_expansion':
                    capability_candidates = ['content_discovery']
                elif success_model == 'differential_or_stateful_signal':
                    capability_candidates = ['http_probe']
                elif success_model == 'fingerprint_or_exposure_signal':
                    capability_candidates = ['http_fingerprint']
                else:
                    capability_candidates = ['http_probe']
            preferred_vectors = [str(x).strip().lower() for x in (per_target_vectors.get(host) or []) if str(x).strip()]
            candidate_vectors = [str(x).strip().lower() for x in (profile.get('candidate_vectors') or []) if str(x).strip()] if isinstance(profile.get('candidate_vectors'), list) else []
            hypothesis_candidates = list(dict.fromkeys(candidate_vectors + preferred_vectors + global_vectors))[:8]
            intent_seed = f'{explicit_target or host}|{fam}|{_family_objective(fam)}'
            intent_id = hashlib.sha256(intent_seed.encode('utf-8')).hexdigest()[:16]
            planner_constraints = {
                'campaign_bound_context': bool(constraints.get('campaign_bound_context', True)),
                'in_scope_only': bool(constraints.get('in_scope_only', True)),
                'credentials_required': bool(credentials_policy.get('credentials_required', False)),
                'allow_auth_header': bool(credentials_policy.get('allow_auth_header', False)),
                'allow_cookie_header': bool(credentials_policy.get('allow_cookie_header', False)),
                'allow_basic_auth': bool(credentials_policy.get('allow_basic_auth', False)),
                'owner_approval_required': bool(credentials_policy.get('owner_approval_required', True)),
                'recommended_aggression_min': constraints.get('recommended_aggression_min'),
                'recommended_aggression_max': constraints.get('recommended_aggression_max'),
            }
            planner_preferences = {
                'preferred_vector_families': preferred_vectors[:6],
                'recommended_task_families': recommended_families[:8],
                'deprioritized_task_families': deprioritized[:8],
                'surface_keywords': [str(x).strip().lower() for x in (surface_map.get(host) or []) if str(x).strip()][:6],
                'focus_allow_keywords': focus_allow_keywords[:8],
                'scope_asset_kind': str(asset.get('asset_kind') or 'domain'),
                'scope_path_prefix': str(asset.get('path_prefix') or '/'),
                'scope_source': str(asset.get('scope_source') or 'authoritative'),
                'family_confidence': dict(family_decision.get('family_confidence') or {}),
                'suppressed_task_families': list(family_decision.get('suppressed_task_families') or []),
            }
            auth_available = bool(planner_constraints.get('allow_auth_header') or planner_constraints.get('allow_cookie_header') or planner_constraints.get('allow_basic_auth') or planner_constraints.get('credentials_required'))
            target_specific_action_types = _target_specific_action_types_for_family(
                fam,
                target_type=target_type,
                auth_available=auth_available,
                surface_keywords=[str(x).strip().lower() for x in (surface_map.get(host) or []) if str(x).strip()][:6],
            )
            profile_execution_hints = dict(per_target_execution_hints.get(host) or {}) if isinstance(per_target_execution_hints.get(host), dict) else {}
            execution_hints = _intent_execution_hints(profile=profile_execution_hints or profile, fam=fam)
            runtime_task_contract = _runtime_task_contract_for_intent(
                host=host,
                target=explicit_target or f'https://{host}/',
                fam=fam,
                target_type=target_type,
                capability_candidates=capability_candidates[:6],
                recommended_action_types=target_specific_action_types,
                hypothesis_candidates=hypothesis_candidates,
                evidence_contract=evidence_contract,
                planner_constraints=planner_constraints,
                planner_preferences=planner_preferences,
                intent_id=intent_id,
                ambiguities=ambiguities[:4],
                open_questions=interpretation_conflicts[:4],
                execution_hints=execution_hints,
            )
            intents.append(compose_experiment_intent_contract(
                base_intent={
                    'intent_id': intent_id,
                    'target_host': host,
                    'target': explicit_target or f'https://{host}/',
                    'target_type': target_type,
                    'scope_asset_kind': str(asset.get('asset_kind') or 'domain'),
                    'scope_path_prefix': str(asset.get('path_prefix') or '/'),
                    'scope_source': str(asset.get('scope_source') or 'authoritative'),
                    'task_family': fam,
                    'objective': _family_objective(fam),
                    'capability_candidates': capability_candidates[:6],
                    'recommended_action_types': target_specific_action_types,
                    'hypothesis_candidates': hypothesis_candidates,
                    'evidence_contract': {
                        'acceptance_checks': list(evidence_contract.get('acceptance_checks') or []),
                        'evidence_required': list(evidence_contract.get('evidence_required') or []),
                        'expected_signal_type': str(evidence_contract.get('expected_signal_type') or ''),
                        'evidence_goal_type': str(evidence_contract.get('evidence_goal_type') or ''),
                    },
                    'success_model': str(evidence_contract.get('success_model') or ''),
                    'negative_control_requirements': list(evidence_contract.get('negative_control_requirements') or []),
                    'planner_constraints': planner_constraints,
                    'planner_preferences': planner_preferences,
                    'priority_tier': execution_hints.get('priority_tier'),
                    'expected_depth': execution_hints.get('expected_depth'),
                    'activation_phase': execution_hints.get('activation_phase'),
                    'activation_mode': execution_hints.get('activation_mode'),
                    'conditional_gate': execution_hints.get('conditional_gate'),
                    'surface_role': execution_hints.get('surface_role'),
                    'target_cluster': execution_hints.get('target_cluster'),
                    'ambiguity_flags': ambiguities[:4],
                    'open_questions': interpretation_conflicts[:4],
                },
                runtime_task_contract=runtime_task_contract,
                success_model=str(evidence_contract.get('success_model') or ''),
            ))
    return intents


def build_blueprint(parsed: Dict[str, Any], operator_input: Dict[str, Any], interpretations: List[Dict[str, Any]]) -> Dict[str, Any]:
    source_hash = parsed["source_hash"]
    identity = build_planner_identity(parsed, operator_input)
    planner_identity_hash = identity["planner_identity_hash"]
    campaign_id = str(uuid.uuid5(NAMESPACE_UUID, planner_identity_hash))
    variants = _build_variants(len(parsed.get("domains", [])))

    flags = (operator_input or {}).get("flags") or {}
    inferred = parsed.get("program_label") or "Campaign"
    client_name = _sanitize_name_part(str(flags.get("client") or flags.get("zleceniodawca") or inferred), "CAMPAIGN")[:16]

    aggression_profile = (operator_input or {}).get("aggression_profile") or {
        "policy_min": 1,
        "policy_max": 10,
        "recommended_min": 3,
        "recommended_default": 5,
        "recommended_max": 7,
        "confidence": 0.6,
        "rationale": ["fallback"],
    }

    llm_meta = (operator_input or {}).get("llm_interpretation") or {}
    credentials_policy = parsed.get("credentials_policy") if isinstance(parsed.get("credentials_policy"), dict) else {
        "credentials_required": False,
        "allow_auth_header": False,
        "allow_cookie_header": False,
        "allow_basic_auth": False,
        "owner_approval_required": True,
        "signals": [],
    }

    target_profiles = parsed.get('target_profiles') if isinstance(parsed.get('target_profiles'), dict) else {}
    authoritative_assets = parsed.get('authoritative_assets') if isinstance(parsed.get('authoritative_assets'), list) else []
    task_family_seeds = {k: list(v.get('task_family_seeds', [])) for k, v in target_profiles.items() if isinstance(v, dict)}
    initial_clusters = _build_target_clusters(target_profiles)
    for cluster_name, cluster_meta in initial_clusters.items():
        primary_hosts = list(cluster_meta.get('primary_hosts') or []) if isinstance(cluster_meta, dict) else []
        for host in list(cluster_meta.get('secondary_hosts') or []) if isinstance(cluster_meta, dict) else []:
            profile = target_profiles.get(host) if isinstance(target_profiles.get(host), dict) else {}
            pruned = _prune_cluster_secondary_families(host=host, profile=profile, primary_hosts=primary_hosts)
            if isinstance(profile, dict):
                profile['cluster_adjusted_task_family_seeds'] = pruned
            task_family_seeds[host] = pruned
    global_vectors = llm_meta.get('suggested_attack_vectors', []) if isinstance(llm_meta, dict) else []
    if not list(global_vectors or []):
        global_vectors = _fallback_global_vectors(
            allow_keywords=list(parsed.get('allow_keywords', []) or []),
            target_profiles=target_profiles,
        )
    candidate_targets = parsed.get('candidate_targets_from_llm', []) if isinstance(parsed.get('candidate_targets_from_llm'), list) else []
    planner_directives = _build_planner_directives(
        task_family_seeds=task_family_seeds,
        target_profiles=target_profiles,
        global_vectors=list(global_vectors or []),
        candidate_targets=list(candidate_targets or []),
        llm_meta=llm_meta if isinstance(llm_meta, dict) else {},
        aggression_profile=aggression_profile,
        credentials_policy=credentials_policy,
        allow_keywords=list(parsed.get('allow_keywords', []) or []),
    )
    experiment_intents = _build_experiment_intents(
        domains=list(parsed.get('domains', []) or []),
        authoritative_assets=[item for item in authoritative_assets if isinstance(item, dict)],
        target_profiles=target_profiles,
        task_family_seeds=task_family_seeds,
        planner_directives=planner_directives,
        credentials_policy=credentials_policy,
    )
    target_clusters = _build_target_clusters(target_profiles)

    payload: Dict[str, Any] = {
        "schema_version": "1.0.0",
        "campaign_id": campaign_id,
        "campaign_name_template": f"{client_name}-V{{version}}-{planner_identity_hash[:8].upper()}",
        "source_program_hash_sha256": source_hash,
        "operator_flags_hash_sha256": identity["operator_flags_hash"],
        "planner_semantics_hash_sha256": identity["planner_semantics_hash"],
        "planner_identity_hash_sha256": planner_identity_hash,
        "planner_provenance_mode": identity["planner_provenance_mode"],
        "version": 1,
        "operator_approval": {"status": "pending", "approved": False},
        "operator_input": operator_input,
        "aggression_profile": aggression_profile,
        "credentials_policy": credentials_policy,
        "planner_hints": {
            "global_vectors": global_vectors,
            "per_target_vectors": {host: fams[:3] for host, fams in task_family_seeds.items()},
            "per_target_execution_hints": {
                host: {
                    'priority_tier': str((profile or {}).get('priority_tier') or 'medium').strip().lower(),
                    'expected_depth': str((profile or {}).get('expected_depth') or 'medium').strip().lower(),
                    'surface_role': str((profile or {}).get('surface_role') or 'primary').strip().lower(),
                    'target_cluster': str((profile or {}).get('target_cluster') or 'general').strip().lower(),
                }
                for host, profile in target_profiles.items()
                if isinstance(profile, dict)
            },
            "target_clusters": target_clusters,
            "recommended_task_families": sorted({fam for fams in task_family_seeds.values() for fam in fams}),
            "deprioritized_task_families": ['secret_hunt'] if credentials_policy.get('credentials_required') else [],
            "candidate_targets": candidate_targets,
            "ambiguities": llm_meta.get("ambiguities", []),
            "llm_used": bool(llm_meta.get("used", False)),
            "llm_confidence": llm_meta.get("llm_confidence"),
            "interpretation_conflicts": llm_meta.get("conflicts", []),
        },
        "planner_directives": planner_directives,
        "variants": [
            {
                "name": v.name,
                "summary": v.summary,
                "suggested_aggression": v.suggested_aggression,
                "first_vectors": v.first_vectors,
            }
            for v in variants
        ],
        "structured_scope": {
            "authoritative_assets": authoritative_assets,
            "authoritative_domains": parsed.get("domains", []),
            "candidate_targets_from_llm": candidate_targets,
            "invalid_domain_candidates": parsed.get('invalid_domain_candidates', []),
            "domains": parsed.get("domains", []),
            "out_of_scope_targets": parsed.get("out_of_scope_targets", []),
            "targets": parsed.get("targets", []),
            "allow_keywords": parsed.get("allow_keywords", []),
            "deny_keywords": parsed.get("deny_keywords", []),
        },
        "target_profiles": target_profiles,
        "task_family_seeds": task_family_seeds,
        "experiment_intents": experiment_intents,
        "attack_taxonomy": {
            "initial_vectors": ["recon", "input-validation", "authz", "xss-safe-probes"],
            "recommended_task_families": sorted({fam for fams in task_family_seeds.values() for fam in fams}),
            "disallowed": parsed.get("deny_keywords", []),
        },
        "interpretations": interpretations,
        "budget_recommendations": {
            v.name: {"max_usd": v.budget_usd, "rationale": "derived_from_variant_strategy"}
            for v in variants
        },
        "target_taxonomy": {
            "counts": {
                "total": len(parsed.get("targets", [])),
                "api": sum(1 for t in parsed.get("targets", []) if _target_type(t) == "api"),
                "web": sum(1 for t in parsed.get("targets", []) if _target_type(t) == "web"),
                "auth": sum(1 for t in parsed.get("targets", []) if _target_type(t) == "auth"),
                "static": sum(1 for t in parsed.get("targets", []) if _target_type(t) == "static"),
                "sandbox": sum(1 for t in parsed.get("targets", []) if _target_type(t) == "sandbox"),
                "integration": sum(1 for t in parsed.get("targets", []) if _target_type(t) == "integration"),
                "support": sum(1 for t in parsed.get("targets", []) if _target_type(t) == "support"),
                "other": sum(1 for t in parsed.get("targets", []) if _target_type(t) not in {"api", "web", "auth", "static", "sandbox", "integration", "support"}),
            }
        },
        "success_criteria": {v.name: v.success_criteria for v in variants},
        "versioning": {
            "engine": "PLANER",
            "deterministic": identity["planner_provenance_mode"] == "deterministic",
            "planner_provenance_mode": identity["planner_provenance_mode"],
            "planner_semantics_version": identity["planner_semantics_version"],
            "reconcile_mode": identity["reconcile_mode"],
            "source_hash": source_hash,
            "operator_flags_hash": identity["operator_flags_hash"],
            "planner_semantics_hash": identity["planner_semantics_hash"],
            "planner_identity_hash": planner_identity_hash,
        },
    }

    payload["blueprint_hash_sha256"] = _stable_hash(payload)
    validate_blueprint(payload)
    return payload
