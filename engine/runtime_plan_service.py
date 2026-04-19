from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any
from urllib.parse import urlparse

from json_state_io import atomic_write_json  # type: ignore
from paths import REPORTS_DIR, RUNTIME_PLAN_PATH, LEGACY_RUNTIME_PLAN_PATH, first_existing  # type: ignore
from planer.planner_intent_contract import build_planning_ladder, recommended_progression_from_planning_ladder  # type: ignore
from runtime_state_schemas import normalize_runtime_plan_meta  # type: ignore
from semantic_lineage import build_semantic_lineage  # type: ignore
from runtime_plan_blueprint_registry import load_active_campaign_blueprint as load_active_campaign_blueprint_helper, load_campaign_blueprint_for_key as load_campaign_blueprint_for_key_helper  # type: ignore
from runtime_plan_selection import load_planner_ui_state as load_planner_ui_state_helper, resolve_runtime_campaign_key as resolve_runtime_campaign_key_helper, resolve_selected_campaign_key as resolve_selected_campaign_key_helper, save_planner_ui_state as save_planner_ui_state_helper  # type: ignore
from runtime_task_schema import normalize_runtime_task_v2  # type: ignore
from time_utils import utc_now_iso  # type: ignore

PLANNER_REGISTRY_ROOT = REPORTS_DIR / "campaign_registry"
PLANNER_UI_STATE_PATH = REPORTS_DIR / ".planner.ui.state.json"
RUNTIME_PLAN_META_PATH = REPORTS_DIR / ".runtime_plan.meta.json"
HOST_TOKEN_RE = re.compile(r"(https?://[^\s\"'<>]+)|\b((?:[a-z0-9-]+\.)+[a-z]{2,})\b", re.IGNORECASE)


def _extract_hosts_from_text(text: object) -> list[str]:
    raw = str(text or '').strip()
    if not raw:
        return []
    from urllib.parse import urlparse
    hosts: list[str] = []
    seen: set[str] = set()
    parsed = str(urlparse(raw).hostname or '').strip().lower() if raw.startswith(('http://', 'https://')) else ''
    if parsed:
        hosts.append(parsed)
        seen.add(parsed)
    for match in HOST_TOKEN_RE.finditer(raw):
        token = str(match.group(1) or match.group(2) or '').strip().lower()
        host = str(urlparse(token if token.startswith(('http://', 'https://')) else '//' + token).hostname or '').strip().lower()
        if host and host not in seen:
            seen.add(host)
            hosts.append(host)
    return hosts


def _string_is_target_bound(text: object, target_host: str) -> bool:
    host = str(target_host or '').strip().lower()
    if not host:
        return True
    mentioned = _extract_hosts_from_text(text)
    if not mentioned:
        return True
    return all(item == host for item in mentioned)


def _sanitize_text_list_for_host(items: object, host: str) -> list[str]:
    return [str(x).strip() for x in (items or []) if str(x).strip() and _string_is_target_bound(x, host)]


def load_planner_ui_state() -> Dict[str, object]:
    return load_planner_ui_state_helper(planner_ui_state_path=PLANNER_UI_STATE_PATH)


def save_planner_ui_state(data: Dict[str, object]) -> None:
    save_planner_ui_state_helper(data, reports_dir=REPORTS_DIR, planner_ui_state_path=PLANNER_UI_STATE_PATH)


def resolve_selected_campaign_key(state_selected_key: str | None = None) -> str:
    return resolve_selected_campaign_key_helper(
        state_selected_key=state_selected_key,
        load_planner_ui_state_fn=load_planner_ui_state,
    )


def resolve_runtime_campaign_key(selected_key: str | None = None, runtime_plan_meta: Dict[str, Any] | None = None) -> str:
    return resolve_runtime_campaign_key_helper(
        selected_key=selected_key,
        runtime_plan_meta=runtime_plan_meta,
        load_runtime_plan_meta_fn=load_runtime_plan_meta,
        resolve_selected_campaign_key_fn=resolve_selected_campaign_key,
    )


def load_campaign_blueprint_for_key(key: str) -> tuple[Path, Path, dict] | tuple[None, None, None]:
    return load_campaign_blueprint_for_key_helper(key, planner_registry_root=PLANNER_REGISTRY_ROOT)


def load_active_campaign_blueprint(selected_key: str | None = None, runtime_plan_meta: Dict[str, Any] | None = None) -> tuple[str, Path | None, Path | None, dict | None]:
    return load_active_campaign_blueprint_helper(
        selected_key=selected_key,
        runtime_plan_meta=runtime_plan_meta,
        resolve_runtime_campaign_key_fn=resolve_runtime_campaign_key,
        load_campaign_blueprint_for_key_fn=load_campaign_blueprint_for_key,
    )


def _normalize_scope_target_url(value: object) -> str:
    raw = str(value or '').strip()
    if not raw.startswith(('http://', 'https://')):
        return ''
    parsed = urlparse(raw)
    host = str(parsed.hostname or '').strip().lower()
    if not host:
        return ''
    out = f'{parsed.scheme.lower()}://{host}{parsed.path or "/"}'
    if parsed.query:
        out += f'?{parsed.query}'
    if parsed.fragment:
        out += f'#{parsed.fragment}'
    return out


def runtime_plan_entries_from_blueprint(bp: Dict[str, object]) -> List[Dict[str, object]]:
    ss = bp.get("structured_scope") if isinstance(bp.get("structured_scope"), dict) else {}
    domains = [str(d).strip().lower() for d in (ss.get("authoritative_domains", ss.get("domains")) or []) if str(d).strip()] if isinstance(ss, dict) else []
    out_scope = [str(d).strip().lower() for d in (ss.get("out_of_scope_targets") or []) if str(d).strip()] if isinstance(ss, dict) else []
    authoritative_assets_raw = ss.get('authoritative_assets') if isinstance(ss, dict) and isinstance(ss.get('authoritative_assets'), list) else []
    allow_keywords = {str(k).strip().lower() for k in (ss.get("allow_keywords") or [])} if isinstance(ss, dict) else set()
    target_profiles = bp.get("target_profiles") if isinstance(bp.get("target_profiles"), dict) else {}
    family_seeds = bp.get("task_family_seeds") if isinstance(bp.get("task_family_seeds"), dict) else {}
    planner_hints = bp.get("planner_hints") if isinstance(bp.get("planner_hints"), dict) else {}
    planner_directives = bp.get("planner_directives") if isinstance(bp.get("planner_directives"), dict) else {}
    experiment_intents = bp.get("experiment_intents") if isinstance(bp.get("experiment_intents"), list) else []
    aggression_profile = bp.get("aggression_profile") if isinstance(bp.get("aggression_profile"), dict) else {}

    allow_exact = set()
    allow_suffix = set()
    deny_exact = set()
    deny_suffix = set()

    for d in domains:
        if d.startswith("*."):
            allow_suffix.add(d[2:])
        else:
            allow_exact.add(d)
    for d in out_scope:
        if d.startswith("*."):
            deny_suffix.add(d[2:])
        else:
            deny_exact.add(d)

    authoritative_domain_hosts: set[str] = set()
    authoritative_exact_targets_by_host: dict[str, set[str]] = {}
    for raw in authoritative_assets_raw:
        if not isinstance(raw, dict):
            continue
        asset_kind = str(raw.get('asset_kind') or 'domain').strip().lower() or 'domain'
        host = str(raw.get('host') or '').strip().lower()
        target = str(raw.get('target') or '').strip()
        if not host:
            continue
        if asset_kind == 'url':
            norm_target = _normalize_scope_target_url(target)
            if norm_target:
                authoritative_exact_targets_by_host.setdefault(host, set()).add(norm_target)
        else:
            authoritative_domain_hosts.add(host)

    if not authoritative_domain_hosts and not authoritative_exact_targets_by_host:
        authoritative_domain_hosts.update(domains)

    def _in_scope(host: str) -> bool:
        h = str(host or "").strip().lower()
        if not h:
            return False
        if h in deny_exact:
            return False
        if any(h == s or h.endswith("." + s) for s in deny_suffix):
            return False
        if h in allow_exact:
            return True
        if any(h == s or h.endswith("." + s) for s in allow_suffix):
            return True
        return False

    def _target_matches_authoritative_scope(target: str, host: str) -> bool:
        h = str(host or '').strip().lower()
        if not h or not _in_scope(h):
            return False
        exact_targets = authoritative_exact_targets_by_host.get(h) or set()
        if not exact_targets:
            return True
        if h in authoritative_domain_hosts:
            return True
        normalized_target = _normalize_scope_target_url(target)
        return bool(normalized_target and normalized_target in exact_targets)

    family_objectives = {
        'recon': ['Passive recon and endpoint discovery'],
        'subdomain_expansion': ['Subdomain expansion and passive asset enumeration'],
        'historical_url_mining': ['Historical URL and legacy endpoint mining'],
        'content_discovery': ['Content discovery and path surface mapping'],
        'tls_assessment': ['TLS/certificate and HTTPS posture checks'],
        'secret_hunt': ['Client-side secret exposure surface review'],
        'authz': ['AuthN/AuthZ boundary probing (safe)'],
        'auth_flow': ['Authentication flow hardening checks (state/nonce/session)'],
        'logic': ['Business-logic flow consistency checks'],
        'client_input': ['Reflected/stored XSS safe probe paths'],
        'input_tamper': ['Input validation and parameter tampering checks'],
        'redirect_trust': ['Open redirect and redirect-trust boundary checks'],
    }

    def _objectives_for_host(host: str) -> list[tuple[str, str]]:
        profile = target_profiles.get(host) if isinstance(target_profiles.get(host), dict) else {}
        seeds = family_seeds.get(host) if isinstance(family_seeds.get(host), list) else profile.get("task_family_seeds", [])
        fams = [str(x).strip().lower() for x in (seeds or []) if str(x).strip()]
        if not fams:
            fams = ["recon", "tls_assessment"]
        out: list[tuple[str, str]] = []
        for fam in fams:
            for objective in family_objectives.get(fam, ["Passive recon and endpoint discovery"]):
                out.append((fam, objective))
        return out

    def _profile_summary(profile: dict) -> dict:
        if not isinstance(profile, dict):
            return {}
        return {
            'target_type': str(profile.get('target_type') or profile.get('type') or ''),
            'surface_keywords': list(profile.get('surface_keywords') or [])[:6] if isinstance(profile.get('surface_keywords'), list) else [],
            'task_family_seeds': [str(x).strip().lower() for x in (profile.get('task_family_seeds') or []) if str(x).strip()][:6],
            'candidate_vectors': [str(x).strip() for x in (profile.get('candidate_vectors') or []) if str(x).strip()][:6] if isinstance(profile.get('candidate_vectors'), list) else [],
            'notes': [str(x).strip() for x in (profile.get('notes') or []) if str(x).strip()][:4] if isinstance(profile.get('notes'), list) else [],
            'priority_tier': str(profile.get('priority_tier') or 'medium').strip().lower() or 'medium',
            'expected_depth': str(profile.get('expected_depth') or 'medium').strip().lower() or 'medium',
            'surface_role': str(profile.get('surface_role') or 'primary').strip().lower() or 'primary',
            'target_cluster': str(profile.get('target_cluster') or 'general').strip().lower() or 'general',
        }

    def _success_semantics_for_family(fam: str) -> dict:
        fam = str(fam or '').strip().lower()
        if fam in {'authz', 'auth_flow', 'logic', 'redirect_trust'}:
            return {'success_model': 'differential_or_stateful_signal', 'expected_signal_type': 'behavior_delta', 'evidence_goal_type': 'controlled_comparison'}
        if fam in {'content_discovery', 'historical_url_mining', 'subdomain_expansion', 'recon'}:
            return {'success_model': 'surface_expansion', 'expected_signal_type': 'novel_asset_or_endpoint', 'evidence_goal_type': 'enumeration_gain'}
        if fam in {'tls_assessment', 'secret_hunt'}:
            return {'success_model': 'fingerprint_or_exposure_signal', 'expected_signal_type': 'configuration_or_exposure_clue', 'evidence_goal_type': 'evidence_capture'}
        return {'success_model': 'generic_signal', 'expected_signal_type': 'technical_signal', 'evidence_goal_type': 'evidence_capture'}

    directive_preferences = planner_directives.get('preferences') if isinstance(planner_directives.get('preferences'), dict) else {}
    directive_unknowns = planner_directives.get('unknowns') if isinstance(planner_directives.get('unknowns'), dict) else {}

    def _planner_field_ownership(
        *,
        planner_input_source: str,
        field_ownership_flags: dict | None = None,
        explicit_evidence_contract: dict | None = None,
    ) -> dict:
        flags = field_ownership_flags if isinstance(field_ownership_flags, dict) else {}
        evidence_contract = explicit_evidence_contract if isinstance(explicit_evidence_contract, dict) else {}
        strict_from_input: list[str] = []
        derived_or_defaulted: list[str] = []
        field_checks = [
            ('target', bool(flags.get('target'))),
            ('task_family', bool(flags.get('task_family'))),
            ('objective', bool(flags.get('objective'))),
            ('capability_candidates', bool(flags.get('capability_candidates'))),
            ('recommended_action_types', bool(flags.get('recommended_action_types'))),
            ('hypothesis_candidates', bool(flags.get('hypothesis_candidates'))),
            ('experiment_intent_id', bool(flags.get('experiment_intent_id'))),
            ('planner_constraints', bool(flags.get('planner_constraints'))),
            ('planner_preferences', bool(flags.get('planner_preferences'))),
            ('acceptance_checks', 'acceptance_checks' in evidence_contract),
            ('evidence_required', 'evidence_required' in evidence_contract),
            ('success_semantics.success_model', bool(flags.get('success_model'))),
            ('success_semantics.expected_signal_type', 'expected_signal_type' in evidence_contract),
            ('success_semantics.evidence_goal_type', 'evidence_goal_type' in evidence_contract),
            ('task_success_criteria', False),
        ]
        for field_name, from_input in field_checks:
            if from_input:
                strict_from_input.append(field_name)
            else:
                derived_or_defaulted.append(field_name)
        return {
            'contract_mode': planner_input_source,
            'strict_from_input': strict_from_input,
            'derived_or_defaulted': derived_or_defaulted,
        }

    def _task_contract_for_family(fam: str, host: str) -> tuple[list[str], list[str], str]:
        acceptance_checks: list[str] = []
        evidence_required: list[str] = []
        success_criteria = ''
        if fam in {"authz", "auth_flow"}:
            acceptance_checks = ["negative_control", "allow_deny_delta"]
            evidence_required = ["http_status", "response_diff"]
            success_criteria = "Validate authz boundary behavior with negative control and clear allow/deny evidence."
        elif fam in {"client_input", "input_tamper", "redirect_trust"}:
            acceptance_checks = ["safe_probe_only", "false_positive_guard"]
            evidence_required = ["reflection_or_behavior_delta"]
            success_criteria = "Confirm input/trust-boundary behavior using safe probes and false-positive guard evidence."
        elif fam == "recon":
            acceptance_checks = ["signal_inventory"]
            evidence_required = ["endpoint_or_header_inventory"]
            success_criteria = "Produce reproducible endpoint/parameter inventory with at least one validated high-value probe path."
        return acceptance_checks, evidence_required, success_criteria + (f" Focus vectors: {', '.join(sorted(allow_keywords)[:4])} on host {host}." if allow_keywords else "")

    def _build_entry(
        *,
        host: str,
        fam: str,
        objective: str,
        profile: dict,
        preferred_vector_families: list[str],
        recommended_task_families: list[str],
        deprioritized_task_families: list[str],
        ambiguity_flags: list[str],
        interpretation_conflicts: list[str],
        capability_candidates: list[str] | None = None,
        recommended_action_types: list[str] | None = None,
        hypothesis_candidates: list[str] | None = None,
        planner_constraints: dict | None = None,
        planner_preferences: dict | None = None,
        experiment_intent_id: str = '',
        open_questions: list[str] | None = None,
        explicit_target: str = '',
        explicit_success_model: str = '',
        explicit_evidence_contract: dict | None = None,
        explicit_runtime_task_contract: dict | None = None,
        explicit_planning_ladder: dict | None = None,
        planner_input_source: str = 'legacy_seed_synthesis',
        field_ownership_flags: dict | None = None,
    ) -> Dict[str, object]:
        target = explicit_target or f"https://{host}/"
        default_acceptance_checks, default_evidence_required, success_criteria = _task_contract_for_family(fam, host)
        explicit_evidence_contract = explicit_evidence_contract if isinstance(explicit_evidence_contract, dict) else {}
        acceptance_checks = [str(x).strip() for x in (explicit_evidence_contract.get('acceptance_checks') or default_acceptance_checks) if str(x).strip()]
        evidence_required = [str(x).strip() for x in (explicit_evidence_contract.get('evidence_required') or default_evidence_required) if str(x).strip()]
        planner_field_ownership = _planner_field_ownership(
            planner_input_source=planner_input_source,
            field_ownership_flags=field_ownership_flags,
            explicit_evidence_contract=explicit_evidence_contract,
        )
        base_success_semantics = _success_semantics_for_family(fam)
        success_semantics = {
            'success_model': str(explicit_success_model or explicit_evidence_contract.get('success_model') or base_success_semantics.get('success_model') or ''),
            'expected_signal_type': str(explicit_evidence_contract.get('expected_signal_type') or base_success_semantics.get('expected_signal_type') or ''),
            'evidence_goal_type': str(explicit_evidence_contract.get('evidence_goal_type') or base_success_semantics.get('evidence_goal_type') or ''),
        }
        rationale = {
            'preferred_vector_families': preferred_vector_families[:6],
            'recommended_task_families': recommended_task_families[:8],
            'deprioritized_task_families': deprioritized_task_families[:8],
            'ambiguity_flags': ambiguity_flags[:4],
            'interpretation_conflicts': interpretation_conflicts[:4],
            'planner_confidence': planner_hints.get('llm_confidence'),
            'target_profile_summary': _profile_summary(profile),
            'aggression_profile_hint': {
                'recommended_default': aggression_profile.get('recommended_default'),
                'recommended_min': aggression_profile.get('recommended_min'),
                'recommended_max': aggression_profile.get('recommended_max'),
            },
            'recommended_progression': ['recon', 'validation', 'deeper_family'],
            'evidence_goals': evidence_required[:],
            'planner_constraints': dict(planner_constraints or {}),
            'planner_preferences': dict(planner_preferences or {}),
            'capability_candidates': list(capability_candidates or []),
            'recommended_action_types': list(recommended_action_types or []),
            'hypothesis_candidates': list(hypothesis_candidates or []),
            'open_questions': list(open_questions or []),
            'experiment_intent_id': experiment_intent_id,
            'planner_input_source': planner_input_source,
            'field_ownership': planner_field_ownership,
        }
        runtime_task_seed = dict(explicit_runtime_task_contract or {})
        profile_priority = str(profile.get('priority_tier') or 'medium').strip().lower() or 'medium'
        profile_depth = str(profile.get('expected_depth') or 'medium').strip().lower() or 'medium'
        profile_role = str(profile.get('surface_role') or 'primary').strip().lower() or 'primary'
        profile_cluster = str(profile.get('target_cluster') or 'general').strip().lower() or 'general'
        runtime_task_seed.update({
            "objective": objective,
            "target": target,
            "task_family": fam,
            "task_success_criteria": success_criteria,
            "campaign_success_criteria": "Complete all low-risk vectors before medium/high-effort vectors.",
            "acceptance_checks": acceptance_checks,
            "evidence_required": evidence_required,
            "success_semantics": success_semantics,
            "planner_input_source": planner_input_source,
            "planner_field_ownership": planner_field_ownership,
            "capability_candidates": list(capability_candidates or runtime_task_seed.get('capability_candidates') or []),
            "recommended_action_types": list(recommended_action_types or runtime_task_seed.get('recommended_action_types') or []),
            "hypothesis_candidates": list(hypothesis_candidates or runtime_task_seed.get('hypothesis_candidates') or []),
            "experiment_intent_id": experiment_intent_id,
            "planner_constraints": dict(planner_constraints or runtime_task_seed.get('planner_constraints') or {}),
            "planner_preferences": dict(planner_preferences or runtime_task_seed.get('planner_preferences') or {}),
            "planner_rationale": {
                'preferred_vector_families': preferred_vector_families[:6],
                'recommended_task_families': recommended_task_families[:8],
                'deprioritized_task_families': deprioritized_task_families[:8],
            },
            "priority_score": runtime_task_seed.get('priority_score', 1.25 if profile_priority == 'high' else 0.8 if profile_priority == 'low' else 1.0),
            "cost_band": runtime_task_seed.get('cost_band', "medium" if fam in {"authz", "auth_flow", "logic", "client_input", "input_tamper", "redirect_trust", "workflow", "state_transition"} else "low"),
            "priority_tier": runtime_task_seed.get('priority_tier', profile_priority),
            "expected_depth": runtime_task_seed.get('expected_depth', profile_depth),
            "activation_phase": runtime_task_seed.get('activation_phase', 1),
            "activation_mode": runtime_task_seed.get('activation_mode', 'immediate'),
            "conditional_gate": runtime_task_seed.get('conditional_gate', ''),
            "surface_role": runtime_task_seed.get('surface_role', profile_role),
            "target_cluster": runtime_task_seed.get('target_cluster', profile_cluster),
            "recommended_tools": list(runtime_task_seed.get('recommended_tools') or []),
        })
        runtime_task = normalize_runtime_task_v2(runtime_task_seed)
        planning_ladder = dict(explicit_planning_ladder or {}) if isinstance(explicit_planning_ladder, dict) and explicit_planning_ladder else build_planning_ladder(
            runtime_task_contract=runtime_task,
            success_model=str(success_semantics.get('success_model') or ''),
            task_family=fam,
            recommended_action_types=list(recommended_action_types or runtime_task.get('recommended_action_types') or []),
        )
        target_type = str((profile or {}).get('target_type') or (profile or {}).get('type') or 'host')
        surface_keywords = [str(x).strip().lower() for x in ((planner_preferences or {}).get('surface_keywords') or []) if str(x).strip()]
        target_surface_rationale: list[str] = []
        if target_type in {'api', 'auth', 'integration'}:
            target_surface_rationale.append('authenticated_or_boundary_mapping')
        elif target_type == 'web':
            target_surface_rationale.append('browser_flow_mapping')
        elif target_type in {'static', 'support'}:
            target_surface_rationale.append('artifact_capture')
        target_surface_rationale.extend([x for x in surface_keywords if x in {'admin', 'billing', 'tenant', 'organization', 'api', 'auth', 'account'}])
        rationale['planning_ladder'] = dict(planning_ladder)
        rationale['recommended_progression'] = recommended_progression_from_planning_ladder(
            planning_ladder=planning_ladder,
            target_type=target_type,
            preferred_vector_families=preferred_vector_families,
        )
        rationale['target_surface_rationale'] = list(dict.fromkeys(target_surface_rationale))[:6]
        runtime_task['planning_ladder'] = dict(planning_ladder)
        runtime_task['planner_rationale'] = dict(runtime_task.get('planner_rationale') or {})
        runtime_task['planner_rationale'].update(dict(rationale))
        runtime_task['planner_rationale']['planning_ladder'] = dict(planning_ladder)
        runtime_task['planner_rationale']['recommended_progression'] = list(rationale['recommended_progression'])
        semantic_lineage = build_semantic_lineage(
            task={
                'target': target,
                'objective': objective,
                'task_family': fam,
                'planner_input_source': planner_input_source,
                'planner_field_ownership': planner_field_ownership,
                'planner_rationale': rationale,
                'planning_ladder': planning_ladder,
                'experiment_intent_id': experiment_intent_id,
            },
            runtime_task=runtime_task,
            source='runtime_plan_entry',
        )
        runtime_task['semantic_lineage'] = semantic_lineage
        return {
            "name": objective,
            "objective": objective,
            "target": target,
            "task_family": fam,
            "task_success_criteria": success_criteria,
            "campaign_success_criteria": "Complete all low-risk vectors before medium/high-effort vectors.",
            "planner_input_source": planner_input_source,
            "planner_field_ownership": planner_field_ownership,
            "acceptance_checks": runtime_task.get('acceptance_checks') or acceptance_checks,
            "evidence_required": runtime_task.get('evidence_required') or evidence_required,
            "success_semantics": runtime_task.get('success_semantics') or success_semantics,
            "priority_tier": runtime_task.get('priority_tier', profile_priority),
            "expected_depth": runtime_task.get('expected_depth', profile_depth),
            "activation_phase": runtime_task.get('activation_phase', 1),
            "activation_mode": runtime_task.get('activation_mode', 'immediate'),
            "conditional_gate": runtime_task.get('conditional_gate', ''),
            "surface_role": runtime_task.get('surface_role', profile_role),
            "target_cluster": runtime_task.get('target_cluster', profile_cluster),
            "target_score": 1.2 if runtime_task.get('priority_tier', profile_priority) == 'high' else 0.8 if runtime_task.get('priority_tier', profile_priority) == 'low' else 1.0,
            "scope_asset_kind": str((planner_preferences or {}).get('scope_asset_kind') or ''),
            "scope_path_prefix": str((planner_preferences or {}).get('scope_path_prefix') or ''),
            "scope_source": str((planner_preferences or {}).get('scope_source') or ''),
            "planner_rationale": rationale,
            "planning_ladder": planning_ladder,
            "semantic_lineage": semantic_lineage,
            "runtime_task": runtime_task,
        }

    def _normalize_experiment_intent(raw: object) -> dict | None:
        if not isinstance(raw, dict):
            return None
        target = str(raw.get('target') or '').strip()
        host = str(raw.get('target_host') or '').strip().lower()
        if not host and target.startswith(('http://', 'https://')):
            try:
                host = str(urlparse(target).hostname or '').strip().lower()
            except Exception:
                host = ''
        if not host or not _target_matches_authoritative_scope(target, host):
            return None
        fam = str(raw.get('task_family') or '').strip().lower()
        objective = str(raw.get('objective') or '').strip() or next(iter(family_objectives.get(fam, ['Passive recon and endpoint discovery'])), 'Passive recon and endpoint discovery')
        intent_id = str(raw.get('intent_id') or '').strip()
        prefs = raw.get('planner_preferences') if isinstance(raw.get('planner_preferences'), dict) else {}
        constraints = raw.get('planner_constraints') if isinstance(raw.get('planner_constraints'), dict) else {}
        profile = target_profiles.get(host) if isinstance(target_profiles.get(host), dict) else {}
        if not isinstance(profile, dict):
            profile = {}
        if 'target_type' not in profile and raw.get('target_type'):
            profile = dict(profile)
            profile['target_type'] = raw.get('target_type')
        dedupe_key = ('intent_id', intent_id) if intent_id else ('compat', host, fam, objective)
        return {
            'host': host,
            'target': target,
            'fam': fam,
            'objective': objective,
            'intent_id': intent_id,
            'field_ownership_flags': {
                'target': bool(target),
                'task_family': bool(str(raw.get('task_family') or '').strip()),
                'objective': bool(str(raw.get('objective') or '').strip()),
                'capability_candidates': 'capability_candidates' in raw,
                'recommended_action_types': 'recommended_action_types' in raw,
                'hypothesis_candidates': 'hypothesis_candidates' in raw,
                'experiment_intent_id': bool(intent_id),
                'planner_constraints': 'planner_constraints' in raw and isinstance(raw.get('planner_constraints'), dict),
                'planner_preferences': 'planner_preferences' in raw and isinstance(raw.get('planner_preferences'), dict),
                'success_model': bool(str(raw.get('success_model') or '').strip()),
                'runtime_task_contract': isinstance(raw.get('runtime_task_contract'), dict),
                'planning_ladder': isinstance(raw.get('planning_ladder'), dict),
                'action_type': bool(str(raw.get('action_type') or '').strip()),
                'capability': bool(str(raw.get('capability') or '').strip()),
                'experiment_shape': bool(str(raw.get('experiment_shape') or '').strip()),
                'evidence_goal': bool(str(raw.get('evidence_goal') or '').strip()),
                'exploit_ladder': isinstance(raw.get('exploit_ladder'), dict),
                'actor_requirements': isinstance(raw.get('actor_requirements'), dict),
                'session_requirements': isinstance(raw.get('session_requirements'), dict),
                'promotion_policy': isinstance(raw.get('promotion_policy'), dict),
                'contamination_policy': isinstance(raw.get('contamination_policy'), dict),
                'approval_sensitivity': isinstance(raw.get('approval_sensitivity'), dict),
            },
            'prefs': prefs,
            'constraints': constraints,
            'profile': profile,
            'ambiguity_flags': _sanitize_text_list_for_host(raw.get('ambiguity_flags') or [], host),
            'open_questions': _sanitize_text_list_for_host(raw.get('open_questions') or [], host),
            'capability_candidates': [str(x).strip().lower() for x in (raw.get('capability_candidates') or []) if str(x).strip()],
            'recommended_action_types': [str(x).strip().lower() for x in (raw.get('recommended_action_types') or []) if str(x).strip()],
            'hypothesis_candidates': [str(x).strip().lower() for x in _sanitize_text_list_for_host(raw.get('hypothesis_candidates') or [], host) if str(x).strip()],
            'success_model': str(raw.get('success_model') or ''),
            'evidence_contract': raw.get('evidence_contract') if isinstance(raw.get('evidence_contract'), dict) else {},
            'runtime_task_contract': raw.get('runtime_task_contract') if isinstance(raw.get('runtime_task_contract'), dict) else {},
            'planning_ladder': raw.get('planning_ladder') if isinstance(raw.get('planning_ladder'), dict) else {},
            'dedupe_key': dedupe_key,
        }

    def _entries_from_experiment_intents() -> List[Dict[str, object]]:
        entries: List[Dict[str, object]] = []
        seen = set()
        for raw in experiment_intents:
            normalized = _normalize_experiment_intent(raw)
            if not isinstance(normalized, dict):
                continue
            key = normalized.get('dedupe_key')
            if key in seen:
                continue
            seen.add(key)
            prefs = normalized.get('prefs') if isinstance(normalized.get('prefs'), dict) else {}
            entries.append(_build_entry(
                host=str(normalized.get('host') or ''),
                fam=str(normalized.get('fam') or ''),
                objective=str(normalized.get('objective') or ''),
                profile=normalized.get('profile') if isinstance(normalized.get('profile'), dict) else {},
                preferred_vector_families=[str(x).strip().lower() for x in (prefs.get('preferred_vector_families') or []) if str(x).strip()],
                recommended_task_families=[str(x).strip().lower() for x in (prefs.get('recommended_task_families') or []) if str(x).strip()],
                deprioritized_task_families=[str(x).strip().lower() for x in (prefs.get('deprioritized_task_families') or []) if str(x).strip()],
                ambiguity_flags=list(normalized.get('ambiguity_flags') or []),
                interpretation_conflicts=list(normalized.get('open_questions') or []),
                capability_candidates=list(normalized.get('capability_candidates') or []),
                recommended_action_types=list(normalized.get('recommended_action_types') or []),
                hypothesis_candidates=list(normalized.get('hypothesis_candidates') or []),
                planner_constraints=normalized.get('constraints') if isinstance(normalized.get('constraints'), dict) else {},
                planner_preferences=prefs,
                experiment_intent_id=str(normalized.get('intent_id') or ''),
                open_questions=list(normalized.get('open_questions') or []),
                explicit_target=str(normalized.get('target') or ''),
                explicit_success_model=str(normalized.get('success_model') or ''),
                explicit_evidence_contract=normalized.get('evidence_contract') if isinstance(normalized.get('evidence_contract'), dict) else {},
                explicit_runtime_task_contract=normalized.get('runtime_task_contract') if isinstance(normalized.get('runtime_task_contract'), dict) else {},
                explicit_planning_ladder=normalized.get('planning_ladder') if isinstance(normalized.get('planning_ladder'), dict) else {},
                planner_input_source='experiment_intent_canonical',
                field_ownership_flags=normalized.get('field_ownership_flags') if isinstance(normalized.get('field_ownership_flags'), dict) else {},
            ))
        entries.sort(key=lambda e: (
            {'high': 0, 'medium': 1, 'low': 2}.get(str(e.get('priority_tier') or 'medium').lower(), 1),
            int(e.get('activation_phase') or 1),
            {'primary': 0, 'supporting': 1, 'background': 2}.get(str(e.get('surface_role') or 'primary').lower(), 1),
            str(e.get('target') or ''),
            str(e.get('task_family') or ''),
        ))
        return entries

    def _entries_from_legacy_seed_synthesis(*, planner_input_source: str = 'legacy_seed_synthesis') -> List[Dict[str, object]]:
        entries: List[Dict[str, object]] = []
        seen = set()
        per_target_vectors = planner_hints.get('per_target_vectors', {}) if isinstance(planner_hints.get('per_target_vectors'), dict) else {}
        recommended_task_families = [str(x).strip().lower() for x in (planner_hints.get('recommended_task_families') or directive_preferences.get('recommended_task_families') or []) if str(x).strip()]
        deprioritized_task_families = [str(x).strip().lower() for x in (planner_hints.get('deprioritized_task_families') or directive_preferences.get('deprioritized_task_families') or []) if str(x).strip()]
        for host in sorted(set(domains)):
            ambiguity_flags = _sanitize_text_list_for_host((planner_hints.get('ambiguities') or directive_unknowns.get('ambiguities') or []), host)
            interpretation_conflicts = _sanitize_text_list_for_host((planner_hints.get('interpretation_conflicts') or directive_unknowns.get('interpretation_conflicts') or []), host)
            if not _in_scope(host):
                continue
            for fam, objective in _objectives_for_host(host):
                key = (host, fam, objective)
                if key in seen:
                    continue
                seen.add(key)
                profile = target_profiles.get(host) if isinstance(target_profiles.get(host), dict) else {}
                if isinstance(profile, dict):
                    profile = dict(profile)
                    profile['notes'] = _sanitize_text_list_for_host((profile.get('notes') or []), host)
                entries.append(_build_entry(
                    host=host,
                    fam=fam,
                    objective=objective,
                    profile=profile if isinstance(profile, dict) else {},
                    preferred_vector_families=[str(x).strip().lower() for x in (per_target_vectors.get(host) or []) if str(x).strip()],
                    recommended_task_families=recommended_task_families,
                    deprioritized_task_families=deprioritized_task_families,
                    ambiguity_flags=ambiguity_flags,
                    interpretation_conflicts=interpretation_conflicts,
                    planner_input_source=planner_input_source,
                ))
        entries.sort(key=lambda e: (
            {'high': 0, 'medium': 1, 'low': 2}.get(str(e.get('priority_tier') or 'medium').lower(), 1),
            int(e.get('activation_phase') or 1),
            {'primary': 0, 'supporting': 1, 'background': 2}.get(str(e.get('surface_role') or 'primary').lower(), 1),
            str(e.get('target') or ''),
            str(e.get('task_family') or ''),
        ))
        return entries

    if experiment_intents:
        entries = _entries_from_experiment_intents()
        if entries:
            return entries
        if authoritative_assets_raw:
            return []
        return _entries_from_legacy_seed_synthesis(planner_input_source='legacy_seed_synthesis_after_empty_experiment_intents')

    return _entries_from_legacy_seed_synthesis()


def load_runtime_plan_meta() -> dict:
    try:
        if RUNTIME_PLAN_META_PATH.exists():
            data = json.loads(RUNTIME_PLAN_META_PATH.read_text(encoding='utf-8'))
            return data if isinstance(data, dict) else {}
    except Exception:
        pass
    return {}


def _entry_key(e: dict) -> str:
    return f"{str(e.get('target') or '')}|{str(e.get('objective') or '')}|{str(e.get('task_family') or '')}"


def _planner_input_source_summary(entries: list[dict]) -> tuple[list[str], dict[str, int]]:
    counts: dict[str, int] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        source = str(entry.get('planner_input_source') or '').strip() or 'unknown'
        counts[source] = int(counts.get(source, 0) or 0) + 1
    return sorted(counts.keys()), counts


def write_runtime_plan(entries: list[dict], campaign_key: str, reason: str = 'manual_or_ui') -> dict:
    if not isinstance(entries, list) or not entries:
        return {'ok': False, 'error': 'runtime_plan_empty_after_scope_filters'}
    prev_meta = load_runtime_plan_meta()
    prev_entries: list[dict] = []
    runtime_plan_read_path = first_existing(RUNTIME_PLAN_PATH, LEGACY_RUNTIME_PLAN_PATH)
    try:
        if runtime_plan_read_path.exists():
            prev_entries = json.loads(runtime_plan_read_path.read_text(encoding='utf-8'))
            if not isinstance(prev_entries, list):
                prev_entries = []
    except Exception:
        prev_entries = []
    payload = json.dumps(entries, ensure_ascii=False, indent=2)
    for path in (RUNTIME_PLAN_PATH, LEGACY_RUNTIME_PLAN_PATH):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding='utf-8')
    uniq_targets = set()
    for e in entries:
        try:
            from urllib.parse import urlparse
            target = str(e.get('target') or '').strip()
            if target:
                parsed = urlparse(target)
                host = (parsed.hostname or '').strip().lower()
                if host and target.startswith(('http://', 'https://')):
                    uniq_targets.add(f'{parsed.scheme.lower()}://{host}{parsed.path or "/"}')
                elif host:
                    uniq_targets.add(host)
                else:
                    uniq_targets.add(target.lower())
        except Exception:
            pass
    plan_hash = hashlib.sha256(json.dumps(entries, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()
    prev_hash = str(prev_meta.get('plan_hash') or '')
    prev_rev = int(prev_meta.get('plan_revision', 0) or 0)
    plan_revision = prev_rev + 1 if plan_hash != prev_hash else prev_rev
    old_map = {_entry_key(e): e for e in prev_entries if isinstance(e, dict)}
    new_map = {_entry_key(e): e for e in entries if isinstance(e, dict)}
    old_keys = set(old_map.keys())
    new_keys = set(new_map.keys())
    added_keys = sorted(new_keys - old_keys)
    deprecated_keys = sorted(old_keys - new_keys)
    change_count = len(added_keys) + len(deprecated_keys)
    baseline = max(1, len(old_keys), len(new_keys))
    material_change = (change_count / baseline) >= 0.08 or change_count >= 5 or not prev_hash
    skipped = False
    if not material_change and prev_meta:
        plan_revision = prev_rev
        skipped = True
    diff_reason = 'material reprioritization'
    if 'promising' in reason:
        diff_reason = 'added because promising host/family signal'
    elif 'degraded' in reason:
        diff_reason = 'deprecated because degraded/noisy host state'
    elif 'periodic' in reason:
        diff_reason = 'periodic campaign refresh'
    planner_input_sources, planner_input_source_counts = _planner_input_source_summary(entries)
    meta_obj = {
        'campaign_key': campaign_key,
        'generated': len(entries),
        'prepared_attacks': len(entries),
        'target_count': len(uniq_targets),
        'input_total': len(uniq_targets),
        'planner_input_sources': planner_input_sources,
        'planner_input_source_counts': planner_input_source_counts,
        'generated_at': utc_now_iso(),
        'plan_revision': plan_revision,
        'plan_hash': plan_hash,
        'regeneration_reason': reason,
        'diff_reason': diff_reason,
        'added_tasks': max(0, len(added_keys)),
        'deprecated_tasks': max(0, len(deprecated_keys)),
        'changed': bool(plan_hash != prev_hash),
        'material_change': bool(material_change),
        'skipped': skipped,
        'added_examples': [
            {'target': str((new_map.get(k) or {}).get('target') or ''), 'objective': str((new_map.get(k) or {}).get('objective') or ''), 'task_family': str((new_map.get(k) or {}).get('task_family') or '')}
            for k in added_keys[:8]
        ],
        'deprecated_examples': [
            {'target': str((old_map.get(k) or {}).get('target') or ''), 'objective': str((old_map.get(k) or {}).get('objective') or ''), 'task_family': str((old_map.get(k) or {}).get('task_family') or '')}
            for k in deprecated_keys[:8]
        ],
    }
    atomic_write_json(RUNTIME_PLAN_META_PATH, normalize_runtime_plan_meta(meta_obj), ensure_ascii=False, indent=2)
    return {'ok': True, **meta_obj}


def regenerate_runtime_plan(campaign_key: str, reason: str = 'manual_or_ui') -> dict:
    version_dir, bp_path, bp = load_campaign_blueprint_for_key(campaign_key)
    if not bp_path or not isinstance(bp, dict):
        return {'ok': False, 'error': 'blueprint_missing'}
    entries = runtime_plan_entries_from_blueprint(bp)
    return write_runtime_plan(entries, campaign_key, reason=reason)
