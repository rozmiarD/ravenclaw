from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse

DOMAIN_RE = re.compile(r"^(\*\.)?(?:[a-z0-9-]+\.)+[a-z]{2,}$", re.IGNORECASE)
CONCAT_TLD_RE = re.compile(r"\.(com|net|org|io|app|dev|ai)(?=[a-z])", re.IGNORECASE)
INLINE_DOMAIN_RE = re.compile(r"(?:\*\.)?(?:[a-z0-9-]+\.)+[a-z]{2,}", re.IGNORECASE)
URL_RE = re.compile(r"https?://[^\s\"'<>`]+", re.IGNORECASE)


def _extract_scope_lines(lines: List[str]) -> List[str]:
    in_scope = False
    scope_items: List[str] = []
    for raw in lines:
        line = raw.rstrip("\n")
        if line.strip().lower() == "## campaign scope":
            in_scope = True
            continue
        if in_scope and line.strip().startswith("## "):
            break
        if not in_scope:
            continue
        if line.strip().startswith("-"):
            scope_items.append(line.strip()[1:].strip())
    return scope_items


def _extract_modern_scope_region(text: str) -> str:
    t = text or ""
    low = t.lower()
    scope_markers = ["\nin scope\n", "\nin scope:", "\nscope\n", "\nscope:", "\nassets eligible:", "\neligible targets:"]
    asset_markers = ["\nhighest impact scope", "\nlower impact scope", "\nin scope also:", "\ntier 1:", "\ntier 2:"]
    out_markers = ["\nout of scope\n", "\nout of scope:", "\nscope exclusions\n", "\nscope exclusions:", "\ncore ineligible findings\n"]

    scope_idx = -1
    for marker in asset_markers:
        idx = low.find(marker)
        if idx != -1:
            scope_idx = idx if scope_idx == -1 else min(scope_idx, idx)
    if scope_idx == -1:
        for marker in scope_markers:
            idx = low.rfind(marker)
            if idx != -1:
                scope_idx = max(scope_idx, idx)

    out_idx = -1
    for marker in out_markers:
        idx = low.find(marker, max(scope_idx + 1, 0)) if scope_idx != -1 else low.find(marker)
        if idx != -1:
            out_idx = idx if out_idx == -1 else min(out_idx, idx)

    if scope_idx == -1:
        return t[:out_idx] if out_idx != -1 else t
    return t[scope_idx:out_idx] if out_idx != -1 and out_idx > scope_idx else t[scope_idx:]


def _extract_modern_scope_items(text: str) -> List[str]:
    region = _extract_modern_scope_region(text)
    items: List[str] = []
    seen: set[str] = set()
    for raw in region.splitlines():
        line = str(raw or "").strip()
        if not line:
            continue
        low = line.lower()
        if any(low.startswith(prefix) for prefix in [
            'response targets',
            'disclosure policy',
            'responsible disclosure policy',
            'important notice',
            'terms & conditions',
            'prohibitions',
            'report vulnerabilities at:',
        ]):
            continue
        for match in URL_RE.finditer(line):
            url = str(match.group(0) or '').strip().rstrip('.,;')
            if url and url not in seen:
                seen.add(url)
                items.append(url)
        url_hosts = {str(urlparse(u).hostname or '').strip().lower() for u in items if u.startswith(('http://', 'https://'))}
        for match in INLINE_DOMAIN_RE.finditer(line):
            token = str(match.group(0) or '').strip().lower().strip("()[]<>'\"`")
            start = int(match.start())
            if start > 0 and line[start - 1] == '@':
                continue
            if token in url_hosts:
                continue
            if token and token not in seen:
                seen.add(token)
                items.append(token)
    return items


def _is_valid_scope_target(target: str) -> bool:
    item = str(target or '').strip().lower()
    if not item:
        return False
    if item.startswith(('http://', 'https://')):
        parsed = urlparse(item)
        host = str(parsed.hostname or '').strip().lower()
        return bool(host and DOMAIN_RE.match(host))
    return bool(DOMAIN_RE.match(item))


def validate_campaign(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    result: Dict[str, Any] = {
        "ok": True,
        "errors": [],
        "warnings": [],
        "scope_targets": 0,
        "valid_targets": 0,
    }
    if not p.exists():
        result["ok"] = False
        result["errors"].append("campaign_not_found")
        return result

    text = p.read_text(encoding="utf-8", errors="replace")
    scope_items = _extract_scope_lines(text.splitlines())
    if not scope_items:
        scope_items = _extract_modern_scope_items(text)
    result["scope_targets"] = len(scope_items)
    if not scope_items:
        result["ok"] = False
        result["errors"].append("campaign_scope_empty")
        return result

    for item in scope_items:
        target = item.strip().lower()
        if not target:
            result["errors"].append("empty_scope_target")
            continue

        if " " in target:
            result["errors"].append(f"invalid_scope_target_whitespace:{item}")
            continue

        if CONCAT_TLD_RE.search(target):
            result["warnings"].append(f"possible_concatenated_domain:{item}")

        if not _is_valid_scope_target(target):
            result["errors"].append(f"invalid_scope_target_format:{item}")
            continue

        result["valid_targets"] += 1

    if result["errors"]:
        result["ok"] = False
    return result
