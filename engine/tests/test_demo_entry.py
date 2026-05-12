from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import demo_entry  # type: ignore


def test_build_demo_commands_default_shape() -> None:
    commands = demo_entry.build_demo_commands(python_bin='python3')
    assert len(commands) == 2
    assert commands[0][0] == 'python3'
    assert commands[0][1].endswith('engine/plan_campaign.py')
    assert commands[0][2:] == ['--scope-txt', 'engine/planer/examples/sample_scope.txt', '--flags-json', '{"homelab": false}', '--runtime-mode', 'demo']
    assert commands[1][1].endswith('engine/run_pipeline.py')
    assert commands[1][2:] == ['--objective', demo_entry.DEFAULT_OBJECTIVE, '--target', demo_entry.DEFAULT_TARGET, '--runtime-mode', 'demo', '--dry-run']


def test_build_demo_commands_plan_only() -> None:
    commands = demo_entry.build_demo_commands(python_bin='python3', plan_only=True)
    assert len(commands) == 1
    assert commands[0][1].endswith('engine/plan_campaign.py')


def test_build_demo_commands_pipeline_only() -> None:
    commands = demo_entry.build_demo_commands(python_bin='python3', pipeline_only=True)
    assert len(commands) == 1
    assert commands[0][1].endswith('engine/run_pipeline.py')


def test_main_print_only_emits_objective_form(capsys) -> None:
    rc = demo_entry.main(['--print-only', '--pipeline-only'])
    out = capsys.readouterr().out
    assert rc == 0
    assert '--objective Fetch the homepage and summarize visible technologies --target https://example.com --runtime-mode demo --dry-run' in out


def test_demo_commands_use_configured_workspace(monkeypatch, tmp_path: Path) -> None:
    configured = tmp_path / 'configured-ravenclaw-root'
    configured.mkdir()
    monkeypatch.setenv('RAVENCLAW_WORKSPACE', str(configured))

    commands = demo_entry.build_demo_commands(python_bin='python3')

    assert commands[0][1] == str(configured / 'engine' / 'plan_campaign.py')
    assert commands[1][1] == str(configured / 'engine' / 'run_pipeline.py')
