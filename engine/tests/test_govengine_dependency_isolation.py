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


def test_ravenclaw_action_modules_are_govengine_compat_aliases() -> None:
    sys.path.insert(0, str(REPO_ROOT / 'engine'))
    import action_compiler  # type: ignore
    import action_schema  # type: ignore
    import action_validators  # type: ignore
    import capability_recipes  # type: ignore
    import semantic_loss_policy  # type: ignore
    import signal_contract  # type: ignore
    import analysis_contract  # type: ignore
    import evidence_policy  # type: ignore

    assert action_schema.__name__ == 'govengine.action_schema'
    assert action_validators.__name__ == 'govengine.action_validators'
    assert action_compiler.__name__ == 'govengine.action_compiler'
    assert capability_recipes.__name__ == 'govengine.capability_recipes'
    assert semantic_loss_policy.__name__ == 'govengine.semantic_loss_policy'
    assert signal_contract.__name__ == 'govengine.contracts.signal'
    assert analysis_contract.__name__ == 'govengine.contracts.analysis'
    assert evidence_policy.__name__ == 'govengine.contracts.evidence_policy'
