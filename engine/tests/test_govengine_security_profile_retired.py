from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_public_validation_no_longer_imports_govengine_security_profile() -> None:
    for rel in (
        'scripts/validate_public_install.py',
        'scripts/validate_govengine_helper_boundary.py',
        'scripts/run_demo_scenario.py',
    ):
        assert 'govengine.security_profile' not in _imports(ROOT / rel)


def test_retired_optional_helper_denylist_is_ravenclaw_owned() -> None:
    text = (ROOT / 'scripts' / 'validate_govengine_helper_boundary.py').read_text(encoding='utf-8')

    assert 'from govengine.security_profile' not in text
    assert "'govengine.security_profile'" in text
    assert "'govengine.action_schema'" in text
    assert "'govengine.policy.gateway'" in text
    assert "'govengine.contracts.signal'" in text
