#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Mapping

ROOT = Path(__file__).resolve().parents[1]
ENGINE_DIR = ROOT / 'engine'
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

import paths as runtime_paths  # noqa: E402
from runtime_state_truth import projected_runtime_state_artifacts, runtime_state_artifacts  # noqa: E402


DOC_PATHS = (
    'STATE_FILES.md',
    'references/runtime-artifact-ownership.md',
    'references/runtime-state-control-govengine-map.md',
)


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def documentation_errors(text_by_path: Mapping[str, str]) -> list[str]:
    errors: list[str] = []
    state_files = text_by_path['STATE_FILES.md']
    ownership = text_by_path['references/runtime-artifact-ownership.md']
    control_map = text_by_path['references/runtime-state-control-govengine-map.md']

    for artifact in runtime_state_artifacts():
        if artifact.path not in state_files:
            errors.append(f'STATE_FILES.md:missing_runtime_state_path:{artifact.path}')
        if artifact.canonical_path_attr and artifact.path not in ownership:
            errors.append(f'references/runtime-artifact-ownership.md:missing_canonical_path:{artifact.path}')
        for legacy_path in artifact.legacy_paths:
            if legacy_path not in ownership:
                errors.append(f'references/runtime-artifact-ownership.md:missing_legacy_path:{legacy_path}')

    for artifact in projected_runtime_state_artifacts():
        if artifact.path not in control_map:
            errors.append(f'references/runtime-state-control-govengine-map.md:missing_projected_path:{artifact.path}')
        if artifact.govengine_projection not in control_map:
            errors.append(
                'references/runtime-state-control-govengine-map.md:'
                f'missing_projection_name:{artifact.govengine_projection}'
            )
    return errors


def canonical_path_errors() -> list[str]:
    errors: list[str] = []
    expected_by_attr = {
        'RUNTIME_PLAN_PATH': runtime_paths.REPORTS_STATE_DIR / 'public_targets_plan.json',
        'CONTEXT_SUMMARY_PATH': runtime_paths.REPORTS_CACHE_DIR / 'context_summary.json',
    }
    for artifact in runtime_state_artifacts():
        if not artifact.canonical_path_attr:
            continue
        actual = getattr(runtime_paths, artifact.canonical_path_attr, None)
        if not isinstance(actual, Path):
            errors.append(f'missing_canonical_path_attr:{artifact.canonical_path_attr}')
            continue
        expected = expected_by_attr.get(artifact.canonical_path_attr, ROOT / artifact.path).resolve()
        if actual.resolve() != expected:
            errors.append(
                f'canonical_path_mismatch:{artifact.canonical_path_attr}:{actual.resolve()}!={expected}'
            )
    return errors


def collect_errors() -> list[str]:
    return [
        *documentation_errors({path: _read(path) for path in DOC_PATHS}),
        *canonical_path_errors(),
    ]


def main() -> int:
    errors = collect_errors()
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f'runtime_state_truth_ok:artifacts={len(runtime_state_artifacts())}:projected={len(projected_runtime_state_artifacts())}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
