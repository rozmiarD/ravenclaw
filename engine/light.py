#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Placeholder for the LIGHT component.
The actual model (NousResearch/Hermes-4-14B) is listed in openclaw.json.
This stub also loads a role-specific system-memory file so LIGHT guidance can
stay aligned with the live runtime architecture.
"""

from pathlib import Path

SYSTEM_MEMORY_DIR = Path(__file__).resolve().parent / "system_memory"
SYSTEM_MEMORY_PATH = SYSTEM_MEMORY_DIR / "light.md"


class Light:
    def __init__(self, memory_path: Path = SYSTEM_MEMORY_PATH):
        self.system_memory_path = memory_path
        self.system_memory = self._load_system_memory()

    def _load_system_memory(self) -> str:
        SYSTEM_MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        if not self.system_memory_path.exists():
            self.system_memory_path.write_text(
                "# Light System Memory\n\n(autocreated)\n", encoding="utf-8"
            )
        return self.system_memory_path.read_text(encoding="utf-8")

    def format_report(self, data: dict) -> str:
        """Return a simple formatted string.
        In a real system this would invoke the LIGHT model to polish and
        structure a concise, faithful operator-facing summary.
        """
        lines = []
        for k, v in data.items():
            lines.append(f"**{k}**: {v}")
        return "\n".join(lines)


if __name__ == "__main__":
    l = Light()
    print(l.format_report({"status": "ok", "detail": "example"}))
