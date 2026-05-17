from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from govengine.semantic_loss_policy import classify_semantic_loss, semantic_loss_runtime_gate


def test_classify_semantic_loss_marks_bounded_lowering() -> None:
    out = classify_semantic_loss({'compiler_strategy': 'enumeration_lowering', 'semantic_loss_detected': False, 'normalization_reason': 'recipe:enum'})
    assert out['loss_class'] == 'bounded_lowering'
    assert out['policy_response'] == 'proceed_mark_degraded'


def test_classify_semantic_loss_marks_required_replan_for_unknown_passthrough() -> None:
    out = classify_semantic_loss({'compiler_strategy': 'passthrough', 'semantic_loss_detected': True, 'normalization_reason': 'unknown_action_type_lowered_to_passthrough'})
    gate = semantic_loss_runtime_gate(out)
    assert out['loss_class'] == 'unacceptable_flattening'
    assert out['policy_response'] == 'required_replan'
    assert gate['blocked'] is True
    assert gate['blocked_reason_code'] == 'semantic_loss_unknown_action_flattened'
