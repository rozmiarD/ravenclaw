from __future__ import annotations

import re
from typing import Any, Callable, Dict, Iterable, List, Mapping, Tuple

HOST_TOKEN_RE = re.compile(r"(https?://[^\s\"'<>]+)|\b((?:[a-z0-9-]+\.)+[a-z]{2,})\b", re.IGNORECASE)

ExtractHost = Callable[[Any], Any]
HostInScope = Callable[[str, Any], bool]
NormalizeTool = Callable[[Any], str]
RestrictedPatternCheck = Callable[[Any, Iterable[Any]], Tuple[bool, str]]


def normalize_argv(
    tool: Any,
    args: Iterable[Any],
    *,
    allowed_tools: Iterable[str],
    contains_tool_restricted_patterns: RestrictedPatternCheck,
    normalize_tool: NormalizeTool,
    approved_spec: bool = False,
) -> List[str]:
    """Normalize one tool invocation without executing it."""

    norm_tool = normalize_tool(tool)
    if not norm_tool:
        raise ValueError('missing_tool')
    allowed = {str(item).strip().lower() for item in allowed_tools if str(item).strip()}
    if norm_tool not in allowed:
        reason = 'tool_not_allowed_for_approved_spec' if approved_spec else 'tool_not_allowed'
        raise ValueError(f'{reason}:{norm_tool}')
    normalized_args = [str(a) for a in (args or [])]
    if norm_tool == 'curl' and '-q' not in normalized_args and '--disable' not in normalized_args:
        normalized_args = ['-q'] + normalized_args
    restricted, restricted_pattern = contains_tool_restricted_patterns(norm_tool, normalized_args)
    if restricted:
        raise ValueError(f'tool_restricted_pattern:{norm_tool}:{restricted_pattern}')
    return [norm_tool] + normalized_args


def extract_hosts_from_text(text: Any, *, extract_host_from_url: ExtractHost) -> List[str]:
    raw = str(text or '').strip()
    if not raw:
        return []
    raw_lower = raw.lower()
    if raw_lower.startswith('file://'):
        return []
    hosts: List[str] = []
    seen: set[str] = set()
    direct = str(extract_host_from_url(raw) or '').strip().lower()
    if direct:
        seen.add(direct)
        hosts.append(direct)
    allow_bare_domain_match = ('/' not in raw and '\\' not in raw) or 'host:' in raw_lower
    for match in HOST_TOKEN_RE.finditer(raw):
        if match.group(1):
            token = str(match.group(1) or '').strip().lower()
        else:
            if not allow_bare_domain_match:
                continue
            token = str(match.group(2) or '').strip().lower()
        host = str(extract_host_from_url(token) or token).strip().lower()
        if host and host not in seen:
            seen.add(host)
            hosts.append(host)
    return hosts


def arg_target_observations(argv: List[str], *, extract_host_from_url: ExtractHost, stdin_text: Any = '') -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {'urls': [], 'hosts': [], 'files': []}
    seen: Dict[str, set[str]] = {'urls': set(), 'hosts': set(), 'files': set()}

    def _observe(raw_value: Any) -> None:
        raw = str(raw_value or '').strip()
        if not raw or raw.startswith('-'):
            return
        lowered = raw.lower()
        if lowered.startswith(('http://', 'https://')):
            if lowered not in seen['urls']:
                seen['urls'].add(lowered)
                out['urls'].append(raw)
            return
        if lowered.startswith('file://'):
            if lowered not in seen['files']:
                seen['files'].add(lowered)
                out['files'].append(raw)
            return
        if any(ch.isspace() for ch in raw) or '/' in raw or '\\' in raw:
            return
        host = str(extract_host_from_url(raw) or raw).strip().lower()
        if not host or '.' not in host:
            return
        if host not in seen['hosts']:
            seen['hosts'].add(host)
            out['hosts'].append(host)

    for token in argv[1:]:
        _observe(token)
    for line in str(stdin_text or '').splitlines():
        _observe(line)
    return out


def enforce_target_semantics(
    argv: List[str],
    *,
    tool_catalog: Mapping[str, Mapping[str, Any]],
    normalize_tool: NormalizeTool,
    extract_host_from_url: ExtractHost,
    stdin_text: Any = '',
) -> None:
    tool = normalize_tool(argv[0] if argv else '')
    if not tool:
        return
    info = tool_catalog.get(tool) or {}
    target_validation_mode = str(info.get('target_validation_mode') or 'none').strip().lower() or 'none'
    observed = arg_target_observations(argv, extract_host_from_url=extract_host_from_url, stdin_text=stdin_text)

    if target_validation_mode == 'strict_url':
        if observed['files'] and not observed['urls']:
            return
        if not observed['urls']:
            raise ValueError(f'missing_target_kind:{tool}:url')
        return

    if target_validation_mode == 'strict_host_domain':
        if observed['urls']:
            raise ValueError(f'invalid_target_kind:{tool}:url')
        if not observed['hosts']:
            raise ValueError(f'missing_target_kind:{tool}:host_or_domain')


def enforce_scope(
    argv: List[str],
    *,
    scope_domains: Any,
    host_in_scope: HostInScope,
    tool_catalog: Mapping[str, Mapping[str, Any]],
    normalize_tool: NormalizeTool,
    extract_host_from_url: ExtractHost,
    stdin_text: Any = '',
) -> None:
    """Enforce target semantics and scope using host-supplied scope policy."""

    enforce_target_semantics(
        argv,
        tool_catalog=tool_catalog,
        normalize_tool=normalize_tool,
        extract_host_from_url=extract_host_from_url,
        stdin_text=stdin_text,
    )
    for token in [*argv[1:], *str(stdin_text or '').splitlines()]:
        for host in extract_hosts_from_text(token, extract_host_from_url=extract_host_from_url):
            if not host_in_scope(host, scope_domains):
                raise ValueError(f'out_of_scope_target:{host}')
