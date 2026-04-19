#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Placeholder for the BRAIN component.
The actual model is managed by OpenClaw via runtime configuration. This local
module mainly preserves project structure and maintains role-specific system
memory aligned with the governed RAVENCLAW runtime.
"""

from pathlib import Path
from typing import Dict

SYSTEM_MEMORY_DIR = Path(__file__).resolve().parent / "system_memory"
SYSTEM_MEMORY_PATH = SYSTEM_MEMORY_DIR / "brain.md"


class Brain:
    def __init__(self, memory_path: Path = SYSTEM_MEMORY_PATH):
        # In production the Brain is a remote LLM accessed via OpenClaw.
        # This stub can be expanded with local test logic if needed.
        self.system_memory_path = memory_path
        self.system_memory = self._load_system_memory()

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
    # Public API
    # ------------------------------------------------------------------
    def plan(self, context: str) -> Dict[str, object]:
        """Return a dummy action specification.
        The real implementation would invoke the BRAIN model and produce a
        compact JSON-compatible proposal for exactly one next governed step.
        """
        memory_preview = "\n".join(self.system_memory.splitlines()[:10]).strip()
        return {
            "role": "BRAIN",
            "action": "run_command",
            "command": "echo 'Brain placeholder executed'",
            "cwd": "~/raven-claw",
            "estimated_tokens": 10,
            "system_memory_preview": memory_preview,
            "context_echo": context[:200],
        }


if __name__ == "__main__":
    b = Brain()
    print(b.plan("dummy"))
