from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str = ''
    stderr: str = ''


class GovExecutionBackend(Protocol):
    """Port for command execution backends.

    Stage 1 defines the contract only; Ravenclaw's current executor remains in
    place until a later approved movement wave.
    """

    def run(self, argv: Sequence[str], *, stdin: str | None = None) -> CommandResult:
        ...
