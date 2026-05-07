from __future__ import annotations

from typing import Any, Protocol


class GovStateStore(Protocol):
    """Port for state persistence supplied by a host application."""

    def read_json(self, key: str) -> dict[str, Any]:
        ...

    def write_json(self, key: str, value: dict[str, Any]) -> None:
        ...
