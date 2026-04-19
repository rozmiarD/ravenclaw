import re
import json
from pathlib import Path
from urllib.parse import urlparse
from typing import Dict, List, Optional

from paths import wp  # type: ignore

WORKSPACE_DIR = wp().resolve()
SCOPE_DIR = WORKSPACE_DIR / 'scope'
DEFAULT_SCOPE_PATH = SCOPE_DIR / 'scope.txt'
PLANNER_UI_STATE_PATH = WORKSPACE_DIR / "reports" / ".planner.ui.state.json"
CAMPAIGN_REGISTRY_ROOT = WORKSPACE_DIR / "reports" / "campaign_registry"

_DOMAIN_PATTERN = re.compile(r'(?:\*\.)?(?:[a-z0-9-]+\.)+[a-z]{2,}', re.IGNORECASE)


def resolve_scope_text_path() -> Path:
    try:
        if PLANNER_UI_STATE_PATH.exists():
            ui = json.loads(PLANNER_UI_STATE_PATH.read_text(encoding='utf-8'))
            raw = str((ui or {}).get('scope_txt') or '').strip()
            if raw:
                p = Path(raw)
                if not p.is_absolute():
                    p = WORKSPACE_DIR / raw
                if p.exists():
                    return p
                scope_candidate = SCOPE_DIR / raw
                if scope_candidate.exists():
                    return scope_candidate
    except Exception:
        pass
    return DEFAULT_SCOPE_PATH


def _load_scope_text() -> str:
    try:
        return resolve_scope_text_path().read_text(encoding='utf-8')
    except FileNotFoundError:
        return ''




def _load_selected_blueprint_scope() -> Dict[str, List[str]]:
    try:
        if not PLANNER_UI_STATE_PATH.exists():
            return {"domains": [], "out_of_scope_targets": []}
        ui = json.loads(PLANNER_UI_STATE_PATH.read_text(encoding='utf-8'))
        key = str((ui or {}).get('selected_campaign_key') or '').strip()
        if not key:
            return {"domains": [], "out_of_scope_targets": []}
        latest = CAMPAIGN_REGISTRY_ROOT / key / 'latest.json'
        if not latest.exists():
            return {"domains": [], "out_of_scope_targets": []}
        meta = json.loads(latest.read_text(encoding='utf-8'))
        raw_path = Path(str(meta.get('path') or ''))
        version_path = raw_path if raw_path.is_absolute() else (latest.parent / raw_path)
        bp_json = version_path / 'blueprint.json'
        if not bp_json.exists():
            return {"domains": [], "out_of_scope_targets": []}
        bp = json.loads(bp_json.read_text(encoding='utf-8'))
        ss = (bp.get('structured_scope') or {}) if isinstance(bp, dict) else {}
        domains = ss.get('authoritative_domains', ss.get('domains')) if isinstance(ss, dict) else []
        out_scope = ss.get('out_of_scope_targets') if isinstance(ss, dict) else []
        return {
            "domains": [str(d).strip().lower() for d in domains or [] if str(d).strip()],
            "out_of_scope_targets": [str(d).strip().lower() for d in out_scope or [] if str(d).strip()],
        }
    except Exception:
        return {"domains": [], "out_of_scope_targets": []}


def _split_campaign_in_out(text: str) -> tuple[str, str]:
    t = text or ''
    low = t.lower()
    markers = ['\nout of scope\n', '\nout of scope:', '\nscope exclusions\n', '\nscope exclusions:']
    idx = -1
    for m in markers:
        i = low.find(m)
        if i != -1:
            idx = i if idx == -1 else min(idx, i)
    if idx == -1:
        return t, ''
    return t[:idx], t[idx:]


def _to_exact_suffix(domains: List[str]) -> tuple[set[str], set[str]]:
    exact: set[str] = set()
    suffix: set[str] = set()
    for d in domains:
        domain = str(d or '').strip().lower()
        if not domain:
            continue
        if domain.startswith('*.'):
            suffix.add(domain[2:])
        else:
            exact.add(domain)
    return exact, suffix


def load_scope_domains() -> Dict[str, List[str]]:
    text = _load_scope_text()
    in_text, out_text = _split_campaign_in_out(text)

    in_domains = [m.lower() for m in _DOMAIN_PATTERN.findall(in_text)]
    out_domains = [m.lower() for m in _DOMAIN_PATTERN.findall(out_text)]

    bps = _load_selected_blueprint_scope()
    in_domains.extend(bps.get('domains', []))
    out_domains.extend(bps.get('out_of_scope_targets', []))

    exact, suffix = _to_exact_suffix(in_domains)
    excl_exact, excl_suffix = _to_exact_suffix(out_domains)

    # remove explicit exclusions from explicit in-scope lists
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

    # deny-first: explicit out-of-scope target exclusion has priority over wildcard include
    if host in domains.get('exclude_exact', []):
        return False
    for suffix in domains.get('exclude_suffix', []):
        if host == suffix or host.endswith('.' + suffix):
            return False

    if host in domains.get('exact', []):
        return True
    for suffix in domains.get('suffix', []):
        if host == suffix:
            return True
        if host.endswith('.' + suffix):
            return True
    return False


def load_scope_targets() -> List[Dict[str, str]]:
    domains = load_scope_domains()
    targets: List[Dict[str, str]] = []
    for item in domains.get('exact', []):
        text = str(item or '').strip()
        if text:
            targets.append({'name': text, 'type': 'host', 'scope': 'selected scope'})
    for item in domains.get('suffix', []):
        text = str(item or '').strip()
        if text:
            targets.append({'name': f'*.{text}', 'type': 'host', 'scope': 'selected scope'})
    return targets


def summarize_scope() -> str:
    targets = load_scope_targets()
    if not targets:
        return ""
    summary_lines = []
    for t in targets:
        name = t.get('name', 'Unknown')
        scope = t.get('scope', '')
        aggression = t.get('aggression', 'N/A')
        summary_lines.append(f"{name} (aggr {aggression}): {scope}")
    return '\n'.join(summary_lines)


def extract_host_from_url(url: str) -> str:
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or '').strip().lower()
        return host
    except Exception:
        return ''
