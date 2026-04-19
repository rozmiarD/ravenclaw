from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

from json_state_io import atomic_write_json, safe_load_json_object
from paths import REPORTS_DIR
from runtime_state_schemas import normalize_learning_store

LEARNING_PATH = REPORTS_DIR / "learning_store.json"


BASE_LEARNING_STORE = {
    "families": {},
    "hosts": {},
    "capabilities": {},
    "tools": {},
    "action_types": {},
    "host_stages": {},
    "planning_stages": {},
    "next_stages": {},
    "target_types": {},
    "target_surface_signals": {},
    "transitions": {},
    "host_transition_pairs": {},
    "progression_priors": {},
    "host_progression_priors": {},
    "archetype_priors": {},
    "host_archetype_priors": {},
    "branch_priors": {},
    "host_branch_priors": {},
    "updated_at": None,
}


def _load() -> Dict[str, Any]:
    data, _meta = safe_load_json_object(
        LEARNING_PATH,
        default=BASE_LEARNING_STORE,
        normalizer=normalize_learning_store,
        description='learning_store',
    )
    return data


def _save(data: Dict[str, Any]) -> None:
    LEARNING_PATH.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(LEARNING_PATH, data, ensure_ascii=False, indent=2)


def _new_counter_bucket() -> Dict[str, Any]:
    return {"seen": 0, "promising": 0, "success": 0}


def _bump_counter(bucket: Dict[str, Any], *, promising: bool, status: str) -> None:
    bucket["seen"] = int(bucket.get("seen", 0)) + 1
    if promising:
        bucket["promising"] = int(bucket.get("promising", 0)) + 1
    if status in {"success", "completed", "ok"}:
        bucket["success"] = int(bucket.get("success", 0)) + 1


def infer_archetypes(*, target_type: str = '', target_surface_rationale: list[str] | None = None, family: str = '', next_family: str = '', next_stage: str = '') -> list[str]:
    target_type_l = str(target_type or '').strip().lower()
    surface = [str(x or '').strip().lower() for x in (target_surface_rationale or []) if str(x or '').strip()]
    family_l = str(family or '').strip().lower()
    next_family_l = str(next_family or '').strip().lower()
    next_stage_l = str(next_stage or '').strip().lower()
    out: list[str] = []
    if target_type_l in {'auth', 'api'} or 'authenticated_or_boundary_mapping' in surface:
        out.append('auth_heavy')
    if target_type_l in {'api', 'integration'} or any(x in surface for x in {'api', 'tenant', 'organization', 'billing'}):
        out.append('api_first')
    if family_l in {'workflow', 'logic', 'state_transition', 'auth_flow'} or next_stage_l in {'state_transition_confirmation', 'bounded_exploit_proof'}:
        out.append('workflow_app')
    if any(x in surface for x in {'admin', 'billing', 'tenant', 'organization'}):
        out.append('admin_surface')
    if target_type_l in {'static', 'support'} or 'artifact_capture' in surface:
        out.append('static_edge')
    if target_type_l == 'integration' or next_family_l in {'authz', 'workflow'}:
        out.append('integration_surface')
    deduped: list[str] = []
    for item in out:
        if item not in deduped:
            deduped.append(item)
    return deduped[:3]



def update_learning(
    host: str,
    family: str,
    classification: str,
    promising: bool,
    status: str,
    *,
    capability: str = '',
    tool: str = '',
    action_type: str = '',
    host_stage: str = '',
    planning_stage: str = '',
    next_stage: str = '',
    target_type: str = '',
    target_surface_rationale: list[str] | None = None,
    next_action_type: str = '',
    next_family: str = '',
    reconsult_tier: str = '',
    archetypes: list[str] | None = None,
    branch_state: str = '',
    branch_action: str = '',
    branch_reason: str = '',
    branch_outcome: str = '',
    branch_lifecycle_status: str = '',
    branch_lifecycle_reason: str = '',
    branch_thread_key: str = '',
    branch_thread_label: str = '',
) -> None:
    data = _load()
    fams = data.setdefault("families", {})
    hosts = data.setdefault("hosts", {})
    capabilities = data.setdefault("capabilities", {})
    family_capabilities = data.setdefault("family_capabilities", {})
    host_capability_pairs = data.setdefault("host_capability_pairs", {})
    tools = data.setdefault("tools", {})
    action_types = data.setdefault("action_types", {})
    host_stages = data.setdefault("host_stages", {})
    planning_stages = data.setdefault("planning_stages", {})
    next_stages = data.setdefault("next_stages", {})
    target_types = data.setdefault("target_types", {})
    target_surface_signals = data.setdefault("target_surface_signals", {})
    transitions = data.setdefault("transitions", {})
    host_transition_pairs = data.setdefault("host_transition_pairs", {})
    progression_priors = data.setdefault("progression_priors", {})
    host_progression_priors = data.setdefault("host_progression_priors", {})
    archetype_priors = data.setdefault("archetype_priors", {})
    host_archetype_priors = data.setdefault("host_archetype_priors", {})
    branch_priors = data.setdefault("branch_priors", {})
    host_branch_priors = data.setdefault("host_branch_priors", {})

    f = fams.setdefault(family, _new_counter_bucket())
    _bump_counter(f, promising=promising, status=status)

    h = hosts.setdefault(host, {"seen": 0, "promising": 0, "top_families": {}, "top_capabilities": {}, "top_tools": {}, "top_action_types": {}, "top_host_stages": {}, "top_planning_stages": {}, "top_next_stages": {}, "top_target_types": {}, "top_target_surface_signals": {}, "classifications": {}})
    h["seen"] = int(h.get("seen", 0)) + 1
    if promising:
        h["promising"] = int(h.get("promising", 0)) + 1
    tf = h.setdefault("top_families", {})
    tf[family] = int(tf.get(family, 0)) + (2 if promising else 1)
    if capability:
        tc = h.setdefault("top_capabilities", {})
        tc[capability] = int(tc.get(capability, 0)) + (2 if promising else 1)
    if tool:
        tt = h.setdefault("top_tools", {})
        tt[tool] = int(tt.get(tool, 0)) + (2 if promising else 1)
    if action_type:
        ta = h.setdefault("top_action_types", {})
        ta[action_type] = int(ta.get(action_type, 0)) + 1
    if host_stage:
        th = h.setdefault("top_host_stages", {})
        th[host_stage] = int(th.get(host_stage, 0)) + 1
    if planning_stage:
        tp = h.setdefault("top_planning_stages", {})
        tp[planning_stage] = int(tp.get(planning_stage, 0)) + (2 if promising else 1)
    if next_stage:
        tn = h.setdefault("top_next_stages", {})
        tn[next_stage] = int(tn.get(next_stage, 0)) + (2 if promising else 1)
    if target_type:
        tt = h.setdefault("top_target_types", {})
        tt[target_type] = int(tt.get(target_type, 0)) + (2 if promising else 1)
    for signal in [str(x or '').strip().lower() for x in (target_surface_rationale or []) if str(x or '').strip()][:6]:
        ts = h.setdefault("top_target_surface_signals", {})
        ts[signal] = int(ts.get(signal, 0)) + (2 if promising else 1)
    classifications = h.setdefault("classifications", {})
    classifications[classification] = int(classifications.get(classification, 0)) + 1

    if capability:
        bucket = capabilities.setdefault(capability, _new_counter_bucket())
        _bump_counter(bucket, promising=promising, status=status)
        family_cap_key = f"{family}::{capability}"
        family_cap_bucket = family_capabilities.setdefault(family_cap_key, {**_new_counter_bucket(), 'family': family, 'capability': capability})
        _bump_counter(family_cap_bucket, promising=promising, status=status)
        host_cap_key = f"{host}::{capability}"
        host_cap_bucket = host_capability_pairs.setdefault(host_cap_key, {**_new_counter_bucket(), 'host': host, 'capability': capability})
        _bump_counter(host_cap_bucket, promising=promising, status=status)
    if tool:
        bucket = tools.setdefault(tool, _new_counter_bucket())
        _bump_counter(bucket, promising=promising, status=status)
    if action_type:
        bucket = action_types.setdefault(action_type, _new_counter_bucket())
        _bump_counter(bucket, promising=promising, status=status)
    if host_stage:
        bucket = host_stages.setdefault(host_stage, _new_counter_bucket())
        _bump_counter(bucket, promising=promising, status=status)
    if planning_stage:
        bucket = planning_stages.setdefault(planning_stage, _new_counter_bucket())
        _bump_counter(bucket, promising=promising, status=status)
    if next_stage:
        bucket = next_stages.setdefault(next_stage, _new_counter_bucket())
        _bump_counter(bucket, promising=promising, status=status)
    if target_type:
        bucket = target_types.setdefault(target_type, _new_counter_bucket())
        _bump_counter(bucket, promising=promising, status=status)
    for signal in [str(x or '').strip().lower() for x in (target_surface_rationale or []) if str(x or '').strip()][:6]:
        bucket = target_surface_signals.setdefault(signal, _new_counter_bucket())
        _bump_counter(bucket, promising=promising, status=status)

    target_surface_tokens = [str(x or '').strip().lower() for x in (target_surface_rationale or []) if str(x or '').strip()][:2]

    transition_parts = [
        str(family or '').strip().lower(),
        str(capability or '').strip().lower(),
        str(action_type or '').strip().lower(),
        str(next_stage or '').strip().lower(),
        str(next_action_type or '').strip().lower(),
    ]
    if any(transition_parts):
        transition_key = '::'.join(part or '-' for part in transition_parts)
        transition_bucket = transitions.setdefault(transition_key, {
            **_new_counter_bucket(),
            'family': transition_parts[0],
            'capability': transition_parts[1],
            'action_type': transition_parts[2],
            'next_stage': transition_parts[3],
            'next_action_type': transition_parts[4],
        })
        _bump_counter(transition_bucket, promising=promising, status=status)
        if host:
            host_transition_key = f"{host}::{transition_key}"
            host_transition_bucket = host_transition_pairs.setdefault(host_transition_key, {
                **_new_counter_bucket(),
                'host': host,
                'transition': transition_key,
            })
            _bump_counter(host_transition_bucket, promising=promising, status=status)

    progression_parts = [
        str(family or '').strip().lower(),
        str(target_type or '').strip().lower(),
        '|'.join(target_surface_tokens) or '-',
        str(next_stage or '').strip().lower(),
        str(next_family or '').strip().lower(),
        str(reconsult_tier or '').strip().lower(),
    ]
    if any(part and part != '-' for part in progression_parts):
        progression_key = '::'.join(part or '-' for part in progression_parts)
        progression_bucket = progression_priors.setdefault(progression_key, {
            **_new_counter_bucket(),
            'family': progression_parts[0],
            'target_type': progression_parts[1],
            'target_surface_signal': progression_parts[2],
            'next_stage': progression_parts[3],
            'next_family': progression_parts[4],
            'reconsult_tier': progression_parts[5],
        })
        _bump_counter(progression_bucket, promising=promising, status=status)
        if host:
            host_progression_key = f"{host}::{progression_key}"
            host_progression_bucket = host_progression_priors.setdefault(host_progression_key, {
                **_new_counter_bucket(),
                'host': host,
                'progression': progression_key,
            })
            _bump_counter(host_progression_bucket, promising=promising, status=status)

    inferred_archetypes = [str(x or '').strip().lower() for x in (archetypes or infer_archetypes(target_type=target_type, target_surface_rationale=target_surface_rationale, family=family, next_family=next_family, next_stage=next_stage)) if str(x or '').strip()][:3]
    for archetype in inferred_archetypes:
        archetype_key = f"{str(target_type or '').strip().lower() or '-'}::{archetype}"
        archetype_bucket = archetype_priors.setdefault(archetype_key, {
            **_new_counter_bucket(),
            'target_type': str(target_type or '').strip().lower(),
            'archetype': archetype,
        })
        _bump_counter(archetype_bucket, promising=promising, status=status)
        if host:
            host_archetype_key = f"{host}::{archetype_key}"
            host_archetype_bucket = host_archetype_priors.setdefault(host_archetype_key, {
                **_new_counter_bucket(),
                'host': host,
                'archetype': archetype,
                'target_type': str(target_type or '').strip().lower(),
            })
            _bump_counter(host_archetype_bucket, promising=promising, status=status)

    branch_state_l = str(branch_state or '').strip().lower()
    branch_action_l = str(branch_action or '').strip().lower()
    branch_reason_l = str(branch_reason or '').strip().lower()
    branch_outcome_l = str(branch_outcome or '').strip().lower()
    branch_lifecycle_status_l = str(branch_lifecycle_status or '').strip().lower()
    branch_lifecycle_reason_l = str(branch_lifecycle_reason or '').strip().lower()
    branch_thread_key_l = str(branch_thread_key or '').strip().lower()
    branch_thread_label_l = str(branch_thread_label or '').strip().lower()
    if not branch_lifecycle_status_l and branch_outcome_l:
        if branch_outcome_l in {'dead_end', 'sterile', 'abandoned'}:
            branch_lifecycle_status_l = 'dead_end'
        elif branch_outcome_l in {'productive', 'confirmed', 'proof'}:
            branch_lifecycle_status_l = 'productive'
        else:
            branch_lifecycle_status_l = branch_outcome_l
    if not branch_lifecycle_reason_l and branch_lifecycle_status_l:
        branch_lifecycle_reason_l = branch_reason_l or branch_lifecycle_status_l
    normalized_branch_outcome = branch_outcome_l or branch_lifecycle_status_l
    branch_parts = [
        branch_state_l,
        branch_action_l,
        branch_reason_l,
        str(next_stage or '').strip().lower(),
        normalized_branch_outcome,
    ]
    if any(branch_parts):
        branch_key = '::'.join(part or '-' for part in branch_parts)
        branch_bucket = branch_priors.setdefault(branch_key, {
            **_new_counter_bucket(),
            'branch_state': branch_parts[0],
            'branch_action': branch_parts[1],
            'branch_reason': branch_parts[2],
            'next_stage': branch_parts[3],
            'branch_outcome': branch_parts[4],
            'branch_lifecycle_status': branch_lifecycle_status_l,
            'branch_lifecycle_reason': branch_lifecycle_reason_l,
            'branch_thread_key': branch_thread_key_l,
            'branch_thread_label': branch_thread_label_l,
        })
        _bump_counter(branch_bucket, promising=promising, status=status)
        if normalized_branch_outcome in {'dead_end', 'sterile', 'abandoned'}:
            branch_bucket['dead_end'] = int(branch_bucket.get('dead_end', 0)) + 1
        elif normalized_branch_outcome in {'productive', 'confirmed', 'proof'}:
            branch_bucket['productive'] = int(branch_bucket.get('productive', 0)) + 1
        if host:
            host_branch_key = f"{host}::{branch_key}"
            host_branch_bucket = host_branch_priors.setdefault(host_branch_key, {
                **_new_counter_bucket(),
                'host': host,
                'branch': branch_key,
                'branch_state': branch_parts[0],
                'branch_action': branch_parts[1],
                'branch_reason': branch_parts[2],
                'next_stage': branch_parts[3],
                'branch_outcome': branch_parts[4],
                'branch_lifecycle_status': branch_lifecycle_status_l,
                'branch_lifecycle_reason': branch_lifecycle_reason_l,
                'branch_thread_key': branch_thread_key_l,
                'branch_thread_label': branch_thread_label_l,
            })
            _bump_counter(host_branch_bucket, promising=promising, status=status)
            if normalized_branch_outcome in {'dead_end', 'sterile', 'abandoned'}:
                host_branch_bucket['dead_end'] = int(host_branch_bucket.get('dead_end', 0)) + 1
            elif normalized_branch_outcome in {'productive', 'confirmed', 'proof'}:
                host_branch_bucket['productive'] = int(host_branch_bucket.get('productive', 0)) + 1

    from time_utils import utc_now_iso
    data["updated_at"] = utc_now_iso()
    _save(data)


def _top_scored_items(section: Dict[str, Any], *, key_name: str, limit: int) -> List[Dict[str, Any]]:
    scored: List[tuple[str, float]] = []
    for name, v in section.items():
        if not isinstance(v, dict):
            continue
        seen = max(1, int(v.get("seen", 0)))
        prom = int(v.get("promising", 0))
        suc = int(v.get("success", 0))
        score = (prom * 2 + suc) / seen
        scored.append((str(name), score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [{key_name: n, "score": round(s, 3)} for n, s in scored[:limit]]


def top_transition_action_hints(
    *,
    family: str = '',
    capability: str = '',
    action_type: str = '',
    next_stage: str = '',
    host: str = '',
    limit: int = 3,
) -> List[Dict[str, Any]]:
    data = _load()
    transitions = data.get('transitions', {}) if isinstance(data.get('transitions'), dict) else {}
    host_transition_pairs = data.get('host_transition_pairs', {}) if isinstance(data.get('host_transition_pairs'), dict) else {}

    fam = str(family or '').strip().lower()
    cap = str(capability or '').strip().lower()
    act = str(action_type or '').strip().lower()
    stage = str(next_stage or '').strip().lower()
    host_norm = str(host or '').strip().lower()

    scored: list[Tuple[str, float, Dict[str, Any]]] = []

    def _score_bucket(bucket: Dict[str, Any], *, host_boost: bool) -> float:
        seen = max(1, int(bucket.get('seen', 0)))
        prom = int(bucket.get('promising', 0))
        suc = int(bucket.get('success', 0))
        base = ((prom * 2) + suc) / seen
        if host_boost:
            base += 0.35
        return base

    def _matches(bucket: Dict[str, Any]) -> bool:
        if fam and str(bucket.get('family') or '').strip().lower() != fam:
            return False
        if cap and str(bucket.get('capability') or '').strip().lower() != cap:
            return False
        if act and str(bucket.get('action_type') or '').strip().lower() != act:
            return False
        if stage and str(bucket.get('next_stage') or '').strip().lower() != stage:
            return False
        next_action = str(bucket.get('next_action_type') or '').strip().lower()
        return bool(next_action)

    for key, bucket in transitions.items():
        if isinstance(bucket, dict) and _matches(bucket):
            scored.append((str(key), _score_bucket(bucket, host_boost=False), bucket))

    if host_norm:
        for key, bucket in host_transition_pairs.items():
            if not isinstance(bucket, dict):
                continue
            if str(bucket.get('host') or '').strip().lower() != host_norm:
                continue
            transition_key = str(bucket.get('transition') or key).strip()
            source = transitions.get(transition_key) if isinstance(transitions.get(transition_key), dict) else {}
            merged = dict(source) if isinstance(source, dict) else {}
            merged.update(bucket)
            if _matches(merged):
                scored.append((transition_key, _score_bucket(bucket, host_boost=True), merged))

    best: Dict[str, tuple[float, Dict[str, Any]]] = {}
    for transition_key, score, bucket in scored:
        next_action = str(bucket.get('next_action_type') or '').strip().lower()
        if not next_action:
            continue
        current = best.get(next_action)
        item = {
            'transition': transition_key,
            'next_action_type': next_action,
            'score': round(score, 3),
            'family': str(bucket.get('family') or '').strip().lower(),
            'capability': str(bucket.get('capability') or '').strip().lower(),
            'action_type': str(bucket.get('action_type') or '').strip().lower(),
            'next_stage': str(bucket.get('next_stage') or '').strip().lower(),
        }
        if current is None or score > current[0]:
            best[next_action] = (score, item)

    out = [item for _score, item in sorted(best.values(), key=lambda x: x[0], reverse=True)]
    return out[:limit]



def top_progression_hints(
    *,
    family: str = '',
    target_type: str = '',
    target_surface_signal: str = '',
    next_stage: str = '',
    host: str = '',
    limit: int = 3,
) -> List[Dict[str, Any]]:
    data = _load()
    priors = data.get('progression_priors', {}) if isinstance(data.get('progression_priors'), dict) else {}
    host_priors = data.get('host_progression_priors', {}) if isinstance(data.get('host_progression_priors'), dict) else {}

    fam = str(family or '').strip().lower()
    ttype = str(target_type or '').strip().lower()
    signal = str(target_surface_signal or '').strip().lower()
    stage = str(next_stage or '').strip().lower()
    host_norm = str(host or '').strip().lower()
    scored: list[Tuple[str, float, Dict[str, Any]]] = []

    def _score_bucket(bucket: Dict[str, Any], *, host_boost: bool) -> float:
        seen = max(1, int(bucket.get('seen', 0)))
        prom = int(bucket.get('promising', 0))
        suc = int(bucket.get('success', 0))
        base = ((prom * 2) + suc) / seen
        if host_boost:
            base += 0.35
        return base

    def _matches(bucket: Dict[str, Any]) -> bool:
        if fam and str(bucket.get('family') or '').strip().lower() != fam:
            return False
        if ttype and str(bucket.get('target_type') or '').strip().lower() != ttype:
            return False
        if signal:
            bucket_signal = str(bucket.get('target_surface_signal') or '').strip().lower()
            if signal not in bucket_signal.split('|'):
                return False
        if stage and str(bucket.get('next_stage') or '').strip().lower() != stage:
            return False
        return bool(str(bucket.get('next_family') or '').strip().lower() or str(bucket.get('reconsult_tier') or '').strip().lower())

    for key, bucket in priors.items():
        if isinstance(bucket, dict) and _matches(bucket):
            scored.append((str(key), _score_bucket(bucket, host_boost=False), bucket))

    if host_norm:
        for key, bucket in host_priors.items():
            if not isinstance(bucket, dict):
                continue
            if str(bucket.get('host') or '').strip().lower() != host_norm:
                continue
            progression_key = str(bucket.get('progression') or key).strip()
            source = priors.get(progression_key) if isinstance(priors.get(progression_key), dict) else {}
            merged = dict(source) if isinstance(source, dict) else {}
            merged.update(bucket)
            if _matches(merged):
                scored.append((progression_key, _score_bucket(bucket, host_boost=True), merged))

    best: Dict[str, tuple[float, Dict[str, Any]]] = {}
    for progression_key, score, bucket in scored:
        next_family_val = str(bucket.get('next_family') or '').strip().lower()
        reconsult_val = str(bucket.get('reconsult_tier') or '').strip().lower()
        dedupe_key = f"{next_family_val}::{reconsult_val}"
        item = {
            'progression': progression_key,
            'next_family': next_family_val,
            'reconsult_tier': reconsult_val,
            'score': round(score, 3),
            'family': str(bucket.get('family') or '').strip().lower(),
            'target_type': str(bucket.get('target_type') or '').strip().lower(),
            'target_surface_signal': str(bucket.get('target_surface_signal') or '').strip().lower(),
            'next_stage': str(bucket.get('next_stage') or '').strip().lower(),
        }
        current = best.get(dedupe_key)
        if current is None or score > current[0]:
            best[dedupe_key] = (score, item)

    out = [item for _score, item in sorted(best.values(), key=lambda x: x[0], reverse=True)]
    return out[:limit]



def top_archetype_hints(*, target_type: str = '', host: str = '', limit: int = 3) -> List[Dict[str, Any]]:
    data = _load()
    priors = data.get('archetype_priors', {}) if isinstance(data.get('archetype_priors'), dict) else {}
    host_priors = data.get('host_archetype_priors', {}) if isinstance(data.get('host_archetype_priors'), dict) else {}
    ttype = str(target_type or '').strip().lower()
    host_norm = str(host or '').strip().lower()
    scored: list[Tuple[str, float, Dict[str, Any]]] = []

    def _score_bucket(bucket: Dict[str, Any], *, host_boost: bool) -> float:
        seen = max(1, int(bucket.get('seen', 0)))
        prom = int(bucket.get('promising', 0))
        suc = int(bucket.get('success', 0))
        base = ((prom * 2) + suc) / seen
        if host_boost:
            base += 0.35
        return base

    for key, bucket in priors.items():
        if not isinstance(bucket, dict):
            continue
        if ttype and str(bucket.get('target_type') or '').strip().lower() != ttype:
            continue
        if str(bucket.get('archetype') or '').strip().lower():
            scored.append((str(key), _score_bucket(bucket, host_boost=False), bucket))

    if host_norm:
        for key, bucket in host_priors.items():
            if not isinstance(bucket, dict):
                continue
            if str(bucket.get('host') or '').strip().lower() != host_norm:
                continue
            if ttype and str(bucket.get('target_type') or '').strip().lower() != ttype:
                continue
            scored.append((str(key), _score_bucket(bucket, host_boost=True), bucket))

    best: Dict[str, tuple[float, Dict[str, Any]]] = {}
    for archetype_key, score, bucket in scored:
        archetype = str(bucket.get('archetype') or '').strip().lower()
        if not archetype:
            continue
        item = {
            'archetype_key': archetype_key,
            'archetype': archetype,
            'target_type': str(bucket.get('target_type') or '').strip().lower(),
            'score': round(score, 3),
        }
        current = best.get(archetype)
        if current is None or score > current[0]:
            best[archetype] = (score, item)

    out = [item for _score, item in sorted(best.values(), key=lambda x: x[0], reverse=True)]
    return out[:limit]



def top_branch_hints(*, branch_state: str = '', branch_action: str = '', branch_reason: str = '', next_stage: str = '', host: str = '', limit: int = 3) -> List[Dict[str, Any]]:
    data = _load()
    priors = data.get('branch_priors', {}) if isinstance(data.get('branch_priors'), dict) else {}
    host_priors = data.get('host_branch_priors', {}) if isinstance(data.get('host_branch_priors'), dict) else {}
    branch_state_l = str(branch_state or '').strip().lower()
    branch_action_l = str(branch_action or '').strip().lower()
    branch_reason_l = str(branch_reason or '').strip().lower()
    next_stage_l = str(next_stage or '').strip().lower()
    host_norm = str(host or '').strip().lower()
    scored: list[Tuple[str, float, Dict[str, Any]]] = []

    def _score_bucket(bucket: Dict[str, Any], *, host_boost: bool) -> float:
        seen = max(1, int(bucket.get('seen', 0)))
        productive = int(bucket.get('productive', 0))
        dead_end = int(bucket.get('dead_end', 0))
        prom = int(bucket.get('promising', 0))
        base = ((productive * 1.4) + (prom * 0.4) - (dead_end * 1.3)) / seen
        if host_boost:
            base += 0.25
        return base

    def _matches(bucket: Dict[str, Any]) -> bool:
        if branch_state_l and str(bucket.get('branch_state') or '').strip().lower() != branch_state_l:
            return False
        if branch_action_l and str(bucket.get('branch_action') or '').strip().lower() != branch_action_l:
            return False
        if branch_reason_l and str(bucket.get('branch_reason') or '').strip().lower() != branch_reason_l:
            return False
        if next_stage_l and str(bucket.get('next_stage') or '').strip().lower() != next_stage_l:
            return False
        return True

    for key, bucket in priors.items():
        if not isinstance(bucket, dict) or not _matches(bucket):
            continue
        scored.append((str(key), _score_bucket(bucket, host_boost=False), dict(bucket)))

    if host_norm:
        for key, bucket in host_priors.items():
            if not isinstance(bucket, dict) or str(bucket.get('host') or '').strip().lower() != host_norm:
                continue
            branch_key = str(bucket.get('branch') or key).strip()
            source = priors.get(branch_key) if isinstance(priors.get(branch_key), dict) else {}
            merged = dict(source) if isinstance(source, dict) else {}
            merged.update(bucket)
            if not _matches(merged):
                continue
            scored.append((str(key), _score_bucket(merged, host_boost=True), merged))

    best: Dict[str, tuple[float, Dict[str, Any]]] = {}
    for branch_key, score, bucket in scored:
        dedupe_key = '::'.join([
            str(bucket.get('branch_state') or '').strip().lower(),
            str(bucket.get('branch_action') or '').strip().lower(),
            str(bucket.get('branch_reason') or '').strip().lower(),
            str(bucket.get('next_stage') or '').strip().lower(),
        ])
        item = {
            'branch_key': branch_key,
            'branch_state': str(bucket.get('branch_state') or '').strip().lower(),
            'branch_action': str(bucket.get('branch_action') or '').strip().lower(),
            'branch_reason': str(bucket.get('branch_reason') or '').strip().lower(),
            'next_stage': str(bucket.get('next_stage') or '').strip().lower(),
            'branch_outcome': str(bucket.get('branch_outcome') or '').strip().lower(),
            'branch_lifecycle_status': str(bucket.get('branch_lifecycle_status') or '').strip().lower(),
            'branch_lifecycle_reason': str(bucket.get('branch_lifecycle_reason') or '').strip().lower(),
            'branch_thread_key': str(bucket.get('branch_thread_key') or '').strip().lower(),
            'branch_thread_label': str(bucket.get('branch_thread_label') or '').strip().lower(),
            'productive': int(bucket.get('productive', 0) or 0),
            'dead_end': int(bucket.get('dead_end', 0) or 0),
            'score': round(score, 3),
        }
        current = best.get(dedupe_key)
        if current is None or score > current[0]:
            best[dedupe_key] = (score, item)

    out = [item for _score, item in sorted(best.values(), key=lambda x: x[0], reverse=True)]
    return out[:limit]



def summarize_branch_threads(limit: int = 5) -> List[Dict[str, Any]]:
    data = _load()
    priors = data.get('branch_priors', {}) if isinstance(data.get('branch_priors'), dict) else {}
    grouped: Dict[str, Dict[str, Any]] = {}
    for bucket in priors.values():
        if not isinstance(bucket, dict):
            continue
        thread_key = str(bucket.get('branch_thread_key') or '').strip().lower()
        if not thread_key:
            continue
        entry = grouped.setdefault(thread_key, {
            'branch_thread_key': thread_key,
            'branch_thread_label': str(bucket.get('branch_thread_label') or '').strip().lower(),
            'branch_action': str(bucket.get('branch_action') or '').strip().lower(),
            'branch_reason': str(bucket.get('branch_reason') or '').strip().lower(),
            'next_stage': str(bucket.get('next_stage') or '').strip().lower(),
            'productive': 0,
            'dead_end': 0,
            'seen': 0,
            'lifecycle_counts': {},
        })
        entry['productive'] += int(bucket.get('productive', 0) or 0)
        entry['dead_end'] += int(bucket.get('dead_end', 0) or 0)
        entry['seen'] += int(bucket.get('seen', 0) or 0)
        lifecycle = str(bucket.get('branch_lifecycle_status') or '').strip().lower()
        if lifecycle:
            counts = entry.get('lifecycle_counts') if isinstance(entry.get('lifecycle_counts'), dict) else {}
            counts[lifecycle] = int(counts.get(lifecycle, 0) or 0) + int(bucket.get('seen', 0) or 0)
            entry['lifecycle_counts'] = counts
        if not entry.get('branch_thread_label'):
            entry['branch_thread_label'] = str(bucket.get('branch_thread_label') or '').strip().lower()
    out: List[Dict[str, Any]] = []
    for entry in grouped.values():
        lifecycle_counts = entry.get('lifecycle_counts') if isinstance(entry.get('lifecycle_counts'), dict) else {}
        dominant_lifecycle = ''
        if lifecycle_counts:
            dominant_lifecycle = str(max(lifecycle_counts.items(), key=lambda item: int(item[1] or 0))[0])
        seen = max(1, int(entry.get('seen', 0) or 0))
        score = round(((int(entry.get('productive', 0) or 0) * 1.4) - (int(entry.get('dead_end', 0) or 0) * 1.3)) / seen, 3)
        out.append({
            'branch_thread_key': str(entry.get('branch_thread_key') or ''),
            'branch_thread_label': str(entry.get('branch_thread_label') or ''),
            'branch_action': str(entry.get('branch_action') or ''),
            'branch_reason': str(entry.get('branch_reason') or ''),
            'next_stage': str(entry.get('next_stage') or ''),
            'productive': int(entry.get('productive', 0) or 0),
            'dead_end': int(entry.get('dead_end', 0) or 0),
            'seen': int(entry.get('seen', 0) or 0),
            'dominant_lifecycle_status': dominant_lifecycle,
            'pressure_score': score,
        })
    out.sort(key=lambda item: (float(item.get('pressure_score', 0.0) or 0.0), int(item.get('seen', 0) or 0)), reverse=True)
    return out[:limit]


def summarize_learning(limit: int = 5) -> Dict[str, Any]:
    data = _load()
    fams = data.get("families", {}) if isinstance(data.get("families"), dict) else {}
    caps = data.get("capabilities", {}) if isinstance(data.get("capabilities"), dict) else {}
    family_caps = data.get("family_capabilities", {}) if isinstance(data.get("family_capabilities"), dict) else {}
    host_cap_pairs = data.get("host_capability_pairs", {}) if isinstance(data.get("host_capability_pairs"), dict) else {}
    tools = data.get("tools", {}) if isinstance(data.get("tools"), dict) else {}
    action_types = data.get("action_types", {}) if isinstance(data.get("action_types"), dict) else {}
    host_stages = data.get("host_stages", {}) if isinstance(data.get("host_stages"), dict) else {}
    planning_stages = data.get("planning_stages", {}) if isinstance(data.get("planning_stages"), dict) else {}
    next_stages = data.get("next_stages", {}) if isinstance(data.get("next_stages"), dict) else {}
    target_types = data.get("target_types", {}) if isinstance(data.get("target_types"), dict) else {}
    target_surface_signals = data.get("target_surface_signals", {}) if isinstance(data.get("target_surface_signals"), dict) else {}
    transitions = data.get("transitions", {}) if isinstance(data.get("transitions"), dict) else {}
    host_transition_pairs = data.get("host_transition_pairs", {}) if isinstance(data.get("host_transition_pairs"), dict) else {}
    progression_priors = data.get("progression_priors", {}) if isinstance(data.get("progression_priors"), dict) else {}
    host_progression_priors = data.get("host_progression_priors", {}) if isinstance(data.get("host_progression_priors"), dict) else {}
    archetype_priors = data.get("archetype_priors", {}) if isinstance(data.get("archetype_priors"), dict) else {}
    host_archetype_priors = data.get("host_archetype_priors", {}) if isinstance(data.get("host_archetype_priors"), dict) else {}
    branch_priors = data.get("branch_priors", {}) if isinstance(data.get("branch_priors"), dict) else {}
    host_branch_priors = data.get("host_branch_priors", {}) if isinstance(data.get("host_branch_priors"), dict) else {}
    return {
        "updated_at": data.get("updated_at"),
        "top_families": _top_scored_items(fams, key_name='family', limit=limit),
        "top_capabilities": _top_scored_items(caps, key_name='capability', limit=limit),
        "top_family_capabilities": _top_scored_items(family_caps, key_name='family_capability', limit=limit),
        "top_host_capability_pairs": _top_scored_items(host_cap_pairs, key_name='host_capability', limit=limit),
        "top_tools": _top_scored_items(tools, key_name='tool', limit=limit),
        "top_action_types": _top_scored_items(action_types, key_name='action_type', limit=limit),
        "top_host_stages": _top_scored_items(host_stages, key_name='host_stage', limit=limit),
        "top_planning_stages": _top_scored_items(planning_stages, key_name='planning_stage', limit=limit),
        "top_next_stages": _top_scored_items(next_stages, key_name='next_stage', limit=limit),
        "top_target_types": _top_scored_items(target_types, key_name='target_type', limit=limit),
        "top_target_surface_signals": _top_scored_items(target_surface_signals, key_name='target_surface_signal', limit=limit),
        "top_transitions": _top_scored_items(transitions, key_name='transition', limit=limit),
        "top_host_transitions": _top_scored_items(host_transition_pairs, key_name='host_transition', limit=limit),
        "top_progression_priors": _top_scored_items(progression_priors, key_name='progression', limit=limit),
        "top_host_progression_priors": _top_scored_items(host_progression_priors, key_name='host_progression', limit=limit),
        "top_archetype_priors": _top_scored_items(archetype_priors, key_name='archetype_key', limit=limit),
        "top_host_archetype_priors": _top_scored_items(host_archetype_priors, key_name='host_archetype_key', limit=limit),
        "top_branch_priors": _top_scored_items(branch_priors, key_name='branch_key', limit=limit),
        "top_host_branch_priors": _top_scored_items(host_branch_priors, key_name='host_branch_key', limit=limit),
        "top_branch_threads": summarize_branch_threads(limit=limit),
    }
