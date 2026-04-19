from __future__ import annotations

DEFAULT_ACTION_TYPE = 'single_probe'
ACTION_TYPES = {
    'single_probe',
    'fingerprint_probe',
    'enumeration_probe',
    'differential_probe',
    'confirmatory_probe',
    'variant_probe',
    'state_transition_probe',
}

DEFAULT_CAPABILITY = 'http_probe'
ACTION_TYPE_TO_CAPABILITY = {
    'single_probe': 'http_probe',
    'fingerprint_probe': 'http_fingerprint',
    'enumeration_probe': 'content_discovery',
    'differential_probe': 'http_probe',
    'confirmatory_probe': 'http_probe',
    'variant_probe': 'http_probe',
    'state_transition_probe': 'http_probe',
}
ACTION_TYPE_TO_EXPERIMENT_SHAPE = {
    'single_probe': 'single_step',
    'fingerprint_probe': 'fingerprint',
    'enumeration_probe': 'enumeration',
    'differential_probe': 'differential',
    'confirmatory_probe': 'single_step',
    'variant_probe': 'variant',
    'state_transition_probe': 'state_transition',
}
ALLOWED_EXPERIMENT_SHAPES = {
    'single_step',
    'bounded_chain',
    'differential',
    'variant',
    'state_transition',
    'enumeration',
    'fingerprint',
}
ALLOWED_TARGET_CARDINALITY = {'single', 'bounded'}
ALLOWED_CHAIN_ROLES = {
    'enumerate',
    'fetch',
    'probe',
    'validate',
    'scan',
    'observe',
    'capture',
    'analyze',
    'fingerprint',
}
CHAIN_MAX_STEPS = 2
TOOL_CANDIDATE_MAX = 4
SEQUENCE_MAX_STEPS = 4
VARIANT_MAX_STEPS = 6
DIFFERENTIAL_MAX_STEPS = 4
ENUMERATION_VARIANT_MAX = 3
