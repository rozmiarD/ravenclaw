from __future__ import annotations

import hashlib
import json
from typing import Any, Dict

PLANNER_SEMANTICS_VERSION = 'planer-semantics-v2'
RECONCILE_MODE = 'deterministic_plus_llm_hybrid_v1'


def _stable_hash(payload: Dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
    return hashlib.sha256(blob.encode('utf-8')).hexdigest()


def _normalize_flags(flags: Any) -> Dict[str, Any]:
    if not isinstance(flags, dict):
        return {}
    return {str(k): flags[k] for k in sorted(flags.keys(), key=lambda x: str(x))}


def build_planner_identity(parsed: Dict[str, Any], operator_input: Dict[str, Any]) -> Dict[str, Any]:
    source_hash = str(parsed.get('source_hash') or '')
    llm_meta = (operator_input or {}).get('llm_interpretation') if isinstance((operator_input or {}).get('llm_interpretation'), dict) else {}
    flags = _normalize_flags((operator_input or {}).get('flags'))
    operator_flags_hash = _stable_hash({'flags': flags})
    planner_semantics_payload = {
        'planner_semantics_version': PLANNER_SEMANTICS_VERSION,
        'reconcile_mode': RECONCILE_MODE,
        'llm_enabled': bool(llm_meta.get('enabled', False)),
        'llm_used': bool(llm_meta.get('used', False)),
        'llm_errors_present': bool(llm_meta.get('errors')),
    }
    planner_semantics_hash = _stable_hash(planner_semantics_payload)
    planner_identity_hash = _stable_hash({
        'source_program_hash_sha256': source_hash,
        'operator_flags_hash': operator_flags_hash,
        'planner_semantics_hash': planner_semantics_hash,
    })
    planner_provenance_mode = 'hybrid' if bool(llm_meta.get('used', False)) else 'deterministic'
    return {
        'source_program_hash_sha256': source_hash,
        'operator_flags_hash': operator_flags_hash,
        'planner_semantics_hash': planner_semantics_hash,
        'planner_identity_hash': planner_identity_hash,
        'planner_provenance_mode': planner_provenance_mode,
        'planner_semantics_version': PLANNER_SEMANTICS_VERSION,
        'reconcile_mode': RECONCILE_MODE,
    }
