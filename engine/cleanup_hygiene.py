#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from paths import WORKSPACE

ROOT = WORKSPACE
PATTERNS = [
    'reports/*.bak*',
    'reports/**/*.bak*',
    '**/*.jsonl.deleted.*',
]
SENSITIVE_HINTS = ['cookie', 'token', 'secret', 'session']


def main() -> None:
    found = []
    for pat in PATTERNS:
        found.extend(ROOT.glob(pat))
    uniq = sorted({p for p in found if p.is_file()})
    broken_links = sorted([p for p in ROOT.rglob('*') if p.is_symlink() and not p.exists()])
    tmp_sensitive = sorted([
        p for p in ROOT.rglob('tmp/*')
        if p.is_file() and any(h in p.name.lower() for h in SENSITIVE_HINTS)
    ])
    venv_backups = sorted([p for p in ROOT.glob('logdash/.venv.bak-*') if p.exists()])
    print(f'candidates={len(uniq)} broken_symlinks={len(broken_links)} tmp_sensitive={len(tmp_sensitive)} venv_backups={len(venv_backups)}')
    for p in uniq[:200]:
        print('CLEANUP', p)
    for p in broken_links[:50]:
        print('BROKEN_SYMLINK', p, '->', p.readlink())
    for p in tmp_sensitive[:50]:
        print('TMP_SENSITIVE', p)
    for p in venv_backups[:20]:
        print('VENV_BACKUP', p)


if __name__ == '__main__':
    main()
