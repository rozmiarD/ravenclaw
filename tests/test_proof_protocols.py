from engine.proof_protocols import protocol_for


def test_idor_protocol_requires_controls_and_consistency():
    p = protocol_for(
        "idor",
        {
            "summary_text": "owner_id exposed",
            "signal_codes": ["authz_boundary_signal"],
            "control_comparison_performed": True,
            "control_delta_observed": True,
            "repeated_consistency": True,
        },
    ).as_dict()
    assert p["repro_pass"] is True


def test_xss_protocol_fails_without_consistency():
    p = protocol_for(
        "xss",
        {
            "summary_text": "<script>alert(1)</script>",
            "signal_codes": [],
            "control_comparison_performed": True,
            "control_delta_observed": True,
            "repeated_consistency": False,
        },
    ).as_dict()
    assert p["repro_pass"] is False
