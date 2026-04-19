from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_runner_controls as rrc  # type: ignore



def test_build_main_runtime_controls_normalizes_invalid_qualification_mode() -> None:
    out = rrc.build_main_runtime_controls({'qualification_mode': 'weird'})
    assert out.qualification_mode == 'shadow'
    assert out.code000_streak_threshold == 3
    assert out.max_followups_per_target == 2



def test_build_main_runtime_controls_respects_explicit_values() -> None:
    out = rrc.build_main_runtime_controls(
        {
            'qualification_mode': 'enforce',
            'code000_streak_threshold': 7,
            'code000_session_cap': 9,
            'code000_cooldown_sec': 123,
            'autodiscover_deep_skip': False,
            'max_followups_per_target': 4,
            'qualification_promising_threshold': 'confirmed',
            'max_confirm_jobs_per_target': 2,
            'confirm_job_cooldown_sec': 456,
            'max_confirm_jobs_total': 22,
            'max_confirm_jobs_per_class': 6,
        }
    )
    assert out.qualification_mode == 'enforce'
    assert out.code000_streak_threshold == 7
    assert out.code000_session_cap == 9
    assert out.code000_cooldown_sec == 123
    assert out.autodiscover_deep_skip is False
    assert out.max_followups_per_target == 4
    assert out.qualification_promising_threshold == 'confirmed'
    assert out.max_confirm_jobs_per_target == 2
    assert out.confirm_job_cooldown_sec == 456
    assert out.max_confirm_jobs_total == 22
    assert out.max_confirm_jobs_per_class == 6
