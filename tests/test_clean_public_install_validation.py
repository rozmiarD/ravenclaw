from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'validate_clean_public_install.py'


def test_clean_public_install_validator_dry_run_documents_clean_env_plan(tmp_path: Path) -> None:
    venv = tmp_path / 'clean-venv'
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            '--venv',
            str(venv),
            '--dev',
            '--sclite-source',
            str(ROOT.parent / 'sclite-owner-update'),
            '--govengine-source',
            str(ROOT.parent / 'govengine-standalone'),
            '--dry-run',
            '--json',
        ],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        check=True,
    )

    data = json.loads(proc.stdout)
    assert data['artifact_type'] == 'ravenclaw_clean_public_install_validation'
    assert data['status'] == 'planned'
    assert data['mode'] == 'dev'
    assert data['venv'] == str(venv)
    commands = [' '.join(step['command']) for step in data['steps']]
    assert commands[0].endswith(f'-m venv {venv}')
    assert any('sclite-owner-update' in command for command in commands)
    assert any('govengine-standalone' in command for command in commands)
    assert any('pip install -e .[dev]' in command for command in commands)
    assert commands[-1].endswith('scripts/validate_public_install.py --dev')


def test_clean_public_install_validator_rejects_existing_venv_path(tmp_path: Path) -> None:
    existing = tmp_path / 'existing'
    existing.mkdir()

    proc = subprocess.run(
        [sys.executable, str(SCRIPT), '--venv', str(existing), '--json'],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        check=False,
    )

    data = json.loads(proc.stdout)
    assert proc.returncode == 1
    assert data['status'] == 'failed'
    assert data['error'] == 'venv_already_exists_choose_new_path'
