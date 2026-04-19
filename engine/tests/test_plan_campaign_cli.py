from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]


def test_plan_campaign_cli_generates_blueprint_from_scope(tmp_path: Path) -> None:
    scope_path = tmp_path / 'scope.txt'
    scope_path.write_text(
        """
In Scope:
*.x.com Wildcard High
chat.x.com Domain Critical
money.x.com Domain Critical
x.com Domain Critical
*.twimg.com Wildcard Medium
Allowed: recon, xss, idor, csrf
Disallowed: dos, phishing
""".strip(),
        encoding='utf-8',
    )
    registry_root = tmp_path / 'registry'
    result = subprocess.run(
        [
            sys.executable,
            'engine/plan_campaign.py',
            '--scope-txt',
            str(scope_path),
            '--flags-json',
            json.dumps({'llm_interpret': False}),
            '--registry',
            str(registry_root),
            '--force-new-blueprint',
        ],
        cwd=WORKSPACE_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    latest_files = list(registry_root.rglob('latest.json'))
    assert latest_files
    blueprint_files = list(registry_root.rglob('blueprint.json'))
    assert blueprint_files
