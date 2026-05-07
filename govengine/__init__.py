"""GovEngine package-in-place seam for Ravenclaw extraction.

This package is intentionally small at Stage 1. It exposes neutral context and
port contracts without moving Ravenclaw runtime logic yet.
"""

from .context import GovEngineContext, GovEnginePaths, ravenclaw_context
from .execution_backend import CommandResult, GovExecutionBackend
from .roles import GovRoleAdapters
from .scope import FunctionalScopePort, GovScopePort
from .sclite_contracts import GovSCLiteLifecycleVerifier, verify_lifecycle_manifest
from .state_store import GovStateStore

__all__ = [
    'CommandResult',
    'GovEngineContext',
    'GovEnginePaths',
    'GovExecutionBackend',
    'GovRoleAdapters',
    'FunctionalScopePort',
    'GovScopePort',
    'GovSCLiteLifecycleVerifier',
    'GovStateStore',
    'ravenclaw_context',
    'verify_lifecycle_manifest',
]
from .action_schema import *  # noqa: F401,F403
