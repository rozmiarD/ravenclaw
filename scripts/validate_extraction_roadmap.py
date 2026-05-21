#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path
from typing import Iterable, Mapping


ROOT = Path(__file__).resolve().parents[1]
ROADMAP = ROOT / 'references' / 'govengine-extraction-readiness-roadmap.md'

ALLOWED_STATUSES = (
    'implement now as Ravenclaw validation/docs hardening',
    'already covered by GovEngine; maintain projection adapter',
    'extract later as contract',
    'defer until Tecrax proves need',
    'keep implementation in Ravenclaw',
    'keep in Ravenclaw',
)

REQUIRED_ADAPTER_LINES = (
    'engine/govengine_state_control_projection.py',
    'engine/govengine_planning_projection.py',
    'engine/govengine_admission_projection.py',
    'engine/govengine_runner_supervision_projection.py',
    'engine/govengine_review_projection.py',
)

REQUIRED_KEEP_TERMS = (
    'Logdash',
    'engine/executor.py',
    'engine/auto_campaign_runner.py',
    'engine/vuln_qualification.py',
    'finding taxonomy',
)

REQUIRED_DEFER_TERMS = (
    'runtime-owned artifact descriptor',
    'State-file manifest',
    'Replay/evaluation summary',
)

FORBIDDEN_CLAIMS = (
    'production-ready',
    'OpenClaw adapter is implemented',
    'OpenClaw Skill is implemented',
    'MCP adapter is implemented',
    'A2A adapter is implemented',
    'GovEngine owns Ravenclaw runtime',
    'GovEngine owns Logdash',
    'GovEngine owns Ravenclaw state files',
    'GovEngine owns Ravenclaw queue mutation',
    'GovEngine owns concrete execution',
)


def _read(path: Path) -> str:
    return path.read_text(encoding='utf-8')


def _pyproject() -> Mapping[str, object]:
    return tomllib.loads(_read(ROOT / 'pyproject.toml'))['project']


def _project_dependency(project: Mapping[str, object], name: str) -> str:
    prefix = f'{name}>='
    for dependency in project.get('dependencies', []):  # type: ignore[union-attr]
        text = str(dependency)
        if text.startswith(prefix):
            return text
    raise AssertionError(f'missing_dependency:{name}')


def _require(errors: list[str], text: str, expected: str) -> None:
    if expected not in text:
        errors.append(f'missing:{expected}')


def status_errors(text: str, allowed_statuses: Iterable[str] = ALLOWED_STATUSES) -> list[str]:
    allowed = set(allowed_statuses)
    errors: list[str] = []
    table_rows = re.findall(r'^\| [^|\n]+ \| [^|\n]+ \| [^|\n]+ \| [^|\n]+ \| [^|\n]+ \| ([^|\n]+) \|$', text, flags=re.MULTILINE)
    for status in table_rows:
        normalized = status.strip()
        if normalized in {'Status', '---'}:
            continue
        if normalized not in allowed:
            errors.append(f'unknown_status:{normalized}')
    return errors


def forbidden_claim_errors(text: str) -> list[str]:
    errors: list[str] = []
    for claim in FORBIDDEN_CLAIMS:
        if claim.lower() in text.lower():
            errors.append(f'forbidden_claim:{claim}')
    return errors


def collect_errors() -> list[str]:
    errors: list[str] = []
    project = _pyproject()
    version = str(project['version'])
    govengine_dep = _project_dependency(project, 'govengine')
    sclite_dep = _project_dependency(project, 'sclite-core')
    text = _read(ROADMAP)

    _require(errors, text, f'Ravenclaw: ravenclaw-security=={version}')
    _require(errors, text, f'Ravenclaw -> {govengine_dep} -> {sclite_dep}')
    _require(errors, text, 'alpha public helper/profile package; full runtime remains source/reference')

    for status in ALLOWED_STATUSES:
        _require(errors, text, status)
    errors.extend(status_errors(text))

    for adapter in REQUIRED_ADAPTER_LINES:
        _require(errors, text, adapter)
    _require(errors, text, 'Already covered by GovEngine')
    _require(errors, text, 'Ravenclaw should maintain projection')

    for term in REQUIRED_KEEP_TERMS:
        _require(errors, text, term)
    for term in REQUIRED_DEFER_TERMS:
        _require(errors, text, term)
    _require(errors, text, 'after Tecrax proves the same need')
    _require(errors, text, 'Keep implementation in Ravenclaw; only neutral snapshots/contracts may be reconsidered after Tecrax proves the same need.')

    errors.extend(forbidden_claim_errors(text))
    return errors


def main() -> int:
    errors = collect_errors()
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    project = _pyproject()
    print(f'extraction_roadmap_ok:ravenclaw-security=={project["version"]}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
