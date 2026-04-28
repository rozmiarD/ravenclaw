#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List, Sequence


TEXT_EXTENSIONS = {
    '.cfg',
    '.css',
    '.csv',
    '.dockerignore',
    '.env',
    '.html',
    '.ini',
    '.js',
    '.json',
    '.json5',
    '.jsx',
    '.md',
    '.py',
    '.sh',
    '.toml',
    '.ts',
    '.tsx',
    '.txt',
    '.yaml',
    '.yml',
}

FORBIDDEN_ROOT_PATHS = {
    'AGENTS.md',
    'SOUL.md',
    'USER.md',
    'TOOLS.md',
    'WORKFLOW.md',
    'HEARTBEAT.md',
    'MEMORY.md',
    'NEXT_SESSION.md',
    'demo-output',
    'logs',
    'memory',
    'pending',
    'reports',
    'state',
    'tmp',
    'workspace-brain',
    '.main-publish-fix',
    '.publish-worktree',
    'ravenclaw.egg-info',
}

FORBIDDEN_RUNTIME_PATHS = {
    'out.json',
    'engine/context_summary.json',
    'engine/pipeline_config.json',
    'engine/public_targets_plan.json',
    'engine/system_memory',
    'logdash/agents_config.json',
    'logdash/logs.db',
}

FORBIDDEN_BASENAMES = {
    'logs.db',
    'logdash.out',
}

BLOCK_CONTENT_PATTERNS: Sequence[tuple[str, re.Pattern[str]]] = (
    ('absolute_home_path', re.compile(r'/home/[A-Za-z0-9._-]+/')),
    ('workspace_absolute_path', re.compile(r'/home/[A-Za-z0-9._-]+/\.openclaw/workspace')),
    ('private_key_material', re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----')),
    ('aws_access_key_id', re.compile(r'AKIA[0-9A-Z]{16}')),
    ('github_token', re.compile(r'gh[pousr]_[A-Za-z0-9_]{20,}')),
    ('slack_token', re.compile(r'xox[baprs]-[A-Za-z0-9-]{20,}')),
    ('openai_key', re.compile(r'sk-[A-Za-z0-9_-]{32,}')),
)

WARN_CONTENT_PATTERNS: Sequence[tuple[str, re.Pattern[str]]] = (
    ('cookie_assignment', re.compile(r'(?i)\b(cookie|set-cookie)\b')),
    ('session_assignment', re.compile(r'(?i)\bsession(id)?\s*=')),
    ('bearer_token_reference', re.compile(r'(?i)bearer\s+[A-Za-z0-9._~+/=-]{12,}')),
    ('raw_stdout_stderr_reference', re.compile(r'(?i)raw stdout|raw stderr|step_[0-9]+_(stdout|stderr)\.txt')),
)


@dataclass(frozen=True)
class Finding:
    severity: str
    check: str
    path: str
    detail: str


def _rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _is_text_file(path: Path) -> bool:
    if path.suffix in TEXT_EXTENSIONS:
        return True
    name = path.name.lower()
    return name in {'dockerfile', 'makefile', 'license'} or path.suffix == ''


def iter_files(root: Path) -> Iterable[Path]:
    for path in root.rglob('*'):
        if path.is_file() and not path.is_symlink():
            yield path


def audit_snapshot(snapshot: Path) -> List[Finding]:
    snapshot = snapshot.resolve()
    findings: List[Finding] = []
    if not snapshot.exists():
        return [Finding('blocker', 'snapshot_exists', str(snapshot), 'snapshot path does not exist')]
    if not snapshot.is_dir():
        return [Finding('blocker', 'snapshot_is_dir', str(snapshot), 'snapshot path is not a directory')]

    for rel in sorted(FORBIDDEN_ROOT_PATHS | FORBIDDEN_RUNTIME_PATHS):
        path = snapshot / rel
        if path.exists():
            findings.append(Finding('blocker', 'forbidden_path', rel, 'forbidden local/runtime path is present'))

    for path in iter_files(snapshot):
        rel = _rel(path, snapshot)
        if rel == '.git' or rel.startswith('.git/'):
            continue
        if path.name in FORBIDDEN_BASENAMES:
            findings.append(Finding('blocker', 'forbidden_basename', rel, f'forbidden generated basename: {path.name}'))
        if re.search(r'step_[0-9]+_(stdout|stderr)\.txt$', path.name):
            findings.append(Finding('blocker', 'raw_handoff_output', rel, 'raw handoff stdout/stderr artifact is present'))
        if path.suffix in {'.pyc', '.pyo', '.pyd', '.log'}:
            findings.append(Finding('blocker', 'generated_noise_file', rel, f'generated/noise extension: {path.suffix}'))
        if not _is_text_file(path):
            continue
        try:
            text = path.read_text(encoding='utf-8', errors='replace')
        except OSError as exc:
            findings.append(Finding('warning', 'read_failed', rel, str(exc)))
            continue
        for check, pattern in BLOCK_CONTENT_PATTERNS:
            if pattern.search(text):
                findings.append(Finding('blocker', check, rel, 'sensitive or private residue pattern present'))
        for check, pattern in WARN_CONTENT_PATTERNS:
            if pattern.search(text):
                findings.append(Finding('warning', check, rel, 'review contextual token/raw-output wording'))
    return findings


def build_manifest(snapshot: Path) -> List[str]:
    snapshot = snapshot.resolve()
    return sorted(_rel(path, snapshot) for path in iter_files(snapshot))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Audit an assembled Ravenclaw public snapshot for local/private residue.')
    parser.add_argument('snapshot_dir')
    parser.add_argument('--json', action='store_true', help='print machine-readable audit result')
    parser.add_argument('--manifest', action='store_true', help='include file manifest in JSON output')
    args = parser.parse_args(argv)

    snapshot = Path(args.snapshot_dir).resolve()
    findings = audit_snapshot(snapshot)
    blockers = [finding for finding in findings if finding.severity == 'blocker']
    warnings = [finding for finding in findings if finding.severity == 'warning']
    result = {
        'snapshot': str(snapshot),
        'ok': not blockers,
        'blockers': [asdict(finding) for finding in blockers],
        'warnings': [asdict(finding) for finding in warnings],
        'counts': {
            'files': len(build_manifest(snapshot)) if snapshot.exists() and snapshot.is_dir() else 0,
            'blockers': len(blockers),
            'warnings': len(warnings),
        },
    }
    if args.manifest and snapshot.exists() and snapshot.is_dir():
        result['manifest'] = build_manifest(snapshot)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        status = 'public_snapshot_residue_ok' if result['ok'] else 'public_snapshot_residue_blocked'
        print(f'{status}:{snapshot}')
        print(f"files={result['counts']['files']} blockers={len(blockers)} warnings={len(warnings)}")
        for finding in blockers:
            print(f'BLOCKER {finding.check} {finding.path}: {finding.detail}', file=sys.stderr)
        for finding in warnings:
            print(f'WARNING {finding.check} {finding.path}: {finding.detail}', file=sys.stderr)
    return 0 if not blockers else 1


if __name__ == '__main__':
    raise SystemExit(main())
