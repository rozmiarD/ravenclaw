from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1] / 'logdash'
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services import (  # type: ignore
    compute_plan_counts,
    load_host_state,
    load_latest_blueprint,
    load_queue_state,
    load_runtime_state,
    runtime_plan_status,
)



def test_runtime_plan_status_reports_normalized_source(tmp_path: Path) -> None:
    reports = tmp_path / 'reports'
    reports.mkdir()
    (reports / '.runtime_plan.meta.json').write_text('{"generated": 2, "campaign_key": "alpha"}', encoding='utf-8')

    payload = runtime_plan_status(reports)

    assert payload['ok'] is True
    assert payload['source'] == 'normalized_runtime_plan_meta'



def test_load_host_state_reports_normalized_source(tmp_path: Path) -> None:
    path = tmp_path / 'host_state.json'
    path.write_text('{"hosts": {"alpha.example.com": {"score": 5}}}', encoding='utf-8')

    payload = load_host_state(path)

    assert payload['_source'] == 'normalized_host_state_file'



def test_load_queue_state_reports_normalized_source(tmp_path: Path) -> None:
    path = tmp_path / 'queue_state.json'
    path.write_text('{"followup_queue": [{"target": "https://a.example.com"}], "precision_queue": []}', encoding='utf-8')

    payload = load_queue_state(path)

    assert payload['source'] == 'normalized_queue_state'
    assert len(payload['followup_queue']) == 1



def test_compute_plan_counts_tolerates_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / 'plan.json'
    path.write_text('{bad json', encoding='utf-8')

    payload = compute_plan_counts(path)

    assert payload == {'prepared_attacks': 0, 'scope_targets': 0}



def test_load_runtime_state_uses_normalized_sources(tmp_path: Path) -> None:
    reports = tmp_path / 'reports'
    reports.mkdir()
    (reports / '.auto_campaign.state.json').write_text('{"state": "running"}', encoding='utf-8')
    (reports / '.runtime_plan.meta.json').write_text('{"generated": 3, "target_count": 2}', encoding='utf-8')

    payload = load_runtime_state(reports)

    assert payload['sources']['auto_campaign'] == 'normalized_auto_campaign_state'
    assert payload['sources']['runtime_plan'] == 'normalized_runtime_plan_meta'



def test_load_latest_blueprint_tolerates_invalid_registry_latest(tmp_path: Path) -> None:
    root = tmp_path / 'registry'
    selected = root / 'alpha'
    selected.mkdir(parents=True)
    (selected / 'latest.json').write_text('{bad json', encoding='utf-8')

    assert load_latest_blueprint('alpha', root) is None
