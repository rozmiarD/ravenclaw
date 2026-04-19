#!/usr/bin/env python3
from __future__ import annotations

import subprocess

from paths import WORKSPACE

ROOT = WORKSPACE
CHANGELOG = ROOT / 'CHANGELOG.md'
THRESHOLD = 5  # enforce update after 5 key commits
KEY_PATHS = ['engine', 'logdash']


def run(cmd: list[str]) -> str:
    p = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    if p.returncode != 0:
        return ''
    return p.stdout.strip()


def main() -> int:
    if not CHANGELOG.exists():
        print('ERROR: CHANGELOG.md missing')
        return 2

    last_changelog_commit = run(['git', 'log', '-n', '1', '--pretty=%H', '--', 'CHANGELOG.md'])
    if not last_changelog_commit:
        print('ERROR: cannot find changelog commit')
        return 3

    key_commits_raw = run(['git', 'rev-list', f'{last_changelog_commit}..HEAD', '--', *KEY_PATHS])
    key_commits = [c for c in key_commits_raw.splitlines() if c.strip()]
    count = len(key_commits)

    print(f'changelog_guard: key_commits_since_changelog={count} threshold={THRESHOLD}')
    if count >= THRESHOLD:
        print('ERROR: CHANGELOG update required before continuing.')
        return 4

    print('OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
