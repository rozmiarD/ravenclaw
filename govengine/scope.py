from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol
from urllib.parse import urlparse

from govengine.context import ravenclaw_context


_DOMAIN_PATTERN = re.compile(r'(?:\*\.)?(?:[a-z0-9-]+\.)+[a-z]{2,}', re.IGNORECASE)


class GovScopePort(Protocol):
    """Neutral host/scope policy port for GovEngine helpers."""

    def extract_host(self, value: Any) -> str:
        ...

    def host_in_scope(self, host: str, scope_domains: Any) -> bool:
        ...


@dataclass(frozen=True)
class FunctionalScopePort:
    """Scope port backed by host-provided functions.

    Ravenclaw supplies its campaign scope helpers here during package-in-place
    extraction. A future GovEngine consumer can provide equivalent functions
    without importing Ravenclaw campaign modules.
    """

    extract_host_fn: Callable[[Any], Any]
    host_in_scope_fn: Callable[[str, Any], bool]

    def extract_host(self, value: Any) -> str:
        return str(self.extract_host_fn(value) or '').strip().lower()

    def host_in_scope(self, host: str, scope_domains: Any) -> bool:
        return bool(self.host_in_scope_fn(str(host or '').strip().lower(), scope_domains))


def extract_host_from_url(url: Any) -> str:
    """Extract a lowercase host from a URL-like scalar."""

    text = str(url or '').strip()
    if not text:
        return ''
    try:
        parsed = urlparse(text)
        host = (parsed.hostname or '').strip().lower()
        if host:
            return host
        if '://' not in text and '.' in text and not any(ch.isspace() for ch in text):
            parsed = urlparse('//' + text)
            return (parsed.hostname or '').strip().lower()
    except Exception:
        return ''
    return ''


def _split_campaign_in_out(text: str) -> tuple[str, str]:
    t = text or ''
    low = t.lower()
    markers = ['\nout of scope\n', '\nout of scope:', '\nscope exclusions\n', '\nscope exclusions:']
    idx = -1
    for marker in markers:
        hit = low.find(marker)
        if hit != -1:
            idx = hit if idx == -1 else min(idx, hit)
    if idx == -1:
        return t, ''
    return t[:idx], t[idx:]


def _to_exact_suffix(domains: List[str]) -> tuple[set[str], set[str]]:
    exact: set[str] = set()
    suffix: set[str] = set()
    for item in domains:
        domain = str(item or '').strip().lower()
        if not domain:
            continue
        if domain.startswith('*.'):
            suffix.add(domain[2:])
        else:
            exact.add(domain)
    return exact, suffix


def _load_selected_blueprint_scope(repo_root: Path) -> Dict[str, List[str]]:
    planner_ui = repo_root / 'reports' / '.planner.ui.state.json'
    registry_root = repo_root / 'reports' / 'campaign_registry'
    try:
        if not planner_ui.exists():
            return {'domains': [], 'out_of_scope_targets': []}
        ui = json.loads(planner_ui.read_text(encoding='utf-8'))
        key = str((ui or {}).get('selected_campaign_key') or '').strip()
        if not key:
            return {'domains': [], 'out_of_scope_targets': []}
        latest = registry_root / key / 'latest.json'
        if not latest.exists():
            return {'domains': [], 'out_of_scope_targets': []}
        meta = json.loads(latest.read_text(encoding='utf-8'))
        raw_path = Path(str(meta.get('path') or ''))
        version_path = raw_path if raw_path.is_absolute() else (latest.parent / raw_path)
        bp_json = version_path / 'blueprint.json'
        if not bp_json.exists():
            return {'domains': [], 'out_of_scope_targets': []}
        bp = json.loads(bp_json.read_text(encoding='utf-8'))
        structured_scope = (bp.get('structured_scope') or {}) if isinstance(bp, dict) else {}
        domains = structured_scope.get('authoritative_domains', structured_scope.get('domains')) if isinstance(structured_scope, dict) else []
        out_scope = structured_scope.get('out_of_scope_targets') if isinstance(structured_scope, dict) else []
        return {
            'domains': [str(d).strip().lower() for d in domains or [] if str(d).strip()],
            'out_of_scope_targets': [str(d).strip().lower() for d in out_scope or [] if str(d).strip()],
        }
    except Exception:
        return {'domains': [], 'out_of_scope_targets': []}


def load_scope_domains(scope_text: str | None = None, *, repo_root: Path | None = None) -> Dict[str, List[str]]:
    """Load exact/suffix scope domains without importing Ravenclaw campaign_utils.

    If ``scope_text`` is omitted, this compatibility helper reads Ravenclaw-style
    scope files from the discovered repository root. Standalone GovEngine
    consumers should usually pass scope text/data explicitly or supply a
    ``GovScopePort``.
    """

    root = (repo_root or ravenclaw_context(Path(__file__)).repo_root).resolve()
    if scope_text is None:
        scope_path = root / 'scope' / 'scope.txt'
        try:
            scope_text = scope_path.read_text(encoding='utf-8')
        except FileNotFoundError:
            scope_text = ''
    in_text, out_text = _split_campaign_in_out(scope_text or '')
    in_domains = [m.lower() for m in _DOMAIN_PATTERN.findall(in_text)]
    out_domains = [m.lower() for m in _DOMAIN_PATTERN.findall(out_text)]

    bps = _load_selected_blueprint_scope(root)
    in_domains.extend(bps.get('domains', []))
    out_domains.extend(bps.get('out_of_scope_targets', []))

    exact, suffix = _to_exact_suffix(in_domains)
    excl_exact, excl_suffix = _to_exact_suffix(out_domains)
    exact -= excl_exact
    suffix -= excl_suffix
    return {
        'exact': sorted(exact),
        'suffix': sorted(suffix),
        'exclude_exact': sorted(excl_exact),
        'exclude_suffix': sorted(excl_suffix),
    }


def host_in_scope(host: str, domains: Optional[Dict[str, List[str]]] = None) -> bool:
    host = (host or '').lower().strip()
    if not host:
        return False
    if domains is None:
        domains = load_scope_domains()
    if host in domains.get('exclude_exact', []):
        return False
    for suffix in domains.get('exclude_suffix', []):
        if host == suffix or host.endswith('.' + suffix):
            return False
    if host in domains.get('exact', []):
        return True
    for suffix in domains.get('suffix', []):
        if host == suffix or host.endswith('.' + suffix):
            return True
    return False
