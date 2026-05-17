from govengine.contracts.evidence_policy import can_be_confirmed


def test_confirmed_requires_repro_and_controls():
    q = {
        "verdict": "confirmed",
        "false_positive_guards_passed": True,
        "observed_artifacts": {
            "control_comparison_performed": True,
            "control_delta_observed": True,
            "protocol": {"repro_pass": True},
        },
    }
    assert can_be_confirmed(q) is True


def test_confirmed_blocked_without_repro():
    q = {
        "verdict": "confirmed",
        "false_positive_guards_passed": True,
        "observed_artifacts": {
            "control_comparison_performed": True,
            "control_delta_observed": True,
            "protocol": {"repro_pass": False},
        },
    }
    assert can_be_confirmed(q) is False
