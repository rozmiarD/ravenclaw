from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_tool_registry_audit_runs_and_reports_profile_lines() -> None:
    proc = subprocess.run(
        [sys.executable, str(ROOT / 'engine' / 'tool_registry_audit.py')],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    out = proc.stdout
    assert 'tools=' in out
    assert 'PROFILE core' in out
    assert 'PROFILE extended' in out
    assert 'PROFILE lab' in out
    assert 'executor_only_declared=' in out
