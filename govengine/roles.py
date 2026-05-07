from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class GovRoleAdapters:
    """Neutral role-provider ports supplied by a host application."""

    proposal_provider: Callable[..., Any] | None = None
    approval_provider: Callable[..., Any] | None = None
    analysis_provider: Callable[..., Any] | None = None
    summary_provider: Callable[..., Any] | None = None
