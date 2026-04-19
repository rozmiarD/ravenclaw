from __future__ import annotations

import os
from pathlib import Path

DEFAULT_WORKSPACE = str(Path(__file__).resolve().parents[1])

WORKSPACE = Path(os.getenv("RAVENCLAW_WORKSPACE") or DEFAULT_WORKSPACE).resolve()
OPENCLAW_HOME = Path(os.getenv("OPENCLAW_HOME") or str(WORKSPACE.parent)).resolve()
ENGINE_DIR = WORKSPACE / "engine"
REPORTS_DIR = WORKSPACE / "reports"
REPORTS_STATE_DIR = REPORTS_DIR / "state"
REPORTS_CACHE_DIR = REPORTS_DIR / "cache"
LOGS_DIR = WORKSPACE / "logs"
LOGDASH_DIR = WORKSPACE / "logdash"
SCOPE_DIR = WORKSPACE / "scope"
CHANGELOG_PATH = WORKSPACE / "CHANGELOG.md"
OPENCLAW_CONFIG_PATH = Path(os.getenv("OPENCLAW_CONFIG_PATH") or str(OPENCLAW_HOME / "openclaw.json")).resolve()
OPENCLAW_ENV_PATH = Path(os.getenv("OPENCLAW_ENV_PATH") or str(OPENCLAW_HOME / ".env")).resolve()
RUNTIME_PLAN_PATH = REPORTS_STATE_DIR / "public_targets_plan.json"
LEGACY_RUNTIME_PLAN_PATH = ENGINE_DIR / "public_targets_plan.json"
CONTEXT_SUMMARY_PATH = REPORTS_CACHE_DIR / "context_summary.json"
LEGACY_CONTEXT_SUMMARY_PATH = ENGINE_DIR / "context_summary.json"


def wp(*parts: str) -> Path:
    return WORKSPACE.joinpath(*parts)


def ep(*parts: str) -> Path:
    return ENGINE_DIR.joinpath(*parts)


def rp(*parts: str) -> Path:
    return REPORTS_DIR.joinpath(*parts)


def rsp(*parts: str) -> Path:
    return REPORTS_STATE_DIR.joinpath(*parts)


def rcp(*parts: str) -> Path:
    return REPORTS_CACHE_DIR.joinpath(*parts)


def first_existing(*paths: Path) -> Path:
    candidates = [Path(p) for p in paths if p is not None]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0] if candidates else Path()
