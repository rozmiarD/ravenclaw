#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

from paths import WORKSPACE

SCAN_DIRS = [WORKSPACE / 'engine', WORKSPACE / 'logdash', WORKSPACE / 'tests']
HARD_PATH = str(WORKSPACE)
TIME_PATTERNS = [r'datetime\.now\(\)', r'datetime\.utcnow\(\)']
ALLOWED_HARDCODED_DEFAULTS = {
    WORKSPACE / 'engine' / 'paths.py',
    WORKSPACE / 'engine' / 'monitor.sh',
    WORKSPACE / 'engine' / 'preflight_checks.sh',
    WORKSPACE / 'logdash' / 'app.py',
}
DOC_PATHS = {
    WORKSPACE / 'engine' / 'planer' / 'README.md',
    WORKSPACE / 'logdash' / 'README.md',
    WORKSPACE / 'logdash' / 'README-service.md',
}


def iter_files():
    for root in SCAN_DIRS:
        if not root.exists():
            continue
        for p in root.rglob('*'):
            if not p.is_file():
                continue
            if '.venv' in p.parts:
                continue
            if p.suffix not in {'.py', '.md', '.sh', '.html', '.json', '.yaml', '.yml'}:
                continue
            yield p


def main() -> int:
    disallowed_hardcoded = []
    allowed_defaults = []
    docs_hardcoded = []
    bad_time = []
    broken_symlinks = [p for p in WORKSPACE.rglob('*') if p.is_symlink() and not p.exists()]
    tmp_sensitive = [p for p in (WORKSPACE / 'tmp').glob('*') if p.is_file() and any(k in p.name.lower() for k in ('cookie', 'token', 'secret', 'session'))]
    for p in iter_files():
        text = p.read_text(encoding='utf-8', errors='ignore')
        if HARD_PATH in text:
            if p in ALLOWED_HARDCODED_DEFAULTS:
                allowed_defaults.append(p)
            elif p in DOC_PATHS:
                docs_hardcoded.append(p)
            else:
                disallowed_hardcoded.append(p)
        if any(re.search(pat, text) for pat in TIME_PATTERNS):
            bad_time.append(p)
    print(
        'hardcoded_disallowed={} hardcoded_defaults={} hardcoded_docs={} naive_time_calls={} broken_symlinks={} tmp_sensitive={}'.format(
            len(disallowed_hardcoded), len(allowed_defaults), len(docs_hardcoded), len(bad_time), len(broken_symlinks), len(tmp_sensitive)
        )
    )
    for label, items in [
        ('HARDCODED_DISALLOWED', disallowed_hardcoded),
        ('HARDCODED_DEFAULT', allowed_defaults),
        ('HARDCODED_DOC', docs_hardcoded),
        ('NAIVE_TIME', bad_time),
        ('BROKEN_SYMLINK', broken_symlinks),
        ('TMP_SENSITIVE', tmp_sensitive),
    ]:
        for p in items[:100]:
            print(label, p)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
