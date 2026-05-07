from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class GovEnginePaths:
    """Filesystem paths supplied by a host application.

    GovEngine core code should receive this explicitly instead of guessing a
    Ravenclaw repository layout from ``__file__`` or environment names.
    """

    repo_root: Path
    reports_dir: Path
    logs_dir: Path
    state_dir: Path
    policy_file: Path
    whitelist_file: Path
    tool_registry_file: Path

    @classmethod
    def from_root(cls, root: Path) -> 'GovEnginePaths':
        resolved = root.resolve()
        tool_registry_candidates = [
            resolved / 'engine' / 'tool_registry.yaml',
            resolved / 'govengine' / 'tool_registry.yaml',
            resolved / 'tool_registry.yaml',
        ]
        tool_registry_file = next((candidate for candidate in tool_registry_candidates if candidate.exists()), tool_registry_candidates[0])
        return cls(
            repo_root=resolved,
            reports_dir=resolved / 'reports',
            logs_dir=resolved / 'logs',
            state_dir=resolved / 'state',
            policy_file=resolved / 'policy.yaml',
            whitelist_file=resolved / 'whitelist.yaml',
            tool_registry_file=tool_registry_file,
        )


@dataclass(frozen=True)
class GovEngineContext:
    """Minimal context object for package-in-place extraction work."""

    paths: GovEnginePaths
    profile: str = 'generic'
    env: Mapping[str, str] | None = None

    @property
    def repo_root(self) -> Path:
        return self.paths.repo_root


def discover_repo_root(start: Path) -> Path:
    """Find a Ravenclaw-style repository root from a file/directory anchor."""

    current = start.resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if not (candidate / 'pyproject.toml').exists():
            continue
        if (candidate / 'engine').is_dir() or (candidate / 'govengine').is_dir():
            return candidate
    return current


def ravenclaw_context(root: Path | None = None) -> GovEngineContext:
    """Build the Ravenclaw compatibility context explicitly.

    This is a compatibility profile, not a GovEngine core dependency on
    Ravenclaw environment variables.
    """

    anchor = root if root is not None else Path(__file__).resolve()
    repo_root = discover_repo_root(anchor)
    return GovEngineContext(paths=GovEnginePaths.from_root(repo_root), profile='ravenclaw')
