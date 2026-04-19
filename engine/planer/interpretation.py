from __future__ import annotations

import hashlib
from typing import Any, Dict, List


def _trace_id(source_fragment: str, rule_id: str, decision: str) -> str:
    raw = f"{source_fragment}|{rule_id}|{decision}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def build_interpretations(parsed: Dict[str, Any], raw_text: str) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []

    for domain in parsed.get("domains", []):
        decision = f"domain_in_scope:{domain}"
        items.append(
            {
                "source_fragment": domain,
                "rule_id": "domain_regex_capture",
                "decision": decision,
                "description": "Domain captured from source text as in-scope target candidate.",
                "confidence": 0.98,
                "trace_id": _trace_id(domain, "domain_regex_capture", decision),
            }
        )

    if parsed.get("deny_keywords"):
        frag = ", ".join(parsed["deny_keywords"])
        decision = "deny_keywords_detected"
        items.append(
            {
                "source_fragment": frag,
                "rule_id": "deny_keyword_scan",
                "decision": decision,
                "description": "Potentially disallowed activity markers were detected in program text.",
                "confidence": 0.85,
                "trace_id": _trace_id(frag, "deny_keyword_scan", decision),
            }
        )

    if parsed.get("candidate_targets_from_llm"):
        frag = ", ".join(str(x) for x in parsed.get("candidate_targets_from_llm", [])[:8])
        decision = "llm_candidate_targets_present"
        items.append(
            {
                "source_fragment": frag,
                "rule_id": "llm_candidate_scope",
                "decision": decision,
                "description": "LLM suggested additional candidate targets that were not promoted into authoritative scope.",
                "confidence": 0.72,
                "trace_id": _trace_id(frag, "llm_candidate_scope", decision),
            }
        )

    if parsed.get("invalid_domain_candidates"):
        frag = ", ".join(str(x) for x in parsed.get("invalid_domain_candidates", [])[:8])
        decision = "invalid_scope_tokens_present"
        items.append(
            {
                "source_fragment": frag,
                "rule_id": "invalid_scope_token_scan",
                "decision": decision,
                "description": "Parser found domain-like tokens that were excluded from authoritative scope as malformed candidates.",
                "confidence": 0.81,
                "trace_id": _trace_id(frag, "invalid_scope_token_scan", decision),
            }
        )

    if not items:
        decision = "no_interpretive_signal"
        items.append(
            {
                "source_fragment": raw_text[:120],
                "rule_id": "fallback_minimal",
                "decision": decision,
                "description": "No explicit scope signals found; produced minimal deterministic baseline.",
                "confidence": 0.55,
                "trace_id": _trace_id(raw_text[:120], "fallback_minimal", decision),
            }
        )

    return items
