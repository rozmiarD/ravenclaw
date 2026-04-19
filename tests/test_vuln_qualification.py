from engine.vuln_qualification import qualify, verdict_at_least


def test_policy_block_yields_none_or_weak():
    q = qualify(
        {
            "objective": "IDOR probe",
            "reason_code": "auditor_owner_approval_required",
            "signal_codes": ["authz_boundary_signal"],
            "summary_text": "Blocked by auditor/policy",
            "http_code": "403",
            "engine_status": "unknown",
            "auditor_decision": "owner_approval_required",
            "in_scope": True,
        }
    ).as_dict()
    assert q["verdict"] in {"none", "weak_signal"}
    assert q["disposition"] == "governance_blocked"


def test_signal_can_reach_probable_not_confirmed_without_controls():
    q = qualify(
        {
            "objective": "Run xss canary",
            "reason_code": "xss_reflection",
            "signal_codes": ["error_trace_signal", "authz_boundary_signal"],
            "summary_text": "<script>alert(1)</script> exception token leak",
            "http_code": "500",
            "engine_status": "success",
            "auditor_decision": "approve",
            "in_scope": True,
            "control_comparison_performed": False,
            "control_delta_observed": False,
        }
    ).as_dict()
    assert verdict_at_least(q["verdict"], "probable")
    assert q["verdict"] != "confirmed"


def test_early_boundary_context_promotes_to_followup_worthy_weak_signal() -> None:
    q = qualify(
        {
            "objective": "Map authz boundary in workflow transition",
            "reason_code": "authz_boundary_signal",
            "signal_codes": ["authz_boundary_signal"],
            "summary_text": "403 profile boundary transition artifact observed on control path",
            "task_family": "authz",
            "http_code": "403",
            "engine_status": "success",
            "auditor_decision": "approve",
            "in_scope": True,
            "control_comparison_performed": True,
            "control_delta_observed": False,
            "repeated_consistency": False,
            "force_auth_like_weak_on_http_controls": True,
        }
    ).as_dict()
    assert q["verdict"] == "weak_signal"
    assert q["confidence"] >= 0.45
    assert "early_boundary_context_promoted" in q["reason_code"]


def test_boundary_context_repeated_consistency_can_reach_probable() -> None:
    q = qualify(
        {
            "objective": "Confirm authz boundary in workflow transition",
            "reason_code": "authz_boundary_signal",
            "signal_codes": ["authz_boundary_signal", "state_transition_signal"],
            "summary_text": "403 on control path but repeated profile/order boundary transition artifact observed",
            "task_family": "authz",
            "http_code": "403",
            "engine_status": "success",
            "auditor_decision": "approve",
            "in_scope": True,
            "control_comparison_performed": True,
            "control_delta_observed": False,
            "repeated_consistency": True,
            "force_auth_like_weak_on_http_controls": True,
        }
    ).as_dict()
    assert q["verdict"] == "probable"
    assert q["confidence"] >= 0.6
    assert "boundary_context_promoted" in q["reason_code"]


def test_policy_block_still_does_not_promote_under_boundary_context() -> None:
    q = qualify(
        {
            "objective": "Confirm authz boundary in workflow transition",
            "reason_code": "auditor_owner_approval_required",
            "signal_codes": ["authz_boundary_signal", "state_transition_signal"],
            "summary_text": "403 profile boundary transition artifact observed",
            "task_family": "authz",
            "http_code": "403",
            "engine_status": "success",
            "auditor_decision": "owner_approval_required",
            "in_scope": True,
            "control_comparison_performed": True,
            "control_delta_observed": False,
            "repeated_consistency": True,
            "force_auth_like_weak_on_http_controls": True,
        }
    ).as_dict()
    assert q["verdict"] in {"none", "weak_signal"}
    assert q["disposition"] == "governance_blocked"


def test_workflow_boundary_context_can_promote_without_authz_specific_signal_tokens() -> None:
    q = qualify(
        {
            "objective": "Validate workflow state transition isolation",
            "reason_code": "workflow_control_path",
            "signal_codes": ["state_transition_signal"],
            "summary_text": "403 observed on workflow replay control path",
            "task_family": "workflow",
            "http_code": "403",
            "engine_status": "success",
            "auditor_decision": "approve",
            "in_scope": True,
            "control_comparison_performed": True,
            "control_delta_observed": False,
            "repeated_consistency": False,
            "actor_or_session_prerequisites": ["two user sessions", "stable order id"],
            "acceptance_checks": ["cross-actor state transition differential"],
            "force_auth_like_weak_on_http_controls": True,
        }
    ).as_dict()
    assert q["verdict"] == "weak_signal"
    assert q["confidence"] >= 0.45
    assert q["disposition"] == "standard"
    assert "early_boundary_context_promoted" in q["reason_code"]
