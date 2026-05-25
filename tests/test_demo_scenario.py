from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / 'scripts' / 'run_demo_scenario.py'
spec = importlib.util.spec_from_file_location('run_demo_scenario', MODULE_PATH)
assert spec and spec.loader
scenario = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scenario)  # type: ignore[union-attr]


def test_demo_scenario_markdown_surfaces_package_chain_truth() -> None:
    text = scenario.build_demo_scenario_markdown(
        {
            'status': 'passed',
            'trace': scenario.DEMO_SCENARIO_TRACE,
            'ravenclaw': {
                'runtime_mode': 'demo',
                'engine_status': 'dry-run',
                'execution_adapter': 'mock',
            },
            'package_chain': {'version_source': 'executed_import_modules', 'govengine': '0.12.0a0', 'sclite-core': '0.8.0a0'},
            'govengine': {
                'boundary_source': 'govengine.kernel_boundary_report',
                'required_surfaces': ['artifact_governance_core', 'controlled_execution_core'],
                'retired_optional_surfaces_present': [],
            },
            'ravenclaw_security_profile': {
                'profile': 'ravenclaw-security',
                'domain': 'security-research-runtime',
                'status': 'passed',
            },
            'sclite': {'artifact_chain_status': 'passed', 'review_bundle_verdict': 'pass', 'checked_entries': ['intent_contract', 'execution_receipt']},
            'reviewer_commands': ['./scripts/bootstrap_public_demo.sh scenario', 'sclite verify-lifecycle demo-output/demo-scenario/artifact_chain_manifest.json'],
            'artifact_paths': {
                'demo_scenario_summary.json': 'demo-output/demo-scenario/demo_scenario_summary.json',
                'artifact_chain_manifest.json': 'demo-output/demo-scenario/artifact_chain_manifest.json',
            },
            'non_claims': ['no live target scanning'],
        }
    )

    assert '# Ravenclaw Demo Scenario Summary' in text
    assert 'execution_adapter: `mock`' in text
    assert 'govengine_version: `0.12.0a0`' in text
    assert 'sclite_core_version: `0.8.0a0`' in text
    assert 'govengine_boundary_source: `govengine.kernel_boundary_report`' in text
    assert 'ravenclaw_security_profile: `ravenclaw-security`' in text
    assert '`artifact_governance_core`' in text
    assert 'sclite_chain_status: `passed`' in text
    assert 'sclite_review_bundle_verdict: `pass`' in text
    assert 'artifact chain manifest' in text
    assert './scripts/bootstrap_public_demo.sh scenario' in text
    assert 'demo_scenario_summary.json' in text
    assert 'no live target scanning' in text
