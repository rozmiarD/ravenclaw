from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Protocol

from sclite.integrity import verify_artifact_chain_manifest


class GovSCLiteLifecycleVerifier(Protocol):
    """Port around SCLite lifecycle verification."""

    def verify(self, manifest: Mapping[str, Any], *, root: Path) -> dict[str, Any]:
        ...


def verify_lifecycle_manifest(manifest: Mapping[str, Any], *, root: Path) -> dict[str, Any]:
    """Verify a v0.2 SCLite lifecycle manifest through the GovEngine seam."""

    return verify_artifact_chain_manifest(manifest, root=root)
