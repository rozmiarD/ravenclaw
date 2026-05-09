from __future__ import annotations

"""Ravenclaw compatibility entrypoint for GovEngine's optional security profile.

GovEngine 0.1.5 introduced ``govengine.security_profile``. Ravenclaw's public
package floor now expects that upstream facade, while this module keeps a small
host-side compatibility seam for older local environments: use the upstream
facade when it exists, otherwise expose the same discovery shape from the
surface registry and direct module imports.
"""

from dataclasses import dataclass, field
from importlib import import_module
from types import ModuleType
from typing import Any, Dict, Iterable, Tuple


@dataclass(frozen=True)
class SecurityProfileGroup:
    name: str
    modules: Tuple[str, ...]
    claim: str
    non_claims: Tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'modules': list(self.modules),
            'claim': self.claim,
            'non_claims': list(self.non_claims),
        }


def _tuple(values: Iterable[str]) -> Tuple[str, ...]:
    return tuple(str(value) for value in values)


def _upstream_module() -> ModuleType | None:
    try:
        return import_module('govengine.security_profile')
    except ModuleNotFoundError as exc:
        if exc.name == 'govengine.security_profile':
            return None
        raise


def _fallback_groups() -> Tuple[SecurityProfileGroup, ...]:
    return (
        SecurityProfileGroup(
            name='action_tooling',
            modules=_tuple((
                'govengine.action_schema',
                'govengine.action_validators',
                'govengine.action_compiler',
                'govengine.capability_recipes',
                'govengine.tool_registry',
                'govengine.semantic_loss_policy',
            )),
            claim='Security-oriented action shape, capability, tool, and semantic-loss helpers.',
            non_claims=_tuple(('scanner implementation', 'live exploit capability', 'target authorization')),
        ),
        SecurityProfileGroup(
            name='policy_scope',
            modules=_tuple(('govengine.policy.core', 'govengine.policy.gateway', 'govengine.scope')),
            claim='Reusable policy gateway and scope-port helpers for host-owned security workflows.',
            non_claims=_tuple(('host policy source-of-truth ownership', 'operator approval workflow ownership')),
        ),
        SecurityProfileGroup(
            name='review_contracts',
            modules=_tuple((
                'govengine.contracts.signal',
                'govengine.contracts.analysis',
                'govengine.contracts.evidence_policy',
            )),
            claim='Signal, analysis, and confirmation-evidence policy contracts for reviewable outcomes.',
            non_claims=_tuple(('raw evidence storage', 'finding publication or disclosure authority')),
        ),
    )


def govengine_security_profile_available() -> bool:
    return _upstream_module() is not None


def security_profile_groups() -> Tuple[Any, ...]:
    upstream = _upstream_module()
    if upstream is not None:
        return tuple(upstream.security_profile_groups())
    return _fallback_groups()


def security_profile_module_names() -> Tuple[str, ...]:
    upstream = _upstream_module()
    if upstream is not None:
        return tuple(upstream.security_profile_module_names())
    try:
        from govengine import security_profile_surface  # type: ignore

        return tuple(security_profile_surface().modules)
    except Exception:
        return tuple(module for group in _fallback_groups() for module in group.modules)


def security_profile_index() -> Dict[str, Any]:
    upstream = _upstream_module()
    if upstream is not None:
        payload = dict(upstream.security_profile_index())
        payload['source'] = 'govengine.security_profile'
        return payload

    try:
        from govengine import security_profile_surface  # type: ignore

        surface = security_profile_surface().as_dict()
    except Exception:
        surface = {
            'name': 'security_profile_helpers',
            'status': 'pre_alpha_optional_profile',
            'modules': list(security_profile_module_names()),
            'claim': 'Optional security-oriented helper surface for Ravenclaw-style hosts.',
            'non_claims': [
                'live exploit/scanner capability',
                'authorization to test targets',
                'OpenClaw/MCP/A2A adapter ownership',
            ],
            'optional_profile': True,
        }
    return {
        'entrypoint': 'engine.govengine_security_profile',
        'source': 'ravenclaw_compat_fallback',
        'surface': surface,
        'groups': [group.as_dict() for group in _fallback_groups()],
    }


def import_security_profile_module(module_name: str) -> ModuleType:
    upstream = _upstream_module()
    if upstream is not None:
        return upstream.import_security_profile_module(module_name)

    normalized = str(module_name)
    allowed = set(security_profile_module_names())
    if normalized not in allowed:
        raise KeyError(normalized)
    return import_module(normalized)


def assert_security_profile_boundary() -> None:
    upstream = _upstream_module()
    if upstream is not None:
        upstream.assert_security_profile_boundary()
        return

    modules = set(security_profile_module_names())
    assert 'govengine.core' not in modules
    assert 'govengine.execution.gate' not in modules
    payload = security_profile_index()
    assert payload['surface']['name'] == 'security_profile_helpers'
    assert payload['surface']['optional_profile'] is True
