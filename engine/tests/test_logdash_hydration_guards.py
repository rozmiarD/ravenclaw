from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / 'logdash' / 'templates'


def _read(name: str) -> str:
    return (TEMPLATES / name).read_text(encoding='utf-8')


def test_system_settings_starts_in_loading_gate_and_badge_state() -> None:
    text = _read('system_settings.html')
    assert '<body class="ui-loading">' in text
    assert 'id="systemHydrationGate"' in text
    assert 'id="systemSaveStateBadge" data-state="pending">loading<' in text
    assert "setSystemSaveState('pending','loading')" in text


def test_campaign_setup_starts_in_loading_gate_and_badge_state() -> None:
    text = _read('campaign_setup.html')
    assert '<body class="ui-loading">' in text
    assert 'id="campaignHydrationGate"' in text
    assert 'id="campaignSaveStateBadge" data-state="pending">loading<' in text
    assert "setCampaignSaveState('pending','loading')" in text


def test_owner_actions_uses_loading_gate_state_badge_and_slider_guard() -> None:
    text = _read('owner_actions.html')
    assert '<body class="ui-loading">' in text
    assert 'id="ownerHydrationGate"' in text
    assert 'id="ownerActionStateBadge" data-state="pending">loading<' in text
    assert 'document.activeElement===slider' in text
    assert "setOwnerActionState('pending','loading')" in text
