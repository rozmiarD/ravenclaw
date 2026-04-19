from __future__ import annotations

import sys
from pathlib import Path

# Make engine modules importable when tests are run from repo root.
ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from campaign_utils import host_in_scope  # type: ignore


def test_wildcard_allow_with_exact_exclude() -> None:
    scope = {
        "exact": [],
        "suffix": ["ravenclaw.org"],
        "exclude_exact": ["api.ravenclaw.org"],
        "exclude_suffix": [],
    }
    assert host_in_scope("api.ravenclaw.org", scope) is False
    assert host_in_scope("www.ravenclaw.org", scope) is True
    assert host_in_scope("ravenclaw.org", scope) is True


def test_wildcard_exclude_blocks_subtree() -> None:
    scope = {
        "exact": [],
        "suffix": ["ravenclaw.org"],
        "exclude_exact": [],
        "exclude_suffix": ["internal.ravenclaw.org"],
    }
    assert host_in_scope("internal.ravenclaw.org", scope) is False
    assert host_in_scope("dev.internal.ravenclaw.org", scope) is False
    assert host_in_scope("app.ravenclaw.org", scope) is True


def test_exclude_has_priority_over_allow_exact_and_wildcard() -> None:
    scope = {
        "exact": ["api.ravenclaw.org"],
        "suffix": ["ravenclaw.org"],
        "exclude_exact": ["api.ravenclaw.org"],
        "exclude_suffix": [],
    }
    assert host_in_scope("api.ravenclaw.org", scope) is False
