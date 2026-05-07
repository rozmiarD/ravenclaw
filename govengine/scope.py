from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Protocol


class GovScopePort(Protocol):
    """Neutral host/scope policy port for GovEngine helpers."""

    def extract_host(self, value: Any) -> str:
        ...

    def host_in_scope(self, host: str, scope_domains: Any) -> bool:
        ...


@dataclass(frozen=True)
class FunctionalScopePort:
    """Scope port backed by host-provided functions.

    Ravenclaw supplies its campaign scope helpers here during package-in-place
    extraction. A future GovEngine consumer can provide equivalent functions
    without importing Ravenclaw campaign modules.
    """

    extract_host_fn: Callable[[Any], Any]
    host_in_scope_fn: Callable[[str, Any], bool]

    def extract_host(self, value: Any) -> str:
        return str(self.extract_host_fn(value) or '').strip().lower()

    def host_in_scope(self, host: str, scope_domains: Any) -> bool:
        return bool(self.host_in_scope_fn(str(host or '').strip().lower(), scope_domains))
