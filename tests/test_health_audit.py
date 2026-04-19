from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_health_audit_reports_clean_runtime_risks() -> None:
    proc = subprocess.run(
        [sys.executable, str(ROOT / 'engine' / 'health_audit.py')],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    out = proc.stdout
    assert 'hardcoded_disallowed=0' in out
    assert 'naive_time_calls=0' in out
    assert 'broken_symlinks=0' in out
    assert 'tmp_sensitive=0' in out
