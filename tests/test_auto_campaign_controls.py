from engine.auto_campaign_controls import derive_control_target


def test_derive_control_target_dedup_and_neutralize():
    t = "https://example.com/api?amount=1&amount=2&role=admin&enabled=true"
    c = derive_control_target(t)
    assert "amount=0" in c or "amount=1" in c
    assert c.count("amount=") == 1
    assert "role=user" in c
    assert "enabled=false" in c
