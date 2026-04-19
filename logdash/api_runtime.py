from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from flask import Flask, jsonify

from context_contract import require_ctx

ROOT = Path(__file__).resolve().parents[1] / 'engine'
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from json_state_io import safe_load_json_object


_RUNTIME_API_CTX_KEYS = (
    "STATE",
    "refresh_runtime_state",
    "load_agent_models",
    "selected_campaign_key",
    "load_runtime_state",
    "load_runtime_snapshot",
    "load_pipeline_config",
    "save_pipeline_config",
    "pipeline_config_meta",
    "selected_runtime_snapshot_view",
    "build_agents_status_payload",
    "build_selected_campaign_projection",
    "load_pipeline_config_effective_posture",
)


def register_runtime_api(app: Flask, ctx: dict[str, Any]) -> None:
    ctx = require_ctx(ctx, *_RUNTIME_API_CTX_KEYS)
    STATE = ctx["STATE"]
    refresh_runtime_state = ctx["refresh_runtime_state"]
    load_agent_models = ctx["load_agent_models"]
    selected_campaign_key = ctx["selected_campaign_key"]
    load_runtime_state = ctx["load_runtime_state"]
    load_runtime_snapshot = ctx["load_runtime_snapshot"]
    load_pipeline_config = ctx["load_pipeline_config"]
    save_pipeline_config = ctx["save_pipeline_config"]
    pipeline_config_meta = ctx["pipeline_config_meta"]
    selected_runtime_snapshot_view = ctx["selected_runtime_snapshot_view"]
    build_agents_status_payload = ctx["build_agents_status_payload"]
    build_selected_campaign_projection = ctx["build_selected_campaign_projection"]
    load_pipeline_config_effective_posture = ctx["load_pipeline_config_effective_posture"]

    def _selected_snapshot_sections() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
        runtime = load_runtime_state()
        selected_view = selected_runtime_snapshot_view(runtime, selected_campaign_key())
        current = build_selected_campaign_projection(runtime, selected_view, STATE)
        snap_campaign = current.get('snap_campaign') if isinstance(current.get('snap_campaign'), dict) else {}
        snap_plan = current.get('snap_plan') if isinstance(current.get('snap_plan'), dict) else {}
        snap_latest = current.get('snap_latest') if isinstance(current.get('snap_latest'), dict) else {}
        return runtime, snap_campaign, snap_plan, snap_latest

    @app.route("/api/agents-status")
    def api_agents_status():
        refresh_runtime_state()
        runtime, snap_campaign, snap_plan, snap_latest = _selected_snapshot_sections()
        model_map = load_agent_models()
        return jsonify(build_agents_status_payload(
            state=STATE,
            runtime=runtime,
            selected_campaign_key=str(selected_campaign_key() or ''),
            model_map=model_map,
            snap_campaign=snap_campaign,
            snap_plan=snap_plan,
            snap_latest=snap_latest,
        ))

    @app.route("/api/pipeline-config")
    def api_pipeline_config_get():
        return jsonify(load_pipeline_config())

    @app.route("/api/pipeline-config", methods=["POST"])
    def api_pipeline_config_post():
        from flask import request
        data = request.get_json(silent=True) or {}
        return jsonify(save_pipeline_config(data))

    @app.route("/api/pipeline-config/meta")
    def api_pipeline_config_meta():
        meta = pipeline_config_meta()
        effective_posture = load_pipeline_config_effective_posture()
        return jsonify({
            "profile": "default",
            "schema_version": 1,
            "schema_path": "/api/pipeline-config/schema",
            "ui_routes": {
                "system_settings": "/system-settings",
                "campaign_setup": "/campaign-setup",
                "owner_actions": "/owner-actions",
            },
            "effective_posture": effective_posture,
            **meta,
        })

    @app.route("/api/pipeline-config/schema")
    def api_pipeline_config_schema():
        manifest, _meta = safe_load_json_object(
            Path(__file__).resolve().parents[1] / 'engine' / 'feature_flags_manifest.json',
            {},
            description='feature_flags_manifest',
        )
        system_core = [
            "enable_analysis", "enable_light", "execution_mode", "qualification_mode", "qualification_threshold",
            "plan_adaptation_mode", "planner_reconsult_mode", "workflow_escalation_profile", "confirm_jobs_profile", "family_decay_mode",
            "out_of_scope_aggression_cap",
        ]
        system_expert = [
            "verbose_commands", "experimental_payloads", "analysis_min_bytes", "context_history", "json_contract_retries",
            "prompt_token_budget", "auditor_prompt_token_budget", "enable_followups", "max_followups_per_target",
            "planner_reconsult_on_high_signal", "planner_reconsult_min_interval_runs", "planner_reconsult_signal_threshold",
            "dynamic_plan_adaptation", "freeze_plan_revision", "aggressive_adaptation", "family_lane_boost", "family_lane_suppress",
            "family_decay_enabled", "family_decay_window_runs", "family_decay_penalty", "host_family_lane_boost", "host_family_lane_suppress",
            "enable_confirm_jobs", "strict_deterministic", "qualification_shadow_workflow_bridge", "candidate_partial_followup_bridge",
            "weak_signal_positive_bridge", "evidence_bearing_followup_bridge", "early_precision_for_high_leverage_families",
            "high_leverage_precision_families", "max_confirm_jobs_per_target", "confirm_job_cooldown_sec", "max_confirm_jobs_total",
            "max_confirm_jobs_per_class", "autodiscover_deep_skip", "policy_diag_logging", "force_auth_like_weak_on_http_controls",
            "queue_preemption_in_curated_loop", "qualification_promising_threshold", "qualification_followup_threshold",
            "code000_streak_threshold", "code000_session_cap", "code000_cooldown_sec",
        ]
        campaign_scoped = [
            "credentials_required", "allow_auth_header", "allow_cookie_header", "allow_basic_auth",
            "bug_bounty_username", "test_account_email", "request_decoration", "max_runs", "target_load_limit", "time_budget_min", "retry_policy",
        ]
        hidden_compat = [
            "safe_dual_action_enabled", "dual_action_allowed_families", "out_of_scope_max_aggression", "out_of_scope_allowed_aggression",
        ]
        return jsonify({
            "schema_version": 1,
            "ui_routes": {
                "system_settings": "/system-settings",
                "campaign_setup": "/campaign-setup",
                "owner_actions": "/owner-actions",
            },
            "counts": {
                "system_core": len(system_core),
                "system_expert": len(system_expert),
                "campaign_scoped": len(campaign_scoped),
                "hidden_compat": len(hidden_compat),
            },
            "system_core": system_core,
            "system_expert": system_expert,
            "campaign_scoped": campaign_scoped,
            "hidden_compat": hidden_compat,
            "removed": ["enable_contextual_reeval"],
            "manifest": manifest,
        })
