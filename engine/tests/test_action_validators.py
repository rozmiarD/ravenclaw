from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from govengine.action_validators import validate_probe_recipe


def test_validate_probe_recipe_accepts_bounded_semantic_actions() -> None:
    assert validate_probe_recipe({'action_type': 'confirmatory_probe', 'probe_recipe': {'evidence_goal': 'confirm authz delta', 'variant_count': 2}}) == []
    assert validate_probe_recipe({'action_type': 'state_transition_probe', 'probe_recipe': {'sequence_steps': ['step1', 'step2'], 'variant_count': 1}}) == []


def test_validate_probe_recipe_rejects_missing_required_keys_and_variant_overflow() -> None:
    errors = validate_probe_recipe({'action_type': 'differential_probe', 'probe_recipe': {}})
    assert 'missing_comparison_mode' in errors
    assert any(e.startswith('differential_variant_count_out_of_range') for e in errors)
    errors2 = validate_probe_recipe({'action_type': 'variant_probe', 'probe_recipe': {'variant_count': 9}})
    assert any(e.startswith('variant_count_out_of_range') for e in errors2)
