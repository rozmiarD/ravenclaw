from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN_TEMPLATE = ROOT / 'logdash' / 'templates' / 'campaign_setup.html'
API_PLANNER = ROOT / 'logdash' / 'api_planner.py'
API_SUPPLEMENTAL = ROOT / 'logdash' / 'api_supplemental.py'
RUN_PIPELINE = ROOT / 'engine' / 'run_pipeline.py'
AUTO_RUNNER = ROOT / 'engine' / 'auto_campaign_runner.py'
RUNTIME_RUNNER_BOOTSTRAP = ROOT / 'engine' / 'runtime_runner_bootstrap.py'


def test_campaign_setup_persists_scope_path_and_guards_active_editing() -> None:
    text = CAMPAIGN_TEMPLATE.read_text(encoding='utf-8')
    assert 'id="scopeTxtInput" type="text" list="scopeTxtSuggestions"' in text
    assert 'id="llmInterpret"' in text
    assert 'Planner mode' not in text
    assert 'id="scopeTxtSuggestions"' in text
    assert 'async function refreshScopeSuggestions(selectedValue=' in text
    assert "await refreshScopeSuggestions(p.scope_txt||$('scopeTxtInput')?.value||'');" in text
    assert "$('scopeTxtInput').onfocus=async()" in text
    assert 'async function persistScopeSelection()' in text
    assert "document.activeElement !== $('scopeTxtInput')" in text
    assert "$('scopeTxtInput').onchange=async()" in text
    assert "$('scopeTxtInput').onblur=async()" in text
    assert "if(e.key==='Enter')" in text
    assert 'await persistScopeSelection();' in text
    assert "llm_interpret: $('llmInterpret')?.value === 'true'" in text
    assert "flags:{homelab:false, llm_interpret:$('llmInterpret')?.value === 'true'}" in text
    assert 'const targets=Number(c.planner_scope_targets ?? p.planner_scope_targets ?? plan.target_count ?? plan.input_total ?? snapPlan.target_count ?? snapPlan.input_total ?? 0);' in text
    assert 'const tasks=Number(c.prepared_attacks ?? p.prepared_attacks ?? plan.prepared_attacks ?? plan.generated ?? snapPlan.prepared_attacks ?? snapPlan.generated ?? 0);' in text
    assert 'id="credentialsStatusBadge"' in text
    assert 'id="credentialsStatusDetail"' in text
    assert "const credStatus = String(c.credentials_status || (cred.credentials_required ? 'INCOMPLETE' : 'ANONYMOUS'));" in text
    assert "$('credentialsStatusDetail').textContent = c.credentials_status_detail || '-';" in text
    assert 'async function loadCampaigns(preferredKey=null)' in text
    assert "const current=String(preferredKey||sel?.value||((state&&state.selected_campaign_key)||''));" in text
    assert "state.selected_campaign_key = d.selected_campaign_key;" in text
    assert "const run=await runPlanner();" in text
    assert "const campaignKey=run.selected_campaign_key||$('plannerCampaignSelect').value||state.selected_campaign_key||null;" in text
    assert 'await loadCampaigns(campaignKey);' in text
    assert 'await approvePlan(campaignKey);' in text
    assert 'await generatePlan(campaignKey);' in text


def test_api_planner_selection_run_and_scope_files_support_scope_txt() -> None:
    text = API_PLANNER.read_text(encoding='utf-8')
    supplemental = API_SUPPLEMENTAL.read_text(encoding='utf-8')
    assert 'def _normalize_scope_txt_for_ui(scope_txt: str | None) -> str:' in text
    assert '@app.route("/api/planner/scope-files")' in text
    assert 'for path in sorted(p for p in SCOPE_DIR.rglob' in text
    assert 'ui["scope_txt"] = _normalize_scope_txt_for_ui(data.get("scope_txt"))' in text
    assert 'ui["scope_txt"] = _normalize_scope_txt_for_ui(str(data.get("scope_txt") or str(scope_path)))' in text
    assert '"scope_txt": str((ui or {}).get("scope_txt") or "scope/scope.txt")' in text
    assert 'ui["llm_interpret"] = _ui_llm_interpret_value(data, ui)' in text
    assert 'if \'llm_interpret\' in data:' in text
    assert '"llm_interpret": bool((ui or {}).get(\'llm_interpret\', False))' in text
    assert 'def _campaign_key_from_planner_result(parsed: dict[str, Any] | None) -> str:' in text
    assert 'selected_key = _campaign_key_from_planner_result(parsed)' in text
    assert 'data.get("campaign_key") or selected_campaign_key() or _latest_campaign_key()' in text
    assert 'entry_{i}_target_broadens_exact_scope' in text
    assert 'def _selected_campaign_plan_counts() -> tuple[int, int]:' in text
    assert 'if not selected_key:' in text
    assert 'if str(snap_campaign.get(\'campaign_key\') or \'\').strip() == selected_key:' in text
    assert 'def _ensure_campaign_credential_defaults(selected_key: str | None = None) -> tuple[dict[str, Any], dict[str, Any]]:' in supplemental
    assert "'credentials_status': cred_status" in supplemental
    assert "selected_key = str(request.args.get('selected_campaign_key') or selected_campaign_key() or '').strip()" in supplemental


def test_runtime_scope_fallback_uses_scope_scope_txt_not_campaign_md() -> None:
    rp = RUN_PIPELINE.read_text(encoding='utf-8')
    ar = AUTO_RUNNER.read_text(encoding='utf-8')
    bootstrap = RUNTIME_RUNNER_BOOTSTRAP.read_text(encoding='utf-8')
    assert "return wp('scope', 'scope.txt')" in rp
    assert "return wp_fn('scope', 'scope.txt')" in bootstrap
    assert "return wp('campaign.md')" not in rp
    assert "return wp_fn('campaign.md')" not in bootstrap
