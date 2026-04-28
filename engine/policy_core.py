from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple
from pathlib import Path
import yaml

from tool_registry import get_execution_allowed_tools, get_planner_visible_tools, get_tool_catalog  # type: ignore


DEFAULT_ALLOWED_TOOLS = {"curl", "ffuf", "nmap", "gobuster", "nikto", "sqlmap"}
DEFAULT_BRAIN_ALLOWED_TOOLS = (
    "amass",
    "curl",
    "dig",
    "dnsx",
    "ffuf",
    "gobuster",
    "httpx",
    "nikto",
    "nmap",
    "nslookup",
    "nuclei",
    "sqlmap",
    "subfinder",
    "whatweb",
)
PUBLIC_RUNTIME_BLOCKED_TOOLS = {
    "bash", "sh", "python", "python3", "perl", "ruby", "node", "php", "lua", "busybox",
    "ssh", "scp", "rsync", "systemctl", "service", "journalctl",
    "aircrack-ng", "aireplay-ng", "airmon-ng", "airodump-ng", "hcxdumptool", "hcxpcapngtool", "reaver", "wash", "wifite",
    "hydra", "masscan",
}
PUBLIC_RUNTIME_BLOCKED_CATEGORIES = {"operator_support"}
PUBLIC_RUNTIME_BLOCKED_CAPABILITIES = {"operator_shell", "auth_bruteforce", "wireless_assessment"}
APPROVED_SPEC_BLOCKED_TOOLS = set(PUBLIC_RUNTIME_BLOCKED_TOOLS)
APPROVED_SPEC_BLOCKED_CATEGORIES = set(PUBLIC_RUNTIME_BLOCKED_CATEGORIES)
APPROVED_SPEC_BLOCKED_CAPABILITIES = set(PUBLIC_RUNTIME_BLOCKED_CAPABILITIES)
BANNED_PATTERNS = ["--flood", "--rate", "slowloris", "benchmark", "stress"]
TOOL_ARG_BLOCKLIST = {
    "curl": {"-k", "--config", "-o", "--output", "-O", "--remote-name", "--remote-name-all", "--upload-file", "-T", "--data-binary", "@"},
    "httpx": {"-config", "-o", "-oa", "-sr", "-srd", "-rr", "-store-response", "-json-export", "-include-response"},
    "ffuf": {"-config", "-o", "-od", "-of", "-request", "-request-proto", "-replay-proxy"},
    "nuclei": {"-config", "-o", "-je", "-jle", "-sresp", "-srd", "-proxy", "-proxy-socks-url"},
    "katana": {"-config", "-o", "-output", "-store-response", "-store-response-dir", "-proxy"},
    "nikto": {"-config", "-output", "-format", "-save", "-useproxy"},
    "whatweb": {"--log-json", "--log-json-verbose", "--log-brief", "--log-verbose", "--log-xml", "--log-sql", "--proxy"},
    "gau": {"--config", "--o", "--proxy"},
    "hakrawler": {"-proxy"},
    "dnsx": {"-l", "-list", "-w", "-wordlist", "-o", "-output", "-proxy"},
    "subfinder": {"-dl", "-list", "-o", "-od", "-output", "-output-dir", "-config", "-pc", "-provider-config", "-rl", "-rlist", "-proxy"},
}
WHITELIST_PATH = Path(__file__).resolve().parents[1] / "whitelist.yaml"


def _load_whitelist_config() -> Dict[str, Any]:
    try:
        data = yaml.safe_load(WHITELIST_PATH.read_text(encoding="utf-8")) or {}
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _normalize_tool_list(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {str(c).strip().lower() for c in value if str(c).strip()}


def load_allowed_tools() -> set[str]:
    registry_tools = get_execution_allowed_tools()
    if registry_tools:
        return registry_tools
    data = _load_whitelist_config()
    cmds = _normalize_tool_list(data.get("allowed_commands", []))
    return cmds or set(DEFAULT_ALLOWED_TOOLS)


def load_brain_allowed_tools(profiles: Iterable[str] | str | None = None) -> tuple[str, ...]:
    registry_tools = tuple(get_planner_visible_tools(profiles))
    if registry_tools:
        return registry_tools
    data = _load_whitelist_config()
    brain_cmds = _normalize_tool_list(data.get("brain_allowed_commands", []))
    allowed = load_allowed_tools()
    if brain_cmds:
        brain_cmds &= allowed
        if brain_cmds:
            return tuple(sorted(brain_cmds))
    fallback = tuple(sorted(t for t in DEFAULT_BRAIN_ALLOWED_TOOLS if t in allowed))
    if fallback:
        return fallback
    return tuple(sorted(t for t in allowed if t in DEFAULT_ALLOWED_TOOLS))


def _apply_public_runtime_boundary(allowed: Iterable[str]) -> set[str]:
    catalog = get_tool_catalog()
    out: set[str] = set()
    for tool in {str(x).strip().lower() for x in allowed if str(x).strip()}:
        info = catalog.get(tool) or {}
        category = str(info.get('category') or '').strip().lower()
        capabilities = {str(x).strip().lower() for x in (info.get('capabilities') or []) if str(x).strip()}
        if tool in PUBLIC_RUNTIME_BLOCKED_TOOLS:
            continue
        if category in PUBLIC_RUNTIME_BLOCKED_CATEGORIES:
            continue
        if capabilities & PUBLIC_RUNTIME_BLOCKED_CAPABILITIES:
            continue
        out.add(tool)
    return out


def get_runtime_allowed_tools() -> set[str]:
    return _apply_public_runtime_boundary(load_allowed_tools())


def get_runtime_brain_allowed_tools(profiles: Iterable[str] | str | None = None) -> tuple[str, ...]:
    return load_brain_allowed_tools(profiles)


def get_approved_spec_allowed_tools() -> set[str]:
    allowed = set(get_runtime_allowed_tools())
    catalog = get_tool_catalog()
    out: set[str] = set()
    for tool in sorted(allowed):
        info = catalog.get(tool) or {}
        category = str(info.get('category') or '').strip().lower()
        capabilities = {str(x).strip().lower() for x in (info.get('capabilities') or []) if str(x).strip()}
        if tool in APPROVED_SPEC_BLOCKED_TOOLS:
            continue
        if category in APPROVED_SPEC_BLOCKED_CATEGORIES:
            continue
        if capabilities & APPROVED_SPEC_BLOCKED_CAPABILITIES:
            continue
        out.add(tool)
    return out


def get_runtime_tool_policy(profiles: Iterable[str] | str | None = None) -> Dict[str, Any]:
    allowed = get_runtime_allowed_tools()
    planner_allowed = get_runtime_brain_allowed_tools(profiles)
    return {
        'execution_allowed_tools': set(allowed),
        'approved_spec_allowed_tools': set(get_approved_spec_allowed_tools()),
        'planner_allowed_tools': tuple(planner_allowed),
        'profiles': list(profiles) if isinstance(profiles, (list, tuple, set)) else ([str(profiles)] if isinstance(profiles, str) and str(profiles).strip() else []),
    }


ALLOWED_TOOLS = load_allowed_tools()
BRAIN_ALLOWED_TOOLS = load_brain_allowed_tools()


def normalize_tool(tool: Any) -> str:
    return str(tool or "").strip().lower()


def args_to_strings(args: Iterable[Any]) -> List[str]:
    return [str(a) for a in (args or [])]


def contains_banned_patterns(args: Iterable[Any], patterns: Iterable[str] | None = None) -> Tuple[bool, str]:
    arg_strings = args_to_strings(args)
    args_joined = " ".join(arg_strings)
    for p in (patterns or BANNED_PATTERNS):
        if p in args_joined:
            return True, p
    for s in arg_strings:
        for op in ('&&', '|', ';'):
            if op in s:
                return True, op
        if '<' in s and '>' in s:
            return True, '<...>'
    return False, ""


def contains_tool_restricted_patterns(tool: Any, args: Iterable[Any]) -> Tuple[bool, str]:
    tool_norm = normalize_tool(tool)
    arg_strings = args_to_strings(args)
    restricted = {str(x).strip().lower() for x in (TOOL_ARG_BLOCKLIST.get(tool_norm) or set()) if str(x).strip()}
    for token in arg_strings:
        stripped = token.strip()
        lowered = stripped.lower()
        if lowered in restricted:
            return True, stripped
        for pattern in restricted:
            if pattern.endswith('='):
                if lowered.startswith(pattern):
                    return True, stripped
            elif lowered.startswith(pattern + '='):
                return True, stripped
        if tool_norm == 'curl' and stripped.startswith('@'):
            return True, '@payload'
    return False, ''


def parse_auth_usage(args: Iterable[Any], tool: str = '') -> Dict[str, bool]:
    arg_list = args_to_strings(args)
    joined = " ".join(arg_list)
    tool_norm = str(tool or '').strip().lower()
    uses_auth_header = "Authorization:" in joined or "Bearer " in joined
    uses_cookie = "Cookie:" in joined or "--cookie" in joined or " -c " in f" {' '.join(arg_list)} "
    basic_auth_flag_tools = {'curl'}
    uses_basic = False
    if tool_norm in basic_auth_flag_tools:
        uses_basic = "-u " in joined or "--user " in joined
    else:
        uses_basic = "--user " in joined or " --auth " in f" {' '.join(arg_list)} "
    return {
        "uses_auth_header": uses_auth_header,
        "uses_cookie": uses_cookie,
        "uses_basic": uses_basic,
        "uses_auth": uses_auth_header or uses_cookie or uses_basic,
    }


def check_credentials_policy(args: Iterable[Any], creds: Dict[str, Any], owner_approved_auth: bool, tool: str) -> Tuple[bool, str]:
    usage = parse_auth_usage(args, tool=tool)

    if usage["uses_auth_header"] and not bool(creds.get("allow_auth_header", False)):
        return False, "auth_header_not_allowed_by_campaign_policy"
    if usage["uses_cookie"] and not bool(creds.get("allow_cookie_header", False)):
        return False, "cookie_header_not_allowed_by_campaign_policy"
    if usage["uses_basic"] and not bool(creds.get("allow_basic_auth", False)):
        return False, "basic_auth_not_allowed_by_campaign_policy"

    if bool(creds.get("credentials_required", False)) and tool in {"curl", "ffuf"}:
        u = str(creds.get("bug_bounty_username") or "").strip()
        e = str(creds.get("test_account_email") or "").strip()
        if not (u and e):
            return False, "missing_required_headers_config"

    if usage["uses_auth"] and (not owner_approved_auth or not bool(creds.get("credentials_owner_approved", False))):
        return False, "credentials_require_owner_approval"

    return True, "ok"
