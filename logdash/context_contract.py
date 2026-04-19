from __future__ import annotations

from typing import Any


def require_ctx(ctx: dict[str, Any], *required_keys: str) -> dict[str, Any]:
    missing = [key for key in required_keys if key not in ctx]
    if missing:
        raise KeyError(f"Missing Logdash API context keys: {', '.join(missing)}")
    return ctx
