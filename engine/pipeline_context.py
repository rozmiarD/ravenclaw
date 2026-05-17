from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List

from campaign_utils import extract_host_from_url  # type: ignore
from feature_flags import PIPELINE_FLAG_DEFAULTS, normalize_pipeline_flags  # type: ignore
from govengine.capability_recipes import resolve_contextual_planner_profiles
from paths import CONTEXT_SUMMARY_PATH, LEGACY_CONTEXT_SUMMARY_PATH, ep, first_existing  # type: ignore
from policy_core import get_runtime_brain_allowed_tools  # type: ignore
from runtime_campaign_state import credentials_runtime_policy, resolve_campaign_key  # type: ignore
from runtime_plan_service import load_active_campaign_blueprint  # type: ignore

PIPELINE_CONFIG_PATH = str(ep('pipeline_config.json'))
HOST_TOKEN_RE = re.compile(r"(https?://[^\s\"'<>]+)|\b((?:[a-z0-9-]+\.)+[a-z]{2,})\b", re.IGNORECASE)


def _extract_hosts_from_text(text: Any) -> list[str]:
    raw = str(text or '').strip()
    if not raw:
        return []
    hosts: list[str] = []
    seen: set[str] = set()
    direct = str(extract_host_from_url(raw) or '').strip().lower()
    if direct:
        seen.add(direct)
        hosts.append(direct)
    for match in HOST_TOKEN_RE.finditer(raw):
        token = str(match.group(1) or match.group(2) or '').strip().lower()
        host = str(extract_host_from_url(token) or token).strip().lower()
        if host and host not in seen:
            seen.add(host)
            hosts.append(host)
    return hosts


def _string_is_target_bound(text: Any, target_host: str) -> bool:
    host = str(target_host or '').strip().lower()
    if not host:
        return True
    mentioned = _extract_hosts_from_text(text)
    if not mentioned:
        return True
    return all(item == host for item in mentioned)


def _sanitize_text_list_for_target(items: Any, target_host: str, limit: int | None = None) -> list[str]:
    values = [str(x).strip() for x in (items or []) if str(x).strip()]
    cleaned = [value for value in values if _string_is_target_bound(value, target_host)]
    if limit is not None and limit >= 0:
        return cleaned[:limit]
    return cleaned


def filter_recent_context_for_target(entries: List[Dict[str, Any]], target: str = '', limit: int = 0) -> List[Dict[str, Any]]:
    host = str(extract_host_from_url(target) or '').strip().lower() if target else ''
    recent = [e for e in (entries or []) if isinstance(e, dict)]
    if host:
        same_host = [e for e in recent if str(extract_host_from_url(str(e.get('target') or '')) or '').strip().lower() == host]
        if same_host:
            recent = same_host
    if limit > 0:
        return recent[-limit:]
    return recent


def sanitize_planner_hints_for_target(planner_hints: Dict[str, Any], target: str = '') -> Dict[str, Any]:
    hints = dict(planner_hints or {}) if isinstance(planner_hints, dict) else {}
    host = str(extract_host_from_url(target) or '').strip().lower() if target else ''
    target_profile = dict(hints.get('target_profile') or {}) if isinstance(hints.get('target_profile'), dict) else {}
    if target_profile:
        target_profile['notes'] = _sanitize_text_list_for_target(target_profile.get('notes') or [], host, limit=4)
    hints['target_profile'] = target_profile
    hints['candidate_targets'] = [str(x).strip() for x in (hints.get('candidate_targets') or []) if str(x).strip() and (not host or str(extract_host_from_url(str(x)) or '').strip().lower() == host)][:6]
    hints['ambiguities'] = _sanitize_text_list_for_target(hints.get('ambiguities') or [], host, limit=len(list(hints.get('ambiguities') or [])))
    hints['interpretation_conflicts'] = _sanitize_text_list_for_target(hints.get('interpretation_conflicts') or [], host, limit=len(list(hints.get('interpretation_conflicts') or [])))
    return hints


def sanitize_intent_runtime_context_for_target(intent_context: Dict[str, Any], target: str = '') -> Dict[str, Any]:
    ctx = dict(intent_context or {}) if isinstance(intent_context, dict) else {}
    host = str(extract_host_from_url(target) or '').strip().lower() if target else ''
    ctx['open_questions'] = _sanitize_text_list_for_target(ctx.get('open_questions') or [], host)
    ctx['hypothesis_candidates'] = _sanitize_text_list_for_target(ctx.get('hypothesis_candidates') or [], host)
    ctx['ambiguities'] = _sanitize_text_list_for_target(ctx.get('ambiguities') or [], host)
    ctx['interpretation_conflicts'] = _sanitize_text_list_for_target(ctx.get('interpretation_conflicts') or [], host)
    ctx['target_surface_rationale'] = [str(x).strip().lower() for x in (ctx.get('target_surface_rationale') or []) if str(x).strip()]
    ctx['recommended_progression'] = [str(x).strip().lower() for x in (ctx.get('recommended_progression') or []) if str(x).strip()]
    ctx['target_profile'] = dict(ctx.get('target_profile') or {}) if isinstance(ctx.get('target_profile'), dict) else {}
    if isinstance(ctx['target_profile'], dict):
        ctx['target_profile']['notes'] = _sanitize_text_list_for_target((ctx['target_profile'] or {}).get('notes') or [], host, limit=4)
    planner_rationale = dict(ctx.get('planner_rationale') or {}) if isinstance(ctx.get('planner_rationale'), dict) else {}
    planner_rationale['target_surface_rationale'] = [str(x).strip().lower() for x in (planner_rationale.get('target_surface_rationale') or ctx.get('target_surface_rationale') or []) if str(x).strip()]
    planner_rationale['recommended_progression'] = [str(x).strip().lower() for x in (planner_rationale.get('recommended_progression') or ctx.get('recommended_progression') or []) if str(x).strip()]
    ctx['planner_rationale'] = planner_rationale
    ctx['planning_ladder'] = dict(ctx.get('planning_ladder') or {}) if isinstance(ctx.get('planning_ladder'), dict) else {}
    ctx['semantic_lineage'] = dict(ctx.get('semantic_lineage') or {}) if isinstance(ctx.get('semantic_lineage'), dict) else {}
    ctx['semantic_lineage_summary'] = dict(ctx.get('semantic_lineage_summary') or {}) if isinstance(ctx.get('semantic_lineage_summary'), dict) else {}
    constraints = dict(ctx.get('planner_constraints') or {}) if isinstance(ctx.get('planner_constraints'), dict) else {}
    if host:
        constraints['target_host_binding'] = host
    ctx['planner_constraints'] = constraints
    return ctx


def _coerce_json_list(raw: Any) -> list[str]:
    if isinstance(raw, list):
        return [str(x).strip() for x in raw if str(x).strip()]
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return []
        try:
            data = json.loads(text)
            if isinstance(data, list):
                return [str(x).strip() for x in data if str(x).strip()]
        except Exception:
            return [part.strip() for part in text.split(',') if part.strip()]
    return []



def _coerce_json_dict(raw: Any) -> dict:
    if isinstance(raw, dict):
        return dict(raw)
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return {}
        try:
            data = json.loads(text)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}
    return {}



def contextual_brain_tooling(task_family: str = '', resolved_profiles: list[str] | None = None) -> dict:
    profiles = list(resolved_profiles or [])
    if not profiles and str(task_family or '').strip():
        profiles = list(resolve_contextual_planner_profiles(task_family).get('profiles') or [])
    tools = list(get_runtime_brain_allowed_tools(profiles or None))
    return {
        'profiles': profiles,
        'tools': tools,
    }



def load_pipeline_config() -> Dict[str, Any]:
    default = dict(PIPELINE_FLAG_DEFAULTS)
    try:
        with open(PIPELINE_CONFIG_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict):
                default.update(data)
    except Exception:
        pass
    return normalize_pipeline_flags(default)



def save_pipeline_config(cfg: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(PIPELINE_CONFIG_PATH), exist_ok=True)
    normalized = normalize_pipeline_flags(cfg)
    with open(PIPELINE_CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(normalized, f, ensure_ascii=False, indent=2)



def _context_read_path() -> Path:
    return first_existing(CONTEXT_SUMMARY_PATH, LEGACY_CONTEXT_SUMMARY_PATH)



def _write_context_payload(payload: str) -> None:
    for path in (CONTEXT_SUMMARY_PATH, LEGACY_CONTEXT_SUMMARY_PATH):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding='utf-8')



def _ensure_context_file() -> None:
    context_path = _context_read_path()
    if context_path.exists():
        if context_path != CONTEXT_SUMMARY_PATH:
            try:
                _write_context_payload(context_path.read_text(encoding='utf-8'))
            except Exception:
                pass
        return
    _write_context_payload('[]')



def load_context_history(limit: int) -> List[Dict[str, Any]]:
    _ensure_context_file()
    try:
        data = json.loads(_context_read_path().read_text(encoding='utf-8'))
        if isinstance(data, list):
            return data[-limit:] if limit > 0 else data
    except Exception:
        pass
    return []



def compact_recent_context(entries: List[Dict[str, Any]], limit: int = 3, target: str = '') -> List[Dict[str, Any]]:
    compact: List[Dict[str, Any]] = []
    selected = filter_recent_context_for_target(entries, target=target, limit=max(1, int(limit)))
    for e in selected:
        if not isinstance(e, dict):
            continue
        compact.append({
            'timestamp': str(e.get('timestamp') or ''),
            'objective': str(e.get('objective') or '')[:140],
            'target': str(e.get('target') or '')[:180],
            'status': str(e.get('status') or ''),
            'returncode': e.get('returncode'),
            'auditor_decision': str(e.get('auditor_decision') or ''),
            'reason_code': str(e.get('reason_code') or ''),
            'task_family': str(e.get('task_family') or ''),
            'next_family_hint': str(e.get('analysis', {}).get('next_family_hint') or '') if isinstance(e.get('analysis'), dict) else '',
            'success_eval': str(e.get('analysis', {}).get('success_criteria_eval') or '') if isinstance(e.get('analysis'), dict) else '',
            'planner_alignment': str(e.get('brain', {}).get('planner_alignment') or '') if isinstance(e.get('brain'), dict) else '',
            'redundancy_risk': str(e.get('brain', {}).get('redundancy_risk') or '') if isinstance(e.get('brain'), dict) else '',
        })
    return compact



def summarize_recent_runtime_state(entries: List[Dict[str, Any]], target: str = '', task_family: str = '') -> Dict[str, Any]:
    host = extract_host_from_url(target) if target else ''
    recent = [e for e in (entries or []) if isinstance(e, dict)]
    same_host = [e for e in recent if host and extract_host_from_url(str(e.get('target') or '')) == host]
    same_family = [e for e in recent if str(e.get('task_family') or '').strip().lower() == str(task_family or '').strip().lower() and str(task_family or '').strip()]
    blocked = [e for e in recent if str(e.get('auditor_decision') or '').lower() in {'reject', 'deny', 'blocked', 'owner_approval_required'}]
    partial = [e for e in recent if str((e.get('analysis') or {}).get('success_criteria_eval') or '').lower() == 'partial']
    not_met = [e for e in recent if str((e.get('analysis') or {}).get('success_criteria_eval') or '').lower() == 'not_met']
    next_hints = []
    for e in recent[-6:]:
        if isinstance(e.get('analysis'), dict):
            hint = str(e.get('analysis', {}).get('next_family_hint') or '').strip().lower()
            if hint:
                next_hints.append(hint)
    return {
        'recent_total': len(recent[-8:]),
        'same_host_recent': len(same_host[-6:]),
        'same_family_recent': len(same_family[-6:]),
        'blocked_recent': len(blocked[-6:]),
        'partial_recent': len(partial[-6:]),
        'not_met_recent': len(not_met[-6:]),
        'recent_next_family_hints': next_hints[-4:],
        'last_reason_codes': [str(e.get('reason_code') or '') for e in recent[-4:]],
    }



def append_context_entry(entry: Dict[str, Any], limit: int) -> None:
    _ensure_context_file()
    try:
        data = json.loads(_context_read_path().read_text(encoding='utf-8'))
        if not isinstance(data, list):
            data = []
    except Exception:
        data = []
    data.append(entry)
    if limit > 0 and len(data) > limit:
        data = data[-limit:]
    _write_context_payload(json.dumps(data, ensure_ascii=False, indent=2))



def load_planner_hints(target: str = '', task_family: str = '', limit_vectors: int = 5, limit_ambiguities: int = 3, limit_conflicts: int = 3, selected_campaign_key: str = '') -> Dict[str, Any]:
    try:
        resolved_key = resolve_campaign_key(selected_campaign_key)
        _campaign_key, _version_dir, bp_path, bp = load_active_campaign_blueprint(resolved_key)
        if not bp_path or not isinstance(bp, dict):
            return {}
        hints = bp.get('planner_hints') if isinstance(bp, dict) else {}
        aggr = bp.get('aggression_profile') if isinstance(bp, dict) else {}
        target_profiles = bp.get('target_profiles') if isinstance(bp.get('target_profiles'), dict) else {}
        host = extract_host_from_url(target) if target else ''
        profile = target_profiles.get(host) if isinstance(target_profiles.get(host), dict) else {}
        per_target_vectors = (hints or {}).get('per_target_vectors', {}) if isinstance((hints or {}).get('per_target_vectors', {}), dict) else {}
        preferred_for_target = [str(x).strip().lower() for x in (per_target_vectors.get(host) or []) if str(x).strip()]
        candidate_vectors = [str(x).strip() for x in (profile.get('candidate_vectors') or []) if str(x).strip()] if isinstance(profile.get('candidate_vectors'), list) else []
        surface_keywords = [str(x).strip().lower() for x in (profile.get('surface_keywords') or []) if str(x).strip()] if isinstance(profile.get('surface_keywords'), list) else []
        raw = {
            'resolved_campaign_key': resolved_key,
            'suggested_attack_vectors': list((hints or {}).get('global_vectors', (hints or {}).get('suggested_attack_vectors', [])) or [])[:max(1, int(limit_vectors))],
            'recommended_task_families': list((hints or {}).get('recommended_task_families', []) or [])[:6],
            'deprioritized_task_families': list((hints or {}).get('deprioritized_task_families', []) or [])[:6],
            'per_target_vectors': per_target_vectors,
            'preferred_vectors_for_target': preferred_for_target[:6],
            'candidate_targets': list((hints or {}).get('candidate_targets', []) or [])[:6],
            'ambiguities': list((hints or {}).get('ambiguities', []) or [])[:max(0, int(limit_ambiguities))],
            'llm_used': bool((hints or {}).get('llm_used', False)),
            'llm_confidence': (hints or {}).get('llm_confidence'),
            'interpretation_conflicts': list((hints or {}).get('interpretation_conflicts', []) or [])[:max(0, int(limit_conflicts))],
            'target_profile': {
                'host': host,
                'target_type': str(profile.get('target_type') or profile.get('type') or ''),
                'surface_keywords': surface_keywords[:6],
                'task_family_seeds': [str(x).strip().lower() for x in (profile.get('task_family_seeds') or []) if str(x).strip()][:6],
                'candidate_vectors': candidate_vectors[:6],
                'notes': [str(x).strip() for x in (profile.get('notes') or []) if str(x).strip()][:4] if isinstance(profile.get('notes'), list) else [],
            },
            'aggression_profile': {
                'recommended_default': (aggr or {}).get('recommended_default'),
                'recommended_min': (aggr or {}).get('recommended_min'),
                'recommended_max': (aggr or {}).get('recommended_max'),
            },
            'task_family_context': {
                'requested_family': str(task_family or '').strip().lower(),
                'preferred_for_target_match': bool(str(task_family or '').strip().lower() and str(task_family or '').strip().lower() in preferred_for_target),
            },
        }
        return sanitize_planner_hints_for_target(raw, target=target)
    except Exception:
        return {}



def load_credentials_runtime_policy() -> Dict[str, Any]:
    try:
        return credentials_runtime_policy()
    except Exception:
        return {
            'credentials_required': False,
            'allow_auth_header': False,
            'allow_cookie_header': False,
            'allow_basic_auth': False,
            'credentials_owner_approved': False,
            'bug_bounty_username': '',
            'test_account_email': '',
            'request_decoration': {
                'mode': 'none',
                'headers': [],
                'cookies': [],
                'basic_auth': {'enabled': False, 'username': '', 'password': '', 'password_ref': ''},
                'provenance_notes': [],
            },
            'resolved_campaign_key': '',
        }



def _merge_intent_runtime_context(args: Any, planner_hints: Dict[str, Any], target: str = '') -> Dict[str, Any]:
    capability_candidates = _coerce_json_list(getattr(args, 'capability_candidates_json', ''))
    recommended_action_types = _coerce_json_list(getattr(args, 'recommended_action_types_json', ''))
    hypothesis_candidates = _coerce_json_list(getattr(args, 'hypothesis_candidates_json', ''))
    open_questions = _coerce_json_list(getattr(args, 'open_questions_json', ''))
    planner_constraints = _coerce_json_dict(getattr(args, 'planner_constraints_json', ''))
    planner_preferences = _coerce_json_dict(getattr(args, 'planner_preferences_json', ''))
    planner_rationale = _coerce_json_dict(getattr(args, 'planner_rationale_json', ''))
    planning_ladder = _coerce_json_dict(getattr(args, 'planning_ladder_json', ''))
    target_surface_rationale = _coerce_json_list(getattr(args, 'target_surface_rationale_json', ''))
    recommended_progression = _coerce_json_list(getattr(args, 'recommended_progression_json', ''))
    semantic_lineage = _coerce_json_dict(getattr(args, 'semantic_lineage_json', ''))
    semantic_lineage_summary = _coerce_json_dict(getattr(args, 'semantic_lineage_summary_json', ''))
    experiment_intent_id = str(getattr(args, 'experiment_intent_id', '') or '').strip()
    if not target_surface_rationale:
        target_surface_rationale = [str(x).strip().lower() for x in (planner_rationale.get('target_surface_rationale') or []) if str(x).strip()]
    if not recommended_progression:
        recommended_progression = [str(x).strip().lower() for x in (planner_rationale.get('recommended_progression') or []) if str(x).strip()]
    merged = {
        'experiment_intent_id': experiment_intent_id,
        'capability_candidates': capability_candidates,
        'recommended_action_types': recommended_action_types,
        'hypothesis_candidates': hypothesis_candidates,
        'open_questions': open_questions,
        'planner_constraints': planner_constraints,
        'planner_preferences': planner_preferences,
        'planner_rationale': planner_rationale,
        'planning_ladder': planning_ladder,
        'target_surface_rationale': target_surface_rationale,
        'recommended_progression': recommended_progression,
        'semantic_lineage': semantic_lineage,
        'semantic_lineage_summary': semantic_lineage_summary,
        'target_profile': dict(planner_hints.get('target_profile') or {}),
        'preferred_vectors_for_target': list(planner_hints.get('preferred_vectors_for_target') or []),
        'deprioritized_task_families': list(planner_hints.get('deprioritized_task_families') or []),
        'ambiguities': list(planner_hints.get('ambiguities') or []),
        'interpretation_conflicts': list(planner_hints.get('interpretation_conflicts') or []),
        'task_family_context': dict(planner_hints.get('task_family_context') or {}),
    }
    if not merged['hypothesis_candidates']:
        merged['hypothesis_candidates'] = [str(x).strip() for x in (planner_hints.get('preferred_vectors_for_target') or []) if str(x).strip()][:6]
    return sanitize_intent_runtime_context_for_target(merged, target=target)
