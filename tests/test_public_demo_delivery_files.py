from __future__ import annotations

import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEVCONTAINER_JSON = ROOT / '.devcontainer' / 'devcontainer.json'
COMPOSE_DEMO = ROOT / 'compose.demo.yaml'
BOOTSTRAP_SCRIPT = ROOT / 'scripts' / 'bootstrap_public_demo.sh'


def test_devcontainer_json_exposes_public_demo_bootstrap() -> None:
    data = json.loads(DEVCONTAINER_JSON.read_text(encoding='utf-8'))
    assert data['name'] == 'Ravenclaw Public Demo'
    assert data['build']['dockerfile'] == 'Dockerfile'
    assert data['workspaceFolder'] == '/workspace'
    assert data['postCreateCommand'] == './scripts/bootstrap_public_demo.sh install'
    assert data['postAttachCommand'] == './scripts/bootstrap_public_demo.sh doctor'
    assert data['remoteEnv']['RAVENCLAW_MODE'] == 'demo'
    assert 9091 in data['forwardPorts']


def test_compose_demo_reuses_same_bootstrap_script() -> None:
    data = yaml.safe_load(COMPOSE_DEMO.read_text(encoding='utf-8'))
    assert set(data['services']) == {'demo', 'demo-bundle', 'logdash'}
    demo = data['services']['demo']
    bundle = data['services']['demo-bundle']
    logdash = data['services']['logdash']
    assert demo['build']['dockerfile'] == '.devcontainer/Dockerfile'
    assert './scripts/bootstrap_public_demo.sh demo' in demo['command'][-1]
    assert './scripts/bootstrap_public_demo.sh bundle' in bundle['command'][-1]
    assert './scripts/bootstrap_public_demo.sh logdash' in logdash['command'][-1]
    assert 'public-demo-venv:/workspace/.venv' in demo['volumes']
    assert '9091:9091' in logdash['ports']


def test_bootstrap_script_declares_expected_modes() -> None:
    text = BOOTSTRAP_SCRIPT.read_text(encoding='utf-8')
    assert 'install)' in text
    assert 'doctor)' in text
    assert 'demo)' in text
    assert 'demo-print)' in text
    assert 'bundle)' in text
    assert 'logdash)' in text
    assert 'smoke)' in text
    assert 'bin/demo' in text
    assert 'bin/demo-bundle' in text
    assert '--print-summary' in text
