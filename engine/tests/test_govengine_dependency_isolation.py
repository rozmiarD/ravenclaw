from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _govengine_source_dir() -> Path:
    in_tree = REPO_ROOT / 'govengine'
    if in_tree.is_dir():
        return in_tree
    import govengine

    return Path(govengine.__file__).resolve().parent


STANDALONE_MODULES = [
    'govengine',
    'govengine.context',
    'govengine.scope',
    'govengine.state_store',
    'govengine.action_schema',
    'govengine.action_validators',
    'govengine.semantic_loss_policy',
    'govengine.capability_recipes',
    'govengine.action_compiler',
    'govengine.tool_registry',
    'govengine.contracts.analysis',
    'govengine.contracts.evidence_policy',
    'govengine.contracts.execution',
    'govengine.contracts.signal',
    'govengine.policy.core',
    'govengine.policy.gateway',
    'govengine.execution.approved_spec',
    'govengine.execution.command_shape',
    'govengine.execution.runner',
    'govengine.execution.ticket_gate',
]


def test_govengine_public_surface_imports_without_engine_path(tmp_path: Path) -> None:
    package_root = tmp_path / 'standalone'
    shutil.copytree(_govengine_source_dir(), package_root / 'govengine')
    script = '\n'.join([
        'import importlib',
        f'mods = {STANDALONE_MODULES!r}',
        'for mod in mods:',
        '    importlib.import_module(mod)',
        'print("standalone_imports_ok:%d" % len(mods))',
    ])

    proc = subprocess.run(
        [sys.executable, '-c', script],
        cwd=package_root,
        env={'PYTHONDONTWRITEBYTECODE': '1'},
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert f'standalone_imports_ok:{len(STANDALONE_MODULES)}' in proc.stdout


def test_remaining_ravenclaw_contract_modules_are_govengine_compat_aliases() -> None:
    sys.path.insert(0, str(REPO_ROOT / 'engine'))
    import signal_contract  # type: ignore
    import analysis_contract  # type: ignore
    import evidence_policy  # type: ignore

    assert signal_contract.__name__ == 'govengine.contracts.signal'
    assert analysis_contract.__name__ == 'govengine.contracts.analysis'
    assert evidence_policy.__name__ == 'govengine.contracts.evidence_policy'


def test_retired_ravenclaw_action_compat_modules_are_absent() -> None:
    sys.path.insert(0, str(REPO_ROOT / 'engine'))
    for module_name in ('action_schema', 'action_compiler', 'action_validators', 'capability_recipes', 'semantic_loss_policy'):
        sys.modules.pop(module_name, None)
        try:
            __import__(module_name)
        except ModuleNotFoundError as exc:
            assert exc.name == module_name
        else:  # pragma: no cover
            raise AssertionError(f'{module_name} compatibility alias should be retired')
