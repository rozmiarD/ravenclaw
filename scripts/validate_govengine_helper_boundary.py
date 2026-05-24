#!/usr/bin/env python3
from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Iterable

from govengine.security_profile import security_profile_module_names


ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / 'engine'
LOGDASH = ROOT / 'logdash'
WRAPPER = ENGINE / 'govengine_security_helpers.py'

OPTIONAL_HELPER_MODULES = security_profile_module_names()


def _is_optional_helper_module(module_name: str) -> bool:
    return any(module_name == prefix or module_name.startswith(prefix + '.') for prefix in OPTIONAL_HELPER_MODULES)


def _source_errors(path: Path, text: str) -> list[str]:
    tree = ast.parse(text, filename=str(path))
    errors: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and _is_optional_helper_module(node.module):
            errors.append(f'{path.relative_to(ROOT)}:direct_optional_helper_import:{node.module}')
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if _is_optional_helper_module(alias.name):
                    errors.append(f'{path.relative_to(ROOT)}:direct_optional_helper_import:{alias.name}')
    return errors


def runtime_source_paths() -> Iterable[Path]:
    for path in sorted(ENGINE.rglob('*.py')):
        if path == WRAPPER or 'tests' in path.parts or path.name == '__init__.py':
            continue
        yield path
    if LOGDASH.exists():
        for path in sorted(LOGDASH.rglob('*.py')):
            if 'tests' in path.parts or path.name == '__init__.py':
                continue
            yield path


def collect_errors() -> list[str]:
    errors: list[str] = []
    if not WRAPPER.exists():
        errors.append('engine/govengine_security_helpers.py:missing_wrapper')
    for path in runtime_source_paths():
        errors.extend(_source_errors(path, path.read_text(encoding='utf-8')))
    return errors


def main() -> int:
    errors = collect_errors()
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print('govengine_helper_boundary_ok:runtime_imports=wrapper_only')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
