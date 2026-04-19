from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import uuid
from typing import Any, Dict, List, Tuple

from aggression_policy import clamp_aggression

OPENCLAW_BIN = shutil.which("openclaw") or "/usr/local/bin/openclaw"
DOMAIN_RE = re.compile(r"(?:\*\.)?(?:[a-z0-9-]+\.)+[a-z]{2,}", re.IGNORECASE)


def _normalize_llm_attack_vectors(raw_vectors: Any) -> List[str]:
    if not isinstance(raw_vectors, list):
        return []
    out: List[str] = []

    def add(*items: str) -> None:
        for item in items:
            val = str(item or '').strip().lower()
            if val and val not in out:
                out.append(val)

    for raw in raw_vectors:
        text = str(raw or '').strip().lower()
        if not text:
            continue
        if any(k in text for k in ['idor', 'authz', 'authorization', 'unauthorized', 'access control', 'permission']):
            add('authz')
        if any(k in text for k in ['xss', 'stored xss', 'reflected xss', 'client-side script', 'script injection']):
            add('client_input')
        if 'csrf' in text or 'cross-site request forgery' in text:
            add('auth_flow')
        if 'ssrf' in text or 'server-side request forgery' in text or 'trust-boundary' in text:
            add('input_tamper')
        if any(k in text for k in ['logic flaw', 'business logic', 'workflow', 'order flow', 'password flow', 'account flow']):
            add('workflow')
        if any(k in text for k in ['recon', 'enumeration', 'fuzz', 'surface mapping', 'path surface', 'endpoint discovery']):
            add('content_discovery')
        if any(k in text for k in ['open redirect', 'redirect']) and 'redirect_trust' not in out:
            add('redirect_trust')
        if not any(k in text for k in ['idor', 'authz', 'authorization', 'unauthorized', 'xss', 'csrf', 'ssrf', 'logic', 'workflow', 'recon', 'fuzz', 'redirect']):
            token = re.sub(r'[^a-z0-9]+', '_', text).strip('_')
            if token:
                add(token)
    return out[:8]


def _extract_json(text: str) -> Dict[str, Any]:
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    s = text.find("{")
    e = text.rfind("}")
    if s != -1 and e != -1 and e > s:
        data = json.loads(text[s : e + 1])
        if isinstance(data, dict):
            return data
    raise ValueError("invalid_json")


def _default_llm_interpret_enabled() -> bool:
    env = str(os.getenv("RAVENCLAW_PLANNER_LLM_INTERPRET", "")).strip().lower()
    if env in {"1", "true", "yes", "on"}:
        return True
    if env in {"0", "false", "no", "off"}:
        return False
    if os.getenv("PYTEST_CURRENT_TEST"):
        return False
    return True


def _run_agent(agent_id: str, message: str, timeout: int = 120) -> str:
    session_id = str(uuid.uuid4())
    cmd = [
        OPENCLAW_BIN,
        "agent",
        "--agent",
        agent_id,
        "--session-id",
        session_id,
        "--message",
        message,
        "--json",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "agent_failed")
    data = json.loads(proc.stdout)
    payloads = data.get("result", {}).get("payloads", [])
    if not payloads:
        raise RuntimeError("empty_payload")
    return (payloads[0].get("text") or "").strip()


def interpret_scope_with_llm(raw_scope_text: str, operator_flags: Dict[str, Any] | None = None) -> Tuple[Dict[str, Any] | None, Dict[str, Any]]:
    flags = operator_flags or {}
    enabled = bool(flags.get("llm_interpret", _default_llm_interpret_enabled()))
    model_hint = str(flags.get("planner_model", "BRAIN"))
    meta: Dict[str, Any] = {
        "enabled": enabled,
        "used": False,
        "model_hint": model_hint,
        "errors": [],
        "default_test_mode_disabled": bool(not flags.get("llm_interpret") and os.getenv("PYTEST_CURRENT_TEST")),
    }
    if not enabled:
        return None, meta

    prompt = (
        "You are PLANER LLM interpreter. Convert bug bounty program text into strict JSON only. "
        "Do not add markdown. Keep output compact.\n"
        "Required JSON shape:\n"
        "{\n"
        "  \"program_name\": \"...\",\n"
        "  \"in_scope_targets\": [\"domain.tld\", \"*.domain.tld\"],\n"
        "  \"out_of_scope_targets\": [\"...\"],\n"
        "  \"allow_keywords\": [\"xss\",\"idor\",\"csrf\",\"ssrf\",\"open redirect\",\"recon\",\"fuzz\"],\n"
        "  \"deny_keywords\": [\"dos\",\"brute force\",\"social engineering\",\"phishing\",\"real user data\"],\n"
        "  \"aggression\": {\"recommended_min\": 1, \"recommended_default\": 5, \"recommended_max\": 8, \"confidence\": 0.7, \"rationale\": [\"...\"]},\n"
        "  \"credentials_policy\": {\"credentials_required\": false, \"allow_auth_header\": false, \"allow_cookie_header\": false, \"allow_basic_auth\": false, \"owner_approval_required\": true, \"notes\": [\"...\"]},\n"
        "  \"suggested_attack_vectors\": [\"...\"],\n"
        "  \"ambiguities\": [\"...\"],\n"
        "  \"confidence\": 0.0\n"
        "}\n"
        "Program text:\n"
        f"{raw_scope_text[:24000]}"
    )
    try:
        raw = _run_agent("brain", prompt, timeout=140)
        data = _extract_json(raw)
        meta["used"] = True
        return data, meta
    except Exception as exc:
        meta["errors"].append(str(exc))
        return None, meta


def reconcile_with_deterministic(parsed: Dict[str, Any], llm_data: Dict[str, Any] | None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    out = dict(parsed)
    meta: Dict[str, Any] = {"conflicts": [], "llm_confidence": None, "hints": {}}
    if not llm_data:
        return out, meta

    llm_targets_raw = llm_data.get("in_scope_targets") or []
    llm_domains: List[str] = []
    if isinstance(llm_targets_raw, list):
        for t in llm_targets_raw:
            s = str(t or "")
            llm_domains.extend(d.lower() for d in DOMAIN_RE.findall(s))
    llm_domains = sorted(set(llm_domains))

    base_domains = sorted(set(str(d).lower() for d in (out.get("domains") or [])))
    candidate_llm_domains = sorted(d for d in llm_domains if d not in set(base_domains))
    if candidate_llm_domains:
        meta["conflicts"].append("llm_added_candidate_domains")

    base_excl = {str(x).lower() for x in (out.get("out_of_scope_targets") or [])}
    llm_excl = {str(x).lower() for x in (llm_data.get("out_of_scope_targets") or [])} if isinstance(llm_data.get("out_of_scope_targets"), list) else set()
    merged_excl = sorted(base_excl | llm_excl)

    # exact exclusion removal at blueprint domain list level (wildcard exceptions are enforced in runtime scope gate)
    out["domains"] = [d for d in base_domains if d not in set(merged_excl)]
    out["candidate_targets_from_llm"] = [d for d in candidate_llm_domains if d not in set(merged_excl)]
    out["out_of_scope_targets"] = merged_excl

    base_targets = {str((t or {}).get("host", "")).lower(): t for t in (out.get("targets") or []) if isinstance(t, dict)}
    for d in out["domains"]:
        if d not in base_targets:
            base_targets[d] = {"host": d, "type": "host", "in_scope": True, "source": "deterministic"}
    out["targets"] = list(base_targets.values())

    allow = set(str(x).lower() for x in (out.get("allow_keywords") or []))
    deny = set(str(x).lower() for x in (out.get("deny_keywords") or []))
    if isinstance(llm_data.get("allow_keywords"), list):
        allow |= {str(x).lower() for x in llm_data["allow_keywords"]}
    if isinstance(llm_data.get("deny_keywords"), list):
        deny |= {str(x).lower() for x in llm_data["deny_keywords"]}
    out["allow_keywords"] = sorted(allow)
    out["deny_keywords"] = sorted(deny)

    aggr = llm_data.get("aggression") if isinstance(llm_data.get("aggression"), dict) else {}
    rec_min = clamp_aggression(aggr.get("recommended_min", 3))
    rec_def = clamp_aggression(aggr.get("recommended_default", 5))
    rec_max = clamp_aggression(aggr.get("recommended_max", 8))
    if rec_min > rec_max:
        rec_min, rec_max = rec_max, rec_min
    if rec_def < rec_min:
        rec_def = rec_min
    if rec_def > rec_max:
        rec_def = rec_max

    meta["llm_confidence"] = float(aggr.get("confidence", llm_data.get("confidence", 0.6)) or 0.6)
    cred = llm_data.get("credentials_policy") if isinstance(llm_data.get("credentials_policy"), dict) else {}
    base_cred = parsed.get("credentials_policy") if isinstance(parsed.get("credentials_policy"), dict) else {}
    cred_policy = {
        "credentials_required": bool(cred.get("credentials_required", base_cred.get("credentials_required", False))),
        "allow_auth_header": bool(cred.get("allow_auth_header", base_cred.get("allow_auth_header", False))),
        "allow_cookie_header": bool(cred.get("allow_cookie_header", base_cred.get("allow_cookie_header", False))),
        "allow_basic_auth": bool(cred.get("allow_basic_auth", base_cred.get("allow_basic_auth", False))),
        "owner_approval_required": bool(cred.get("owner_approval_required", True)),
        "notes": cred.get("notes", []),
    }

    out["credentials_policy"] = cred_policy
    normalized_vectors = _normalize_llm_attack_vectors(llm_data.get("suggested_attack_vectors", []))
    meta["hints"] = {
        "aggression": {
            "recommended_min": rec_min,
            "recommended_default": rec_def,
            "recommended_max": rec_max,
            "confidence": meta["llm_confidence"],
            "rationale": aggr.get("rationale", []),
        },
        "credentials_policy": cred_policy,
        "global_vectors": normalized_vectors,
        "raw_global_vectors": llm_data.get("suggested_attack_vectors", []),
        "ambiguities": llm_data.get("ambiguities", []),
        "candidate_targets": out.get("candidate_targets_from_llm", []),
    }
    return out, meta
