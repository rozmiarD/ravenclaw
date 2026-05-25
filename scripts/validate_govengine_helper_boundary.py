#!/usr/bin/env python3
from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / 'engine'
LOGDASH = ROOT / 'logdash'
WRAPPER = ENGINE / 'govengine_security_helpers.py'

RETIRED_OPTIONAL_HELPER_MODULES = (
    'govengine.security_profile',
    'govengine.action_schema',
    'govengine.action_validators',
    'govengine.action_compiler',
    'govengine.capability_recipes',
    'govengine.tool_registry',
    'govengine.semantic_loss_policy',
    'govengine.policy.core',
    'govengine.policy.gateway',
    'govengine.scope',
    'govengine.contracts.signal',
    'govengine.contracts.analysis',
    'govengine.contracts.evidence_policy',
)
HOST_OWNED_OPTIONAL_REPLACEMENTS = {
    'govengine.action_schema': ENGINE / 'security_action_schema.py',
    'govengine.action_validators': ENGINE / 'security_action_validators.py',
    'govengine.action_compiler': ENGINE / 'security_action_compiler.py',
    'govengine.capability_recipes': ENGINE / 'security_capability_recipes.py',
    'govengine.tool_registry': ENGINE / 'security_tool_registry.py',
    'govengine.semantic_loss_policy': ENGINE / 'security_semantic_loss_policy.py',
    'govengine.policy.core': ENGINE / 'security_policy_core.py',
    'govengine.policy.gateway': ENGINE / 'security_policy_gateway.py',
    'govengine.contracts.signal': ENGINE / 'security_signal_contract.py',
    'govengine.contracts.analysis': ENGINE / 'security_analysis_contract.py',
    'govengine.contracts.evidence_policy': ENGINE / 'security_evidence_policy.py',
}


def _is_optional_helper_module(module_name: str) -> bool:
    return any(module_name == prefix or module_name.startswith(prefix + '.') for prefix in RETIRED_OPTIONAL_HELPER_MODULES)


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


def _wrapper_migration_errors(text: str) -> list[str]:
    tree = ast.parse(text, filename=str(WRAPPER))
    errors: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module in HOST_OWNED_OPTIONAL_REPLACEMENTS:
            errors.append(f'engine/govengine_security_helpers.py:reintroduced_host_owned_import:{node.module}')
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in HOST_OWNED_OPTIONAL_REPLACEMENTS:
                    errors.append(f'engine/govengine_security_helpers.py:reintroduced_host_owned_import:{alias.name}')
    return errors


def collect_errors() -> list[str]:
    errors: list[str] = []
    if not WRAPPER.exists():
        errors.append('engine/govengine_security_helpers.py:missing_wrapper')
    else:
        errors.extend(_wrapper_migration_errors(WRAPPER.read_text(encoding='utf-8')))
    for upstream, replacement in HOST_OWNED_OPTIONAL_REPLACEMENTS.items():
        if not replacement.exists():
            errors.append(f'{replacement.relative_to(ROOT)}:missing_host_owned_replacement_for:{upstream}')
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
