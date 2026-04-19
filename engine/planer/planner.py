from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import sys

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)
from aggression_policy import derive_profile_from_scope  # type: ignore

from .blueprint import build_blueprint
from .identity import build_planner_identity
from .interpretation import build_interpretations
from .parser import parse_program_text
from .llm_interpreter import interpret_scope_with_llm, reconcile_with_deterministic
from .registry import find_existing_plan, store_plan
from .templates import build_templates


def build_or_load_campaign_plan(
    raw_scope_text: str,
    operator_flags: Dict[str, Any] | None,
    history: Dict[str, Any] | None,
    registry_root: Path,
    force_new_blueprint: bool = False,
) -> Dict[str, Any]:
    parsed = parse_program_text(raw_scope_text, operator_flags)
    llm_data, llm_meta = interpret_scope_with_llm(raw_scope_text, operator_flags)
    parsed_hybrid, hybrid_meta = reconcile_with_deterministic(parsed, llm_data)

    aggression_profile = derive_profile_from_scope(parsed_hybrid)
    hinted_aggr = (hybrid_meta.get('hints') or {}).get('aggression') if isinstance(hybrid_meta, dict) else None
    if isinstance(hinted_aggr, dict):
        aggression_profile.update({
            'recommended_min': hinted_aggr.get('recommended_min', aggression_profile.get('recommended_min')),
            'recommended_default': hinted_aggr.get('recommended_default', aggression_profile.get('recommended_default')),
            'recommended_max': hinted_aggr.get('recommended_max', aggression_profile.get('recommended_max')),
            'confidence': hinted_aggr.get('confidence', aggression_profile.get('confidence')),
            'rationale': list(dict.fromkeys((aggression_profile.get('rationale') or []) + (hinted_aggr.get('rationale') or []))),
        })

    operator_input = {
        'flags': operator_flags or {},
        'force_new_blueprint': bool(force_new_blueprint),
        'history_present': bool(history),
        'aggression_profile': aggression_profile,
        'llm_interpretation': {
            'enabled': llm_meta.get('enabled', False),
            'used': llm_meta.get('used', False),
            'errors': llm_meta.get('errors', []),
            'llm_confidence': hybrid_meta.get('llm_confidence'),
            'conflicts': hybrid_meta.get('conflicts', []),
            'suggested_attack_vectors': (hybrid_meta.get('hints') or {}).get('global_vectors', []),
            'raw_suggested_attack_vectors': (hybrid_meta.get('hints') or {}).get('raw_global_vectors', []),
            'ambiguities': (hybrid_meta.get('hints') or {}).get('ambiguities', []),
        },
    }

    identity = build_planner_identity(parsed_hybrid, operator_input)
    existing = find_existing_plan(registry_root, parsed_hybrid['source_hash'], identity['planner_identity_hash'])
    if existing and not force_new_blueprint:
        return {
            'status': 'existing',
            'registry': existing,
            'source_hash': parsed_hybrid['source_hash'],
            'planner_identity_hash': identity['planner_identity_hash'],
        }

    interpretations = build_interpretations(parsed_hybrid, raw_scope_text)
    blueprint = build_blueprint(parsed_hybrid, operator_input, interpretations)
    templates = build_templates(blueprint)
    stored = store_plan(registry_root, blueprint, templates)

    return {
        'status': 'created',
        'registry': stored,
        'campaign_id': blueprint['campaign_id'],
        'planner_identity_hash': blueprint.get('planner_identity_hash_sha256'),
        'interpretations': interpretations,
        'blueprint': blueprint,
    }
