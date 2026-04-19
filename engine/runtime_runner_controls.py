from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MainRuntimeControls:
    code000_streak_threshold: int
    code000_session_cap: int
    code000_cooldown_sec: int
    autodiscover_deep_skip: bool
    max_followups_per_target: int
    qualification_mode: str
    qualification_promising_threshold: str
    max_confirm_jobs_per_target: int
    confirm_job_cooldown_sec: int
    max_confirm_jobs_total: int
    max_confirm_jobs_per_class: int



def build_main_runtime_controls(toggles: dict) -> MainRuntimeControls:
    qualification_mode = str(toggles.get('qualification_mode', 'shadow') or 'shadow').strip().lower()
    if qualification_mode not in {'shadow', 'enforce'}:
        qualification_mode = 'shadow'
    return MainRuntimeControls(
        code000_streak_threshold=int(toggles.get('code000_streak_threshold', 3) or 3),
        code000_session_cap=int(toggles.get('code000_session_cap', 5) or 5),
        code000_cooldown_sec=int(toggles.get('code000_cooldown_sec', 3600) or 3600),
        autodiscover_deep_skip=bool(toggles.get('autodiscover_deep_skip', True)),
        max_followups_per_target=int(toggles.get('max_followups_per_target', 2) or 2),
        qualification_mode=qualification_mode,
        qualification_promising_threshold=str(toggles.get('qualification_promising_threshold', 'probable') or 'probable').strip().lower(),
        max_confirm_jobs_per_target=int(toggles.get('max_confirm_jobs_per_target', 1) or 1),
        confirm_job_cooldown_sec=int(toggles.get('confirm_job_cooldown_sec', 900) or 900),
        max_confirm_jobs_total=int(toggles.get('max_confirm_jobs_total', 20) or 20),
        max_confirm_jobs_per_class=int(toggles.get('max_confirm_jobs_per_class', 8) or 8),
    )
