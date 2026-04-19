from __future__ import annotations

from typing import Any, Dict, List

from .planner_intent_contract import (
    PLANNER_INTENT_REQUIRED_DICT_FIELDS,
    PLANNER_INTENT_REQUIRED_FIELDS,
    PLANNER_INTENT_REQUIRED_STRING_FIELDS,
    validate_experiment_intent_contract,
)

BLUEPRINT_SCHEMA: Dict[str, Any] = {
    'required': [
        'schema_version',
        'campaign_id',
        'campaign_name_template',
        'source_program_hash_sha256',
        'operator_flags_hash_sha256',
        'planner_semantics_hash_sha256',
        'planner_identity_hash_sha256',
        'planner_provenance_mode',
        'blueprint_hash_sha256',
        'version',
        'operator_approval',
        'aggression_profile',
        'credentials_policy',
        'planner_hints',
        'planner_directives',
        'variants',
        'structured_scope',
        'target_profiles',
        'task_family_seeds',
        'experiment_intents',
        'attack_taxonomy',
        'interpretations',
        'budget_recommendations',
        'target_taxonomy',
        'success_criteria',
    ]
}


def _require_keys(data: Dict[str, Any], keys: List[str]) -> List[str]:
    return [k for k in keys if k not in data]


def validate_blueprint(data: Dict[str, Any]) -> None:
    missing = _require_keys(data, BLUEPRINT_SCHEMA['required'])
    if missing:
        raise ValueError(f"missing_required_keys:{','.join(missing)}")

    if not isinstance(data.get('variants'), list) or len(data['variants']) != 3:
        raise ValueError('variants_must_have_3_items')

    names = {v.get('name') for v in data['variants'] if isinstance(v, dict)}
    expected = {'cost_effective', 'easy_to_hard', 'high_reward_high_effort'}
    if names != expected:
        raise ValueError('variant_names_invalid')

    if not isinstance(data.get('interpretations'), list):
        raise ValueError('interpretations_must_be_list')

    ap = data.get('aggression_profile')
    if not isinstance(ap, dict):
        raise ValueError('aggression_profile_must_be_object')
    for key in ['policy_min', 'policy_max', 'recommended_min', 'recommended_default', 'recommended_max']:
        if key not in ap:
            raise ValueError(f'aggression_profile_missing_{key}')

    cp = data.get('credentials_policy')
    if not isinstance(cp, dict):
        raise ValueError('credentials_policy_must_be_object')
    for key in ['credentials_required', 'allow_auth_header', 'allow_cookie_header', 'allow_basic_auth', 'owner_approval_required']:
        if key not in cp:
            raise ValueError(f'credentials_policy_missing_{key}')

    hints = data.get('planner_hints')
    if not isinstance(hints, dict):
        raise ValueError('planner_hints_must_be_object')

    directives = data.get('planner_directives')
    if not isinstance(directives, dict):
        raise ValueError('planner_directives_must_be_object')
    for key in ['constraints', 'preferences', 'unknowns']:
        if not isinstance(directives.get(key), dict):
            raise ValueError(f'planner_directives_missing_{key}')

    if data.get('planner_provenance_mode') not in {'deterministic', 'hybrid'}:
        raise ValueError('planner_provenance_mode_invalid')

    if not isinstance(data.get('target_profiles'), dict):
        raise ValueError('target_profiles_must_be_object')
    if not isinstance(data.get('task_family_seeds'), dict):
        raise ValueError('task_family_seeds_must_be_object')
    if not isinstance(data.get('experiment_intents'), list):
        raise ValueError('experiment_intents_must_be_list')

    domains = ((data.get('structured_scope') or {}).get('domains') or []) if isinstance(data.get('structured_scope'), dict) else []
    invalid = ((data.get('structured_scope') or {}).get('invalid_domain_candidates') or []) if isinstance(data.get('structured_scope'), dict) else []
    if invalid and not domains:
        raise ValueError('invalid_domain_candidates_present_without_valid_domains')
    if not domains:
        raise ValueError('structured_scope_domains_empty')

    counts = ((data.get('target_taxonomy') or {}).get('counts') or {}) if isinstance(data.get('target_taxonomy'), dict) else {}
    typed_non_host = sum(int(counts.get(k, 0) or 0) for k in ['api', 'web', 'auth', 'static', 'sandbox', 'integration', 'support'])
    if typed_non_host <= 0:
        raise ValueError('target_taxonomy_too_flat')

    if bool((hints or {}).get('llm_used')) and not any((hints or {}).get(k) for k in ['global_vectors', 'ambiguities', 'candidate_targets']):
        raise ValueError('llm_used_without_hint_payload')

    for item in data['interpretations']:
        if not isinstance(item, dict):
            raise ValueError('interpretation_item_not_dict')
        for key in ['source_fragment', 'rule_id', 'decision', 'confidence', 'trace_id']:
            if key not in item:
                raise ValueError(f'interpretation_missing_{key}')

    for item in data['experiment_intents']:
        if not isinstance(item, dict):
            raise ValueError('experiment_intent_item_not_dict')
        for key in PLANNER_INTENT_REQUIRED_FIELDS:
            if key not in item:
                raise ValueError(f'experiment_intent_missing_{key}')
        if not isinstance(item.get('capability_candidates'), list) or not item.get('capability_candidates'):
            raise ValueError('experiment_intent_capability_candidates_invalid')
        if not isinstance(item.get('recommended_action_types'), list) or not item.get('recommended_action_types'):
            raise ValueError('experiment_intent_recommended_action_types_invalid')
        if not isinstance(item.get('runtime_task_contract'), dict) or int(item.get('runtime_task_contract', {}).get('schema_version', 0) or 0) != 2:
            raise ValueError('experiment_intent_runtime_task_contract_invalid')
        for dict_key in PLANNER_INTENT_REQUIRED_DICT_FIELDS:
            if not isinstance(item.get(dict_key), dict):
                raise ValueError(f'experiment_intent_{dict_key}_invalid')
        for str_key in PLANNER_INTENT_REQUIRED_STRING_FIELDS:
            if not str(item.get(str_key) or '').strip():
                raise ValueError(f'experiment_intent_{str_key}_invalid')
        validate_experiment_intent_contract(item)
