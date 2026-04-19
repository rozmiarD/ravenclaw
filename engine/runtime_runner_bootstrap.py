from __future__ import annotations

import json
import os
from pathlib import Path

from campaign_utils import load_scope_targets, summarize_scope, load_scope_domains
from feature_flags import normalize_pipeline_flags  # type: ignore
from learning_store import top_progression_hints
from paths import OPENCLAW_ENV_PATH, ep, wp  # type: ignore
from runtime_plan_control import summarize_planner_feedback, adaptive_quality_context  # type: ignore
from runtime_plan_service import load_planner_ui_state  # type: ignore


PIPELINE_CONFIG_PATH = ep('pipeline_config.json')


def selected_scope_path(*, load_planner_ui_state_fn=load_planner_ui_state, wp_fn=wp) -> Path:
    try:
        ui = load_planner_ui_state_fn()
        raw = str((ui or {}).get('scope_txt') or '').strip()
        if raw:
            p = Path(raw)
            if not p.is_absolute():
                p = wp_fn(raw)
            if p.exists():
                return p
            scope_candidate = wp_fn('scope', raw)
            if scope_candidate.exists():
                return scope_candidate
    except Exception:
        pass
    return wp_fn('scope', 'scope.txt')


def current_scope_targets(*, load_scope_domains_fn=load_scope_domains, load_scope_targets_fn=load_scope_targets) -> list[str]:
    try:
        domains = load_scope_domains_fn()
        exact = [str(x).strip().lower() for x in (domains.get('exact') or []) if str(x).strip()]
        suffix = [f'*.{str(x).strip().lower()}' for x in (domains.get('suffix') or []) if str(x).strip()]
        return sorted(dict.fromkeys(exact + suffix))
    except Exception:
        fallback = load_scope_targets_fn()
        return [str((item or {}).get('name') or '').strip() for item in fallback if str((item or {}).get('name') or '').strip()]


def current_scope_summary(*, current_scope_targets_fn=current_scope_targets, summarize_scope_fn=summarize_scope) -> str:
    targets = current_scope_targets_fn()
    if targets:
        return ', '.join(targets[:20])
    return summarize_scope_fn()


def load_openclaw_env(*, environ=None, env_path: Path | None = None, warn_fn=None) -> dict:
    env = dict((environ or os.environ).copy())
    resolved_path = env_path or OPENCLAW_ENV_PATH
    try:
        if resolved_path.exists():
            for line in resolved_path.read_text(encoding='utf-8').splitlines():
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                k, v = line.split('=', 1)
                if k and v:
                    env.setdefault(k.strip(), v.strip())
    except OSError as exc:
        if callable(warn_fn):
            warn_fn(f'failed to load env file {resolved_path}: {exc}')
    return env


def load_runtime_toggles(*, pipeline_config_path: str | Path = PIPELINE_CONFIG_PATH, normalize_pipeline_flags_fn=normalize_pipeline_flags, warn_fn=None) -> dict:
    defaults = {
        'max_followups_per_target': 1,
        'planner_reconsult_on_high_signal': False,
        'planner_reconsult_min_interval_runs': 12,
        'planner_reconsult_signal_threshold': 15,
        'dynamic_plan_adaptation': True,
        'freeze_plan_revision': False,
        'aggressive_adaptation': False,
        'family_lane_boost': [],
        'family_lane_suppress': [],
        'family_decay_enabled': True,
        'family_decay_window_runs': 24,
        'family_decay_penalty': 0.12,
        'host_family_lane_boost': {},
        'host_family_lane_suppress': {},
        'qualification_mode': 'shadow',
        'qualification_promising_threshold': 'probable',
        'max_confirm_jobs_per_target': 1,
        'confirm_job_cooldown_sec': 900,
    }
    resolved = Path(str(pipeline_config_path))
    try:
        if resolved.exists():
            data = json.loads(resolved.read_text(encoding='utf-8'))
            if isinstance(data, dict):
                defaults.update(data)
    except (OSError, json.JSONDecodeError) as exc:
        if callable(warn_fn):
            warn_fn(f'failed to load runtime toggles from {resolved}: {exc}')
    return normalize_pipeline_flags_fn(defaults)


def maybe_reconsult_planner(toggles: dict, runs: list[dict], promising_count: int, host_state: dict | None = None, *, summarize_planner_feedback_fn=summarize_planner_feedback) -> str:
    if not bool(toggles.get('planner_reconsult_on_high_signal', False)):
        return ''
    min_interval = max(1, int(toggles.get('planner_reconsult_min_interval_runs', 10) or 10))
    threshold = max(1, int(toggles.get('planner_reconsult_signal_threshold', 4) or 4))
    if len(runs) % min_interval != 0:
        return ''
    feedback = summarize_planner_feedback_fn(runs=runs, host_state=host_state)
    reconsult_worthy_recent = int(feedback.get('reconsult_worthy_recent', 0) or 0)
    adaptation_positive_recent = int(feedback.get('adaptation_positive_recent', 0) or 0)
    next_stage_hints = [str(x or '').strip().lower() for x in (feedback.get('recent_next_stage_hints') or []) if str(x or '').strip()]
    target_surface_rationale = [str(x or '').strip().lower() for x in (feedback.get('recent_target_surface_rationale') or []) if str(x or '').strip()]
    next_family_hints = [str(x or '').strip().lower() for x in (feedback.get('recent_next_family_hints') or []) if str(x or '').strip()]
    progression_hints = top_progression_hints(
        family=str(next_family_hints[-1] if next_family_hints else ''),
        target_surface_signal=str(target_surface_rationale[-1] if target_surface_rationale else ''),
        next_stage=str(next_stage_hints[-1] if next_stage_hints else ''),
        limit=2,
    )
    progression_reconsult_tiers = [str(item.get('reconsult_tier') or '').strip().lower() for item in progression_hints if str(item.get('reconsult_tier') or '').strip()]
    quality = adaptive_quality_context(feedback)
    dead_end_heavy = bool(quality.get('dead_end_heavy', False))
    quality_structural = bool(quality.get('quality_structural', False))
    if max(promising_count, reconsult_worthy_recent) >= (threshold * 2) and not dead_end_heavy:
        return 'structural'
    degraded = int(feedback.get('degraded_hosts', 0) or 0)
    if degraded >= 3 and not dead_end_heavy:
        return 'structural'
    if int(feedback.get('planner_override_recent', 0) or 0) >= 3 and not dead_end_heavy:
        return 'structural'
    if (next_stage_hints.count('bounded_exploit_proof') >= max(2, threshold - 1) or next_stage_hints.count('state_transition_confirmation') >= max(2, threshold - 1)) and not dead_end_heavy:
        return 'structural'
    if 'structural' in progression_reconsult_tiers and not dead_end_heavy:
        return 'structural'
    if quality_structural and (adaptation_positive_recent >= max(1, threshold - 1) or reconsult_worthy_recent >= max(1, threshold - 1)):
        return 'structural'
    if int(feedback.get('high_redundancy_recent', 0) or 0) >= 3 or int(feedback.get('not_met_recent', 0) or 0) >= max(2, threshold) or dead_end_heavy:
        return 'light'
    if target_surface_rationale.count('authenticated_or_boundary_mapping') >= threshold or target_surface_rationale.count('artifact_capture') >= threshold:
        return 'light'
    if 'light' in progression_reconsult_tiers:
        return 'light'
    if max(promising_count, reconsult_worthy_recent, adaptation_positive_recent) >= threshold:
        return 'light'
    return ''
