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
            'govengine': {'surface': 'security_profile_helpers', 'groups': ['action_tooling', 'policy_scope']},
            'sclite': {'artifact_chain_status': 'passed', 'checked_entries': ['intent_contract', 'execution_receipt']},
            'non_claims': ['no live target scanning'],
        }
    )

    assert '# Ravenclaw Demo Scenario Summary' in text
    assert 'execution_adapter: `mock`' in text
    assert 'govengine_surface: `security_profile_helpers`' in text
    assert 'sclite_chain_status: `passed`' in text
    assert 'artifact chain manifest' in text
    assert 'no live target scanning' in text
