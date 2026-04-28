from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List

DEFAULT_SCOPE_TXT = 'engine/planer/examples/sample_scope.txt'
DEFAULT_FLAGS_JSON = '{"homelab": false}'
DEFAULT_OBJECTIVE = 'Fetch the homepage and summarize visible technologies'
DEFAULT_TARGET = 'https://example.com'


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _python_bin() -> str:
    return sys.executable or 'python3'


def build_demo_commands(
    *,
    python_bin: str | None = None,
    scope_txt: str = DEFAULT_SCOPE_TXT,
    flags_json: str = DEFAULT_FLAGS_JSON,
    objective: str = DEFAULT_OBJECTIVE,
    target: str = DEFAULT_TARGET,
    plan_only: bool = False,
    pipeline_only: bool = False,
) -> List[List[str]]:
    py = python_bin or _python_bin()
    root = repo_root()
    commands: List[List[str]] = []

    if not pipeline_only:
        commands.append(
            [
                py,
                str(root / 'engine' / 'plan_campaign.py'),
                '--scope-txt',
                scope_txt,
                '--flags-json',
                flags_json,
                '--runtime-mode',
                'demo',
            ]
        )

    if not plan_only:
        commands.append(
            [
                py,
                str(root / 'engine' / 'run_pipeline.py'),
                '--objective',
                objective,
                '--target',
                target,
                '--runtime-mode',
                'demo',
                '--dry-run',
            ]
        )

    return commands


def _format_command(command: Iterable[str]) -> str:
    return ' '.join(str(part) for part in command)


def _run_commands(commands: List[List[str]], *, cwd: Path) -> int:
    env = dict(os.environ)
    env.setdefault('RAVENCLAW_MODE', 'demo')
    for command in commands:
        print(f'[demo] $ {_format_command(command)}')
        proc = subprocess.run(command, cwd=str(cwd), env=env)
        if proc.returncode != 0:
            return int(proc.returncode)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description='Run the official public-safe Ravenclaw demo path.')
    ap.add_argument('--scope-txt', default=DEFAULT_SCOPE_TXT)
    ap.add_argument('--flags-json', default=DEFAULT_FLAGS_JSON)
    ap.add_argument('--objective', default=DEFAULT_OBJECTIVE)
    ap.add_argument('--target', default=DEFAULT_TARGET)
    ap.add_argument('--print-only', action='store_true', help='print the demo commands without executing them')
    ap.add_argument('--plan-only', action='store_true', help='run only the sample scope planning step')
    ap.add_argument('--pipeline-only', action='store_true', help='run only the governed dry-run pipeline step')
    args = ap.parse_args(argv)

    if args.plan_only and args.pipeline_only:
        ap.error('--plan-only and --pipeline-only cannot be used together')

    commands = build_demo_commands(
        scope_txt=str(args.scope_txt),
        flags_json=str(args.flags_json),
        objective=str(args.objective),
        target=str(args.target),
        plan_only=bool(args.plan_only),
        pipeline_only=bool(args.pipeline_only),
    )

    if args.print_only:
        for command in commands:
            print(_format_command(command))
        return 0

    return _run_commands(commands, cwd=repo_root())


if __name__ == '__main__':
    raise SystemExit(main())
