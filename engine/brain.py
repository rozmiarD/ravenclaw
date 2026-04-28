#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Planner/brain adapter seam for the governed Ravenclaw runtime.

This module is intentionally narrow.
It does **not** claim to embed Ravenclaw's full production planner stack locally.
Instead it provides:
- a stable role-specific memory seam for local/dev use
- an honest adapter surface that can delegate to externally configured runtime integrations
- a deterministic fallback when no external planner backend is configured

That keeps the public core truthful: the planner/brain interface is real, but some
production integrations live in runtime configuration and surrounding operator
infrastructure rather than in this file.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable, Dict, Mapping

SYSTEM_MEMORY_DIR = Path(__file__).resolve().parent / "system_memory"
SYSTEM_MEMORY_PATH = SYSTEM_MEMORY_DIR / "brain.md"

PlanBackend = Callable[[str, str], Mapping[str, Any]]


class Brain:
    """Honest adapter for planner/brain behavior.

    Default behavior is deterministic fallback mode.
    If `RAVENCLAW_BRAIN_BACKEND` is set to `deterministic`, the same fallback is
    used explicitly.

    Future runtime wiring may register additional backends, but this file should
    remain explicit about the fact that backend selection is configuration-driven
    rather than pretending to contain the full production planner implementation.
    """

    def __init__(self, memory_path: Path = SYSTEM_MEMORY_PATH):
        self.system_memory_path = memory_path
        self.system_memory = self._load_system_memory()
        self.backend_name = self._resolve_backend_name()

    def _resolve_backend_name(self) -> str:
        raw = str(os.getenv("RAVENCLAW_BRAIN_BACKEND", "")).strip().lower()
        return raw or "deterministic"

    # ------------------------------------------------------------------
    # System memory helpers
    # ------------------------------------------------------------------
    def _load_system_memory(self) -> str:
        SYSTEM_MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        if not self.system_memory_path.exists():
            self.system_memory_path.write_text(
                "# Brain System Memory\n\n(autocreated)", encoding="utf-8"
            )
        return self.system_memory_path.read_text(encoding="utf-8")

    def append_system_memory(self, note: str) -> None:
        note = note.strip()
        if not note:
            return
        current = self._load_system_memory().rstrip()
        if current:
            current += "\n"
        updated = f"{current}- {note}\n"
        self.system_memory_path.write_text(updated, encoding="utf-8")
        self.system_memory = updated

    # ------------------------------------------------------------------
    # Backends
    # ------------------------------------------------------------------
    def _deterministic_plan(self, context: str) -> Dict[str, object]:
        memory_preview = "\n".join(self.system_memory.splitlines()[:10]).strip()
        context_echo = str(context or "")[:200]
        return {
            "role": "BRAIN",
            "mode": "deterministic_fallback",
            "summary": "No external planner backend configured; using bounded deterministic fallback.",
            "next_step": {
                "kind": "request_operator_or_runtime_input",
                "reason": "planner_backend_unavailable",
                "safe": True,
            },
            "system_memory_preview": memory_preview,
            "context_echo": context_echo,
        }

    def _run_backend(self, context: str) -> Dict[str, object]:
        if self.backend_name == "deterministic":
            return self._deterministic_plan(context)
        return {
            "role": "BRAIN",
            "mode": "backend_not_available",
            "summary": (
                f"Planner backend '{self.backend_name}' is referenced by configuration "
                "but is not implemented in this public adapter seam."
            ),
            "next_step": {
                "kind": "request_operator_or_runtime_input",
                "reason": "planner_backend_not_available",
                "safe": True,
            },
            "configured_backend": self.backend_name,
            "context_echo": str(context or "")[:200],
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def plan(self, context: str) -> Dict[str, object]:
        """Return a planner proposal from the configured adapter mode.

        This method preserves the public seam without pretending that a remote
        model/runtime integration is fully implemented inside this module.
        """
        return self._run_backend(context)


if __name__ == "__main__":
    b = Brain()
    print(b.plan("dummy"))
