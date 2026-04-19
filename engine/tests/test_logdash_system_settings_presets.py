from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / 'logdash' / 'templates' / 'system_settings.html'


def test_system_settings_exposes_pipeline_preset_dropdown_and_hooks() -> None:
    text = TEMPLATE.read_text(encoding='utf-8')
    assert 'id="pipelinePresetSelect"' in text
    assert 'exploratory_efficient' in text
    assert 'exploratory_max' in text
    assert 'confirmation_heavy' in text
    assert 'id="pipelinePresetDesc"' in text
    assert 'id="pipelinePresetBadge"' in text
    assert 'id="pipelinePresetPersistedBadge"' in text
    assert 'const PIPELINE_PRESETS=' in text
    assert 'function detectMatchingPreset(cfg)' in text
    assert 'function applyPreset(key)' in text
    assert "$('pipelinePresetSelect').onchange" in text


def test_system_settings_preset_labels_and_custom_mode_are_present() -> None:
    text = TEMPLATE.read_text(encoding='utf-8')
    assert 'exploratory-efficient' in text
    assert 'exploratory-max' in text
    assert 'confirmation-heavy' in text
    assert 'preset: loading' in text
    assert 'persisted: loading' in text
    assert "return 'custom';" in text


def test_system_settings_manual_text_inputs_reflect_custom_preset_state_immediately() -> None:
    text = TEMPLATE.read_text(encoding='utf-8')
    assert "$('familyLaneBoostInput').oninput=()=>{ draft.family_lane_boost" in text
    assert "$('familyLaneSuppressInput').oninput=()=>{ draft.family_lane_suppress" in text
    assert "$('highLeveragePrecisionFamiliesInput').oninput=()=>{ draft.high_leverage_precision_families" in text
    assert "$('hostFamilyLaneBoostInput').oninput=()=>{ const v=safeJsonParse('hostFamilyLaneBoostInput'); if(v!==null){ draft.host_family_lane_boost=v; dirty=true; reflect(); savePipelineNow(); }" in text
    assert "$('hostFamilyLaneSuppressInput').oninput=()=>{ const v=safeJsonParse('hostFamilyLaneSuppressInput'); if(v!==null){ draft.host_family_lane_suppress=v; dirty=true; reflect(); savePipelineNow(); }" in text
    assert 'const persistedBadge=$(\'pipelinePresetPersistedBadge\');' in text
    assert 'persistedBadge.textContent = `persisted: ${persistedLabel}`;' in text
