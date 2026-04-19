from __future__ import annotations

from typing import Any, Dict

DEFAULT_HIGH_LEVERAGE_PRECISION_FAMILIES = [
    "authz",
    "idor",
    "logic",
    "workflow",
    "state_transition",
    "input_tamper",
]
DEFAULT_DUAL_ACTION_ALLOWED_FAMILIES = ["authz", "idor", "logic", "workflow"]

PLAN_ADAPTATION_MODES = {"off", "balanced", "aggressive", "frozen"}
PLANNER_RECONSULT_MODES = {"off", "conservative", "balanced", "aggressive"}
FAMILY_DECAY_MODES = {"off", "light", "standard", "strong"}
WORKFLOW_ESCALATION_PROFILES = {"off", "conservative", "balanced", "aggressive"}
CONFIRM_JOB_PROFILES = {"off", "conservative", "standard", "aggressive"}
QUALIFICATION_THRESHOLDS = {"none", "weak_signal", "probable", "confirmed"}
QUALIFICATION_THRESHOLD_OPTIONS = QUALIFICATION_THRESHOLDS | {"custom"}

PIPELINE_FLAG_DEFAULTS: Dict[str, Any] = {
    "enable_analysis": True,
    "enable_light": True,
    "verbose_commands": False,
    "analysis_min_bytes": 32,
    "context_history": 5,
    "json_contract_retries": 1,
    "prompt_token_budget": 900,
    "auditor_prompt_token_budget": 900,
    "enable_followups": True,
    "workflow_escalation_profile": "aggressive",
    "qualification_shadow_workflow_bridge": True,
    "candidate_partial_followup_bridge": True,
    "weak_signal_positive_bridge": True,
    "evidence_bearing_followup_bridge": True,
    "early_precision_for_high_leverage_families": True,
    "high_leverage_precision_families": list(DEFAULT_HIGH_LEVERAGE_PRECISION_FAMILIES),
    "safe_dual_action_enabled": True,
    "dual_action_allowed_families": list(DEFAULT_DUAL_ACTION_ALLOWED_FAMILIES),
    "max_followups_per_target": 1,
    "followup_cooldown_sec": 900,
    "planner_reconsult_mode": "off",
    "planner_reconsult_on_high_signal": False,
    "planner_reconsult_min_interval_runs": 12,
    "planner_reconsult_signal_threshold": 15,
    "plan_adaptation_mode": "balanced",
    "dynamic_plan_adaptation": True,
    "freeze_plan_revision": False,
    "aggressive_adaptation": False,
    "family_lane_boost": [],
    "family_lane_suppress": [],
    "family_decay_mode": "standard",
    "family_decay_enabled": True,
    "family_decay_window_runs": 24,
    "family_decay_penalty": 0.12,
    "host_family_lane_boost": {},
    "host_family_lane_suppress": {},
    "experimental_payloads": False,
    "execution_mode": "normalized",
    "code000_streak_threshold": 3,
    "code000_session_cap": 5,
    "code000_cooldown_sec": 3600,
    "host_health_cooldown_sec": 900,
    "deep_budget_cap_per_host_family": 2,
    "precheck_burst_cooldown_threshold": 10,
    "precheck_burst_cooldown_sec": 300,
    "host_fail_streak_backoff_step_sec": 0.4,
    "host_fail_streak_backoff_cap_sec": 2.0,
    "transport_observation_cooldown_sec": 600,
    "http_403_streak_threshold": 4,
    "http_403_cooldown_sec": 1800,
    "code000_session_cooldown_sec": 86400,
    "autodiscover_deep_skip": True,
    "strict_deterministic": True,
    "qualification_mode": "shadow",
    "qualification_threshold": "probable",
    "qualification_promising_threshold": "probable",
    "qualification_followup_threshold": "probable",
    "confirm_jobs_profile": "standard",
    "enable_confirm_jobs": True,
    "max_confirm_jobs_per_target": 1,
    "confirm_job_cooldown_sec": 900,
    "max_confirm_jobs_total": 20,
    "max_confirm_jobs_per_class": 8,
    "out_of_scope_aggression_cap": 1,
    "out_of_scope_max_aggression": 1,
    "out_of_scope_allowed_aggression": 1,
    "policy_diag_logging": True,
    "force_auth_like_weak_on_http_controls": True,
    "queue_preemption_in_curated_loop": True,
}


def _normalize_bool(value: Any, default: bool = False) -> bool:
    return bool(default if value is None else value)


def _normalize_str_list(value: Any, default: list[str] | None = None) -> list[str]:
    if not isinstance(value, list):
        return list(default or [])
    out: list[str] = []
    for item in value:
        text = str(item or "").strip().lower()
        if text:
            out.append(text)
    return out


def _normalize_family_map(value: Any) -> dict[str, list[str]]:
    if not isinstance(value, dict):
        return {}
    out: dict[str, list[str]] = {}
    for key, raw in value.items():
        host = str(key or "").strip().lower()
        if not host:
            continue
        out[host] = _normalize_str_list(raw)
    return out


def _derive_plan_adaptation_mode(raw: Dict[str, Any]) -> str:
    if bool(raw.get("freeze_plan_revision", False)):
        return "frozen"
    if not bool(raw.get("dynamic_plan_adaptation", True)):
        return "off"
    return "aggressive" if bool(raw.get("aggressive_adaptation", False)) else "balanced"


def _apply_plan_adaptation_mode(out: Dict[str, Any], mode: str) -> None:
    mode = mode if mode in PLAN_ADAPTATION_MODES else _derive_plan_adaptation_mode(out)
    out["plan_adaptation_mode"] = mode
    if mode == "frozen":
        out["dynamic_plan_adaptation"] = True
        out["aggressive_adaptation"] = False
        out["freeze_plan_revision"] = True
    elif mode == "off":
        out["dynamic_plan_adaptation"] = False
        out["aggressive_adaptation"] = False
        out["freeze_plan_revision"] = False
    elif mode == "aggressive":
        out["dynamic_plan_adaptation"] = True
        out["aggressive_adaptation"] = True
        out["freeze_plan_revision"] = False
    else:
        out["dynamic_plan_adaptation"] = True
        out["aggressive_adaptation"] = False
        out["freeze_plan_revision"] = False


def _derive_planner_reconsult_mode(raw: Dict[str, Any]) -> str:
    if not bool(raw.get("planner_reconsult_on_high_signal", False)):
        return "off"
    interval = int(raw.get("planner_reconsult_min_interval_runs", 12) or 12)
    threshold = int(raw.get("planner_reconsult_signal_threshold", 15) or 15)
    if interval <= 6 or threshold <= 8:
        return "aggressive"
    if interval <= 12 or threshold <= 12:
        return "balanced"
    return "conservative"


def _apply_planner_reconsult_mode(out: Dict[str, Any], mode: str) -> None:
    mode = mode if mode in PLANNER_RECONSULT_MODES else _derive_planner_reconsult_mode(out)
    out["planner_reconsult_mode"] = mode
    if mode == "off":
        out["planner_reconsult_on_high_signal"] = False
        out["planner_reconsult_min_interval_runs"] = 12
        out["planner_reconsult_signal_threshold"] = 15
    elif mode == "conservative":
        out["planner_reconsult_on_high_signal"] = True
        out["planner_reconsult_min_interval_runs"] = 18
        out["planner_reconsult_signal_threshold"] = 15
    elif mode == "aggressive":
        out["planner_reconsult_on_high_signal"] = True
        out["planner_reconsult_min_interval_runs"] = 6
        out["planner_reconsult_signal_threshold"] = 8
    else:
        out["planner_reconsult_on_high_signal"] = True
        out["planner_reconsult_min_interval_runs"] = 12
        out["planner_reconsult_signal_threshold"] = 12


def _derive_family_decay_mode(raw: Dict[str, Any]) -> str:
    if not bool(raw.get("family_decay_enabled", True)):
        return "off"
    window = int(raw.get("family_decay_window_runs", 24) or 24)
    penalty = float(raw.get("family_decay_penalty", 0.12) or 0.12)
    if penalty >= 0.18 or window <= 12:
        return "strong"
    if penalty <= 0.08 or window >= 36:
        return "light"
    return "standard"


def _apply_family_decay_mode(out: Dict[str, Any], mode: str) -> None:
    mode = mode if mode in FAMILY_DECAY_MODES else _derive_family_decay_mode(out)
    out["family_decay_mode"] = mode
    if mode == "off":
        out["family_decay_enabled"] = False
        out["family_decay_window_runs"] = 24
        out["family_decay_penalty"] = 0.12
    elif mode == "light":
        out["family_decay_enabled"] = True
        out["family_decay_window_runs"] = 36
        out["family_decay_penalty"] = 0.08
    elif mode == "strong":
        out["family_decay_enabled"] = True
        out["family_decay_window_runs"] = 12
        out["family_decay_penalty"] = 0.18
    else:
        out["family_decay_enabled"] = True
        out["family_decay_window_runs"] = 24
        out["family_decay_penalty"] = 0.12


def _derive_workflow_escalation_profile(raw: Dict[str, Any]) -> str:
    if not bool(raw.get("enable_followups", True)):
        return "off"
    score = sum(
        1
        for key in (
            "qualification_shadow_workflow_bridge",
            "candidate_partial_followup_bridge",
            "weak_signal_positive_bridge",
            "evidence_bearing_followup_bridge",
            "early_precision_for_high_leverage_families",
            "safe_dual_action_enabled",
        )
        if bool(raw.get(key, False))
    )
    max_followups = int(raw.get("max_followups_per_target", 1) or 1)
    followup_cooldown = int(raw.get("followup_cooldown_sec", 900) or 900)
    if score >= 5 or max_followups >= 4 or followup_cooldown <= 300:
        return "aggressive"
    if score >= 3 or max_followups >= 2 or followup_cooldown <= 900:
        return "balanced"
    return "conservative"


def _apply_workflow_escalation_profile(out: Dict[str, Any], profile: str) -> None:
    profile = profile if profile in WORKFLOW_ESCALATION_PROFILES else _derive_workflow_escalation_profile(out)
    out["workflow_escalation_profile"] = profile
    if profile == "off":
        out["enable_followups"] = False
        out["qualification_shadow_workflow_bridge"] = False
        out["candidate_partial_followup_bridge"] = False
        out["weak_signal_positive_bridge"] = False
        out["evidence_bearing_followup_bridge"] = False
        out["early_precision_for_high_leverage_families"] = False
        out["safe_dual_action_enabled"] = False
        out["max_followups_per_target"] = 1
        out["followup_cooldown_sec"] = 1800
    elif profile == "conservative":
        out["enable_followups"] = True
        out["qualification_shadow_workflow_bridge"] = True
        out["candidate_partial_followup_bridge"] = False
        out["weak_signal_positive_bridge"] = False
        out["evidence_bearing_followup_bridge"] = False
        out["early_precision_for_high_leverage_families"] = False
        out["safe_dual_action_enabled"] = False
        out["max_followups_per_target"] = 1
        out["followup_cooldown_sec"] = 1800
    elif profile == "balanced":
        out["enable_followups"] = True
        out["qualification_shadow_workflow_bridge"] = True
        out["candidate_partial_followup_bridge"] = True
        out["weak_signal_positive_bridge"] = False
        out["evidence_bearing_followup_bridge"] = True
        out["early_precision_for_high_leverage_families"] = True
        out["safe_dual_action_enabled"] = True
        out["max_followups_per_target"] = 2
        out["followup_cooldown_sec"] = 900
    else:
        out["enable_followups"] = True
        out["qualification_shadow_workflow_bridge"] = True
        out["candidate_partial_followup_bridge"] = True
        out["weak_signal_positive_bridge"] = True
        out["evidence_bearing_followup_bridge"] = True
        out["early_precision_for_high_leverage_families"] = True
        out["safe_dual_action_enabled"] = True
        out["max_followups_per_target"] = 4
        out["followup_cooldown_sec"] = 180


def _derive_confirm_jobs_profile(raw: Dict[str, Any]) -> str:
    if not bool(raw.get("enable_confirm_jobs", True)):
        return "off"
    per_target = int(raw.get("max_confirm_jobs_per_target", 1) or 1)
    cooldown = int(raw.get("confirm_job_cooldown_sec", 900) or 900)
    total = int(raw.get("max_confirm_jobs_total", 20) or 20)
    per_class = int(raw.get("max_confirm_jobs_per_class", 8) or 8)
    if per_target >= 2 or cooldown <= 600 or total >= 40 or per_class >= 12:
        return "aggressive"
    if cooldown >= 1800 or total <= 10 or per_class <= 4:
        return "conservative"
    return "standard"


def _apply_confirm_jobs_profile(out: Dict[str, Any], profile: str) -> None:
    profile = profile if profile in CONFIRM_JOB_PROFILES else _derive_confirm_jobs_profile(out)
    out["confirm_jobs_profile"] = profile
    if profile == "off":
        out["enable_confirm_jobs"] = False
        out["max_confirm_jobs_per_target"] = 1
        out["confirm_job_cooldown_sec"] = 1800
        out["max_confirm_jobs_total"] = 10
        out["max_confirm_jobs_per_class"] = 4
    elif profile == "conservative":
        out["enable_confirm_jobs"] = True
        out["max_confirm_jobs_per_target"] = 1
        out["confirm_job_cooldown_sec"] = 1800
        out["max_confirm_jobs_total"] = 10
        out["max_confirm_jobs_per_class"] = 4
    elif profile == "aggressive":
        out["enable_confirm_jobs"] = True
        out["max_confirm_jobs_per_target"] = 2
        out["confirm_job_cooldown_sec"] = 300
        out["max_confirm_jobs_total"] = 40
        out["max_confirm_jobs_per_class"] = 12
    else:
        out["enable_confirm_jobs"] = True
        out["max_confirm_jobs_per_target"] = 1
        out["confirm_job_cooldown_sec"] = 900
        out["max_confirm_jobs_total"] = 20
        out["max_confirm_jobs_per_class"] = 8


def _derive_qualification_threshold(raw: Dict[str, Any]) -> str:
    promising = str(raw.get("qualification_promising_threshold", "probable") or "probable").strip().lower()
    followup = str(raw.get("qualification_followup_threshold", "probable") or "probable").strip().lower()
    if promising == followup and promising in QUALIFICATION_THRESHOLDS:
        return promising
    return "custom"


def _apply_qualification_threshold(out: Dict[str, Any], threshold: str) -> None:
    threshold = threshold if threshold in QUALIFICATION_THRESHOLD_OPTIONS else _derive_qualification_threshold(out)
    out["qualification_threshold"] = threshold
    if threshold in QUALIFICATION_THRESHOLDS:
        out["qualification_promising_threshold"] = threshold
        out["qualification_followup_threshold"] = threshold


def _derive_out_of_scope_aggression_cap(raw: Dict[str, Any]) -> int:
    if raw.get("out_of_scope_aggression_cap") not in (None, ""):
        try:
            return int(raw.get("out_of_scope_aggression_cap") or 1)
        except Exception:
            pass
    try:
        max_cap = int(raw.get("out_of_scope_max_aggression", 1) or 1)
    except Exception:
        max_cap = 1
    try:
        allowed_cap = int(raw.get("out_of_scope_allowed_aggression", 1) or 1)
    except Exception:
        allowed_cap = 1
    return min(max_cap, allowed_cap)


def _apply_out_of_scope_aggression_cap(out: Dict[str, Any], cap: int) -> None:
    cap = max(1, min(10, int(cap or 1)))
    out["out_of_scope_aggression_cap"] = cap
    out["out_of_scope_max_aggression"] = cap
    out["out_of_scope_allowed_aggression"] = cap


def normalize_pipeline_flags(payload: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(PIPELINE_FLAG_DEFAULTS)
    merged.update({k: payload.get(k, v) for k, v in PIPELINE_FLAG_DEFAULTS.items()})
    out = dict(merged)

    out["enable_analysis"] = _normalize_bool(out.get("enable_analysis"), True)
    out["enable_light"] = _normalize_bool(out.get("enable_light"), True)
    out["verbose_commands"] = _normalize_bool(out.get("verbose_commands"), False)
    out["experimental_payloads"] = _normalize_bool(out.get("experimental_payloads"), False)
    out["policy_diag_logging"] = _normalize_bool(out.get("policy_diag_logging"), True)
    out["force_auth_like_weak_on_http_controls"] = _normalize_bool(out.get("force_auth_like_weak_on_http_controls"), True)
    out["queue_preemption_in_curated_loop"] = _normalize_bool(out.get("queue_preemption_in_curated_loop"), True)
    out["autodiscover_deep_skip"] = _normalize_bool(out.get("autodiscover_deep_skip"), True)
    out["strict_deterministic"] = _normalize_bool(out.get("strict_deterministic"), True)

    out["analysis_min_bytes"] = max(0, min(2048, int(out.get("analysis_min_bytes", 32) or 32)))
    out["context_history"] = max(1, min(20, int(out.get("context_history", 5) or 5)))
    out["json_contract_retries"] = max(0, min(3, int(out.get("json_contract_retries", 1) or 1)))
    out["prompt_token_budget"] = max(0, min(1250, int(out.get("prompt_token_budget", 350) or 0)))
    out["auditor_prompt_token_budget"] = max(0, min(2000, int(out.get("auditor_prompt_token_budget", 900) or 0)))
    out["max_followups_per_target"] = max(0, min(20, int(out.get("max_followups_per_target", 1) or 1)))
    out["code000_streak_threshold"] = max(1, min(10, int(out.get("code000_streak_threshold", 3) or 3)))
    out["code000_session_cap"] = max(1, min(20, int(out.get("code000_session_cap", 5) or 5)))
    out["code000_cooldown_sec"] = max(60, min(86400, int(out.get("code000_cooldown_sec", 3600) or 3600)))
    out["host_health_cooldown_sec"] = max(60, min(7200, int(out.get("host_health_cooldown_sec", 900) or 900)))
    deep_budget_cap = out.get("deep_budget_cap_per_host_family", 2)
    if deep_budget_cap is None:
        deep_budget_cap = 2
    out["deep_budget_cap_per_host_family"] = max(1, min(8, int(deep_budget_cap)))
    burst_threshold = out.get("precheck_burst_cooldown_threshold", 10)
    if burst_threshold is None:
        burst_threshold = 10
    out["precheck_burst_cooldown_threshold"] = max(2, min(50, int(burst_threshold)))
    burst_cooldown = out.get("precheck_burst_cooldown_sec", 300)
    if burst_cooldown is None:
        burst_cooldown = 300
    out["precheck_burst_cooldown_sec"] = max(60, min(3600, int(burst_cooldown)))
    backoff_step = out.get("host_fail_streak_backoff_step_sec", 0.4)
    if backoff_step is None:
        backoff_step = 0.4
    out["host_fail_streak_backoff_step_sec"] = max(0.0, min(5.0, float(backoff_step)))
    backoff_cap = out.get("host_fail_streak_backoff_cap_sec", 2.0)
    if backoff_cap is None:
        backoff_cap = 2.0
    out["host_fail_streak_backoff_cap_sec"] = max(0.0, min(10.0, float(backoff_cap)))
    if out["host_fail_streak_backoff_cap_sec"] < out["host_fail_streak_backoff_step_sec"]:
        out["host_fail_streak_backoff_cap_sec"] = out["host_fail_streak_backoff_step_sec"]
    transport_obs_cooldown = out.get("transport_observation_cooldown_sec", 600)
    if transport_obs_cooldown is None:
        transport_obs_cooldown = 600
    out["transport_observation_cooldown_sec"] = max(60, min(3600, int(transport_obs_cooldown)))
    http_403_threshold = out.get("http_403_streak_threshold", 4)
    if http_403_threshold is None:
        http_403_threshold = 4
    out["http_403_streak_threshold"] = max(1, min(20, int(http_403_threshold)))
    http_403_cooldown = out.get("http_403_cooldown_sec", 1800)
    if http_403_cooldown is None:
        http_403_cooldown = 1800
    out["http_403_cooldown_sec"] = max(60, min(86400, int(http_403_cooldown)))
    code000_session_cooldown = out.get("code000_session_cooldown_sec", 86400)
    if code000_session_cooldown is None:
        code000_session_cooldown = 86400
    out["code000_session_cooldown_sec"] = max(300, min(172800, int(code000_session_cooldown)))

    out["execution_mode"] = str(out.get("execution_mode", "normalized") or "normalized").strip().lower()
    if out["execution_mode"] not in {"normalized", "faithful"}:
        out["execution_mode"] = "normalized"
    out["qualification_mode"] = str(out.get("qualification_mode", "shadow") or "shadow").strip().lower()
    if out["qualification_mode"] not in {"shadow", "enforce"}:
        out["qualification_mode"] = "shadow"

    out["family_lane_boost"] = _normalize_str_list(out.get("family_lane_boost"))
    out["family_lane_suppress"] = _normalize_str_list(out.get("family_lane_suppress"))
    out["host_family_lane_boost"] = _normalize_family_map(out.get("host_family_lane_boost"))
    out["host_family_lane_suppress"] = _normalize_family_map(out.get("host_family_lane_suppress"))
    out["high_leverage_precision_families"] = _normalize_str_list(out.get("high_leverage_precision_families"), DEFAULT_HIGH_LEVERAGE_PRECISION_FAMILIES)
    out["dual_action_allowed_families"] = _normalize_str_list(out.get("dual_action_allowed_families"), DEFAULT_DUAL_ACTION_ALLOWED_FAMILIES)

    plan_adaptation_mode = str(payload.get("plan_adaptation_mode") or "").strip().lower() if "plan_adaptation_mode" in payload else _derive_plan_adaptation_mode(out)
    out["plan_adaptation_mode"] = plan_adaptation_mode
    _apply_plan_adaptation_mode(out, plan_adaptation_mode)

    out["planner_reconsult_on_high_signal"] = _normalize_bool(out.get("planner_reconsult_on_high_signal"), False)
    out["planner_reconsult_min_interval_runs"] = max(1, min(200, int(out.get("planner_reconsult_min_interval_runs", 12) or 12)))
    out["planner_reconsult_signal_threshold"] = max(1, min(20, int(out.get("planner_reconsult_signal_threshold", 15) or 15)))
    planner_reconsult_mode = str(payload.get("planner_reconsult_mode") or "").strip().lower() if "planner_reconsult_mode" in payload else _derive_planner_reconsult_mode(out)
    out["planner_reconsult_mode"] = planner_reconsult_mode
    _apply_planner_reconsult_mode(out, planner_reconsult_mode)

    out["family_decay_enabled"] = _normalize_bool(out.get("family_decay_enabled"), True)
    out["family_decay_window_runs"] = max(6, min(120, int(out.get("family_decay_window_runs", 24) or 24)))
    out["family_decay_penalty"] = max(0.0, min(0.5, float(out.get("family_decay_penalty", 0.12) or 0.12)))
    family_decay_mode = str(payload.get("family_decay_mode") or "").strip().lower() if "family_decay_mode" in payload else _derive_family_decay_mode(out)
    out["family_decay_mode"] = family_decay_mode
    _apply_family_decay_mode(out, family_decay_mode)

    workflow_escalation_profile = str(payload.get("workflow_escalation_profile") or "").strip().lower() if "workflow_escalation_profile" in payload else _derive_workflow_escalation_profile(out)
    out["workflow_escalation_profile"] = workflow_escalation_profile
    _apply_workflow_escalation_profile(out, workflow_escalation_profile)
    out["enable_followups"] = _normalize_bool(out.get("enable_followups"), True)
    out["qualification_shadow_workflow_bridge"] = _normalize_bool(out.get("qualification_shadow_workflow_bridge"), True)
    out["candidate_partial_followup_bridge"] = _normalize_bool(out.get("candidate_partial_followup_bridge"), True)
    out["weak_signal_positive_bridge"] = _normalize_bool(out.get("weak_signal_positive_bridge"), True)
    out["evidence_bearing_followup_bridge"] = _normalize_bool(out.get("evidence_bearing_followup_bridge"), True)
    out["early_precision_for_high_leverage_families"] = _normalize_bool(out.get("early_precision_for_high_leverage_families"), True)
    out["safe_dual_action_enabled"] = _normalize_bool(out.get("safe_dual_action_enabled"), True)

    out["enable_confirm_jobs"] = _normalize_bool(out.get("enable_confirm_jobs"), True)
    out["max_confirm_jobs_per_target"] = max(0, min(5, int(out.get("max_confirm_jobs_per_target", 1) or 1)))
    out["confirm_job_cooldown_sec"] = max(60, min(7200, int(out.get("confirm_job_cooldown_sec", 900) or 900)))
    out["max_confirm_jobs_total"] = max(1, min(200, int(out.get("max_confirm_jobs_total", 20) or 20)))
    out["max_confirm_jobs_per_class"] = max(1, min(50, int(out.get("max_confirm_jobs_per_class", 8) or 8)))
    confirm_jobs_profile = str(payload.get("confirm_jobs_profile") or "").strip().lower() if "confirm_jobs_profile" in payload else _derive_confirm_jobs_profile(out)
    out["confirm_jobs_profile"] = confirm_jobs_profile
    _apply_confirm_jobs_profile(out, confirm_jobs_profile)

    qpt = str(out.get("qualification_promising_threshold", "probable") or "probable").strip().lower()
    qft = str(out.get("qualification_followup_threshold", "probable") or "probable").strip().lower()
    out["qualification_promising_threshold"] = qpt if qpt in QUALIFICATION_THRESHOLDS else "probable"
    out["qualification_followup_threshold"] = qft if qft in QUALIFICATION_THRESHOLDS else "probable"
    qualification_threshold = str(payload.get("qualification_threshold") or "").strip().lower() if "qualification_threshold" in payload else _derive_qualification_threshold(out)
    out["qualification_threshold"] = qualification_threshold
    _apply_qualification_threshold(out, qualification_threshold)

    out_of_scope_aggression_cap = _derive_out_of_scope_aggression_cap(payload if "out_of_scope_aggression_cap" not in payload else out)
    _apply_out_of_scope_aggression_cap(out, out_of_scope_aggression_cap)

    return out
