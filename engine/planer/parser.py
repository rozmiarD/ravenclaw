from __future__ import annotations

import hashlib
import re
from urllib.parse import urlparse
from typing import Any, Dict, List

DOMAIN_RE = re.compile(r"(?:\*\.)?(?:[a-z0-9-]+\.)+[a-z]{2,}", re.IGNORECASE)
STRICT_DOMAIN_RE = re.compile(r"^(?:\*\.)?(?:[a-z0-9-]+\.)+[a-z]{2,}$", re.IGNORECASE)
CONCAT_TLD_RE = re.compile(r"\.(com|net|org|io|app|dev|ai)(?=[a-z])", re.IGNORECASE)
URL_RE = re.compile(r"https?://[^\s\"'<>`]+", re.IGNORECASE)


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _is_valid_domain_token(token: str) -> bool:
    t = str(token or '').strip().lower().strip("()[]<>'\"`")
    if not t:
        return False
    if CONCAT_TLD_RE.search(t):
        return False
    return bool(STRICT_DOMAIN_RE.fullmatch(t))


def _iter_valid_domain_matches(text: str):
    raw = text or ''
    for match in DOMAIN_RE.finditer(raw):
        token = str(match.group(0) or '').lower().strip().strip("()[]<>'\"`")
        start = int(match.start())
        if start > 0 and raw[start - 1] == '@':
            continue
        if _is_valid_domain_token(token):
            yield token


def extract_domains(text: str) -> List[str]:
    domains = sorted(set(_iter_valid_domain_matches(text)))
    return domains




def _normalize_scope_line(line: str) -> str:
    t = (line or "").strip()
    # Keep leading `*.` wildcard targets intact; only strip obvious bullets/numbering.
    t = re.sub(r"^[\-•\d\.)\s]+", "", t)
    return t.strip()


def extract_domains_from_scope_lines(text: str) -> List[str]:
    domains = set()
    for raw in (text or "").splitlines():
        line = _normalize_scope_line(raw)
        if not line:
            continue
        low = line.lower()
        if low.startswith("out of scope") or low.startswith("scope exclusions"):
            continue

        # Ignore long prose-like lines; keep compact asset/table-like rows.
        if len(line) > 140 or len(line.split()) > 14:
            continue

        # Extract all domain-looking tokens from compact rows.
        for token in _iter_valid_domain_matches(line):
            domains.add(token)
    return sorted(domains)


def _normalize_url_token(token: str) -> str:
    url = str(token or '').strip().strip("()[]<>'\"`").rstrip('.,;')
    if not url:
        return ''
    parsed = urlparse(url)
    host = str(parsed.hostname or '').strip().lower()
    if not host:
        return ''
    path = parsed.path or '/'
    norm = f'{parsed.scheme.lower()}://{host}{path}'
    if parsed.query:
        norm += f'?{parsed.query}'
    if parsed.fragment:
        norm += f'#{parsed.fragment}'
    return norm


def _line_looks_like_scope_asset(line: str) -> bool:
    raw = str(line or '').strip()
    if not raw:
        return False
    low = raw.lower()
    if low.endswith(':') and len(raw.split()) <= 6:
        return False
    if any(low.startswith(prefix) for prefix in ['program rules', 'rules', 'notes', 'policy', 'safe harbor', 'disclosure policy', 'response targets', 'rewards']):
        return False
    if len(raw) > 220 or len(raw.split()) > 18:
        return False
    has_url = bool(URL_RE.search(raw))
    has_domain = bool(list(_iter_valid_domain_matches(raw)))
    return has_url or has_domain


def extract_scope_assets_from_scope_lines(text: str) -> List[Dict[str, str]]:
    assets: List[Dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for raw in (text or '').splitlines():
        line = _normalize_scope_line(raw)
        if not _line_looks_like_scope_asset(line):
            continue
        urls = []
        for match in URL_RE.finditer(line):
            norm = _normalize_url_token(match.group(0))
            if norm:
                urls.append(norm)
        url_hosts = {str(urlparse(u).hostname or '').strip().lower() for u in urls}
        for url in urls:
            parsed = urlparse(url)
            host = str(parsed.hostname or '').strip().lower()
            if not host:
                continue
            item = {
                'asset_kind': 'url',
                'target': url,
                'host': host,
                'path_prefix': parsed.path or '/',
                'scope_source': 'authoritative',
                'source_line': line,
            }
            key = (item['asset_kind'], item['target'])
            if key not in seen:
                seen.add(key)
                assets.append(item)
        for token in _iter_valid_domain_matches(line):
            if token in url_hosts:
                continue
            item = {
                'asset_kind': 'domain',
                'target': token,
                'host': token,
                'path_prefix': '/',
                'scope_source': 'authoritative',
                'source_line': line,
            }
            key = (item['asset_kind'], item['target'])
            if key not in seen:
                seen.add(key)
                assets.append(item)
    return assets



def _extract_scope_regions(text: str) -> tuple[str, str]:
    t = text or ""
    low = t.lower()
    in_scope_region = t
    out_scope_region = ""

    scope_markers = ["\nin scope\n", "\nin scope:", "\nscope\n", "\nscope:", "\nassets eligible:", "\neligible targets:"]
    asset_markers = ["\nhighest impact scope", "\nlower impact scope", "\nin scope also:", "\ntier 1:", "\ntier 2:"]
    out_markers = ["\nout of scope\n", "\nout of scope:", "\nscope exclusions\n", "\nscope exclusions:", "\ncore ineligible findings\n"]

    scope_idx = -1
    for m in asset_markers:
        i = low.find(m)
        if i != -1:
            scope_idx = i if scope_idx == -1 else min(scope_idx, i)
    if scope_idx == -1:
        for m in scope_markers:
            i = low.rfind(m)
            if i != -1:
                scope_idx = max(scope_idx, i)

    out_idx = -1
    for m in out_markers:
        i = low.find(m, max(scope_idx + 1, 0)) if scope_idx != -1 else low.find(m)
        if i != -1:
            out_idx = i if out_idx == -1 else min(out_idx, i)

    out_end = len(t)
    resume_tail = ''
    if out_idx != -1:
        resume_markers = [
            "\nstarting domains",
            "\nin scope also:",
            "\nhighest impact scope",
            "\nlower impact scope",
            "\ntier 1:",
            "\ntier 2:",
            "\nassets eligible:",
            "\neligible targets:",
        ]
        resume_idx = -1
        for m in resume_markers:
            i = low.find(m, out_idx + 1)
            if i != -1:
                resume_idx = i if resume_idx == -1 else min(resume_idx, i)
        if resume_idx != -1:
            out_end = min(out_end, resume_idx)
            resume_tail = t[resume_idx:]
        stop_markers = [
            "\nstarting domains",
            "\nsafe harbor",
            "\nresponse targets",
            "\ndisclosure policy",
            "\nrewards",
        ]
        for m in stop_markers:
            i = low.find(m, out_idx + 1)
            if i != -1:
                out_end = min(out_end, i)

    if scope_idx != -1:
        start = scope_idx
        if out_idx != -1 and out_idx > start:
            in_scope_region = t[start:out_idx]
            if resume_tail:
                in_scope_region = f"{in_scope_region}\n{resume_tail}"
        else:
            in_scope_region = t[start:out_end]
    elif out_idx != -1:
        in_scope_region = t[:out_idx]
        if resume_tail:
            in_scope_region = f"{in_scope_region}\n{resume_tail}"

    if out_idx != -1:
        out_scope_region = t[out_idx:out_end]

    return in_scope_region, out_scope_region

def classify_target(domain: str) -> str:
    d = str(domain or '').lower().strip()
    base = d[2:] if d.startswith('*.') else d
    if base.startswith('api.') or '-api.' in base or '.api.' in base:
        return 'api'
    if base.startswith('id.') or '.id.' in base:
        return 'auth'
    if any(k in base for k in ['auth', 'login', 'signin', 'oauth', 'sso', 'account', 'accounts', 'secure']):
        return 'auth'
    if any(k in base for k in ['static', 'cdn', 'assets', 'asset', 'media', 'img', 'image', 'twimg']):
        return 'static'
    if any(k in base for k in ['sandbox', 'staging', 'stage', 'dev', 'test', 'qa', 'int.']):
        return 'sandbox'
    if any(k in base for k in ['webhook', 'hook', 'callback', 'partner', 'integration', 'gnip']):
        return 'integration'
    if base.startswith('support') or 'support' in base or base.startswith('status.') or base.startswith('help.'):
        return 'support'
    if any(k in base for k in ['chat', 'app', 'console', 'portal', 'money', 'billing', 'pay', 'wallet']):
        return 'web'
    if base.startswith('www.') or any(k in base for k in ['blog', 'careers', 'news', 'site', 'grok']):
        return 'web'
    # Bare apex / wildcard domains are far more likely to be primary web surfaces than opaque generic hosts.
    if base.count('.') == 1:
        return 'web'
    return 'host'



def _surface_keywords_for_domain(domain: str, *, target_type: str) -> list[str]:
    d = str(domain or '').lower().strip()
    base = d[2:] if d.startswith('*.') else d
    labels = [p for p in re.split(r'[._\-]+', base) if p]
    keywords: list[str] = []
    if d.startswith('*.'):
        keywords.append('wildcard')
    token_map = {
        'api': ['api', 'json'],
        'id': ['auth', 'identity', 'account'],
        'auth': ['auth', 'account'],
        'login': ['auth', 'session'],
        'signin': ['auth', 'session'],
        'oauth': ['auth', 'session'],
        'account': ['account', 'session'],
        'accounts': ['account', 'session'],
        'secure': ['auth'],
        'chat': ['chat', 'messaging', 'session'],
        'money': ['billing', 'wallet', 'account'],
        'billing': ['billing', 'account'],
        'wallet': ['wallet', 'account'],
        'pay': ['billing', 'payments'],
        'payments': ['billing', 'payments'],
        'admin': ['admin', 'account'],
        'console': ['admin', 'account'],
        'portal': ['portal', 'account'],
        'app': ['app', 'session'],
        'cdn': ['cdn', 'static'],
        'static': ['static'],
        'assets': ['static'],
        'asset': ['static'],
        'media': ['media', 'static'],
        'img': ['media', 'static'],
        'image': ['media', 'static'],
        'twimg': ['media', 'static'],
        'support': ['support'],
        'status': ['support'],
        'help': ['support'],
        'webhook': ['integration'],
        'callback': ['integration', 'auth'],
        'partner': ['integration'],
        'integration': ['integration'],
        'gnip': ['integration', 'api'],
        'grok': ['chat', 'ai', 'session'],
        'xai': ['ai'],
    }
    for label in labels:
        keywords.extend(token_map.get(label, []))
    if target_type == 'api':
        keywords.extend(['api', 'json'])
    elif target_type == 'auth':
        keywords.extend(['auth', 'account'])
    elif target_type == 'static':
        keywords.extend(['static'])
    elif target_type == 'integration':
        keywords.extend(['integration'])
    elif target_type == 'support':
        keywords.extend(['support'])
    elif target_type == 'web':
        keywords.extend(['web'])
    return list(dict.fromkeys(keywords))[:8]



def _target_cluster_for_domain(domain: str, *, target_type: str, surface_keywords: list[str]) -> str:
    d = str(domain or '').lower().strip()
    base = d[2:] if d.startswith('*.') else d
    surface = set(surface_keywords or [])
    if any(k in surface for k in ['billing', 'wallet', 'payments']):
        return 'money'
    if target_type == 'auth' or any(k in surface for k in ['auth', 'identity', 'account']):
        return 'identity_auth'
    if any(k in surface for k in ['chat', 'messaging', 'ai']) or 'grok' in base or base.endswith('.x.ai') or base == 'x.ai':
        return 'ai_chat'
    if any(k in surface for k in ['store', 'shop', 'cart', 'checkout', 'order']) or any(k in base for k in ['shop', 'store']):
        return 'commerce_store'
    if target_type in {'integration', 'api'} or any(k in surface for k in ['integration', 'api', 'json']):
        return 'integration_api'
    if any(k in surface for k in ['cloud', 'proxy', 'internal']) or any(k in base for k in ['cloud', 'proxy', 'safe']):
        return 'infra_edge'
    if target_type == 'static' or any(k in surface for k in ['static', 'media', 'cdn']):
        return 'static_media'
    if base == 'x.com' or base.endswith('.x.com') or base == 'twitter.com' or base.endswith('.twitter.com'):
        return 'core_social'
    if target_type == 'web' or any(k in surface for k in ['web', 'portal', 'support']):
        return 'consumer_web'
    return 'general'



def _priority_profile_for_target(*, domain: str, target_type: str, surface_keywords: list[str]) -> tuple[str, str, str]:
    d = str(domain or '').lower().strip()
    base = d[2:] if d.startswith('*.') else d
    surface = set(surface_keywords or [])
    wildcard = d.startswith('*.')
    priority_tier = 'medium'
    expected_depth = 'medium'
    surface_role = 'primary'
    if target_type == 'static' or any(k in surface for k in ['static', 'media', 'cdn']):
        return 'low', 'light', 'background'
    if target_type == 'support':
        return 'low', 'light', 'supporting'
    if wildcard:
        # Wildcards should bias toward narrowing/mapping first, not behave like fully concrete product hosts.
        if target_type in {'integration', 'api'} or any(k in surface for k in ['integration', 'api', 'auth', 'account', 'chat', 'billing', 'wallet', 'payments']):
            return 'medium', 'medium', 'supporting'
        return 'medium', 'light', 'supporting'
    if target_type in {'integration', 'api'}:
        priority_tier = 'high'
        expected_depth = 'medium'
        surface_role = 'primary'
    if any(k in surface for k in ['billing', 'wallet', 'payments']):
        priority_tier = 'high'
        expected_depth = 'deep'
        surface_role = 'primary'
    elif any(k in surface for k in ['chat', 'messaging', 'session', 'account', 'auth', 'admin', 'portal']):
        priority_tier = 'high'
        expected_depth = 'deep'
        surface_role = 'primary'
    elif base in {'x.com', 'twitter.com'}:
        priority_tier = 'high'
        expected_depth = 'medium'
        surface_role = 'primary'
    return priority_tier, expected_depth, surface_role



def _limit_seed_families_for_profile(*, domain: str, target_cluster: str, priority_tier: str, expected_depth: str, surface_role: str, fams: list[str]) -> list[str]:
    order = {
        'authz': 100,
        'auth_flow': 98,
        'workflow': 95,
        'logic': 94,
        'state_transition': 93,
        'client_input': 88,
        'input_tamper': 87,
        'redirect_trust': 84,
        'content_discovery': 60,
        'historical_url_mining': 56,
        'recon': 50,
        'tls_assessment': 40,
        'subdomain_expansion': 42,
    }
    cluster_boosts = {
        'money': {'authz': 12, 'auth_flow': 10, 'logic': 11, 'workflow': 10, 'state_transition': 9},
        'ai_chat': {'auth_flow': 16, 'workflow': 13, 'state_transition': 13, 'client_input': 10},
        'integration_api': {'authz': 16, 'auth_flow': 12, 'input_tamper': 12, 'content_discovery': 1},
        'core_social': {'auth_flow': 14, 'client_input': 12, 'redirect_trust': 4, 'content_discovery': 1},
        'static_media': {'content_discovery': 6, 'historical_url_mining': 5, 'tls_assessment': 20, 'recon': 4},
    }
    primary_filters = {
        'money': {'authz', 'auth_flow', 'logic', 'workflow', 'state_transition'},
        'ai_chat': {'auth_flow', 'workflow', 'state_transition', 'client_input', 'content_discovery'},
        'integration_api': {'authz', 'auth_flow', 'input_tamper', 'content_discovery'},
        'core_social': {'auth_flow', 'client_input', 'redirect_trust', 'content_discovery'},
    }
    scored: dict[str, int] = {}
    wildcard = str(domain or '').startswith('*.')
    for idx, fam in enumerate(fams or []):
        f = str(fam or '').strip().lower()
        if not f:
            continue
        score = order.get(f, 30) - min(idx, 8)
        score += cluster_boosts.get(target_cluster, {}).get(f, 0)
        if surface_role != 'primary' and f in {'workflow', 'logic', 'state_transition', 'redirect_trust', 'input_tamper'}:
            score -= 30
        if surface_role == 'background' and f not in {'historical_url_mining', 'content_discovery', 'recon', 'tls_assessment'}:
            score -= 100
        if priority_tier == 'high' and expected_depth == 'deep' and f in {'recon', 'historical_url_mining', 'content_discovery', 'tls_assessment'}:
            score -= 22
        if target_cluster == 'integration_api' and f in {'recon', 'historical_url_mining', 'tls_assessment'}:
            score -= 50
        if target_cluster == 'integration_api' and f == 'content_discovery' and surface_role == 'primary' and not wildcard:
            score -= 15
        if target_cluster == 'core_social' and not wildcard and f in {'historical_url_mining', 'recon', 'tls_assessment'}:
            score -= 40
        if target_cluster == 'core_social' and not wildcard and f == 'content_discovery':
            score -= 18
        if target_cluster == 'ai_chat' and not wildcard and f in {'content_discovery', 'historical_url_mining', 'recon', 'tls_assessment'}:
            score -= 40
        if target_cluster in {'money', 'ai_chat', 'integration_api'} and f == 'redirect_trust':
            score -= 120
        scored[f] = max(scored.get(f, -999), score)
    if surface_role == 'background':
        cap = 3
    elif surface_role == 'supporting':
        cap = 3
    elif priority_tier == 'high' and expected_depth == 'deep':
        cap = 5
    else:
        cap = 4
    if target_cluster == 'integration_api':
        cap = min(cap, 3)
    if target_cluster == 'core_social' and not wildcard and surface_role == 'primary':
        cap = min(cap, 3)
    if target_cluster == 'ai_chat' and not wildcard and surface_role == 'primary':
        cap = min(cap, 5)
    if target_cluster in {'core_social', 'ai_chat'} and surface_role == 'supporting':
        cap = min(cap, 3)
    ordered = [fam for fam, _ in sorted(scored.items(), key=lambda item: (-item[1], item[0]))]
    if surface_role == 'primary' and not wildcard and target_cluster in primary_filters:
        allow = primary_filters[target_cluster]
        ordered = [fam for fam in ordered if fam in allow] + [fam for fam in ordered if fam not in allow]
    if wildcard:
        ordered = [fam for fam in ordered if fam != 'tls_assessment'] + (['tls_assessment'] if 'tls_assessment' in ordered and surface_role == 'background' else [])
    return ordered[:cap]



def _seed_vectors_and_families(*, domain: str, target_type: str, allow_keywords: list[str], credentials_required: bool) -> tuple[list[str], list[str]]:
    surface_keywords = _surface_keywords_for_domain(domain, target_type=target_type)
    allow = {str(x or '').strip().lower() for x in (allow_keywords or []) if str(x or '').strip()}
    candidate_vectors: list[str] = []
    fams: list[str] = []

    def add_family(*items: str) -> None:
        for item in items:
            if item and item not in fams:
                fams.append(item)

    def add_vector(*items: str) -> None:
        for item in items:
            if item and item not in candidate_vectors:
                candidate_vectors.append(item)

    # High-value authenticated/boundary surfaces first.
    if target_type in {'api', 'auth', 'integration'} or any(k in surface_keywords for k in ['account', 'auth', 'admin', 'portal']):
        add_family('auth_flow', 'authz')
        add_vector('authz', 'auth_flow')
    if any(k in surface_keywords for k in ['billing', 'wallet', 'payments', 'money']):
        add_family('logic', 'workflow', 'state_transition', 'authz', 'auth_flow')
        add_vector('workflow', 'logic', 'authz')
    if any(k in surface_keywords for k in ['chat', 'messaging', 'session']):
        add_family('auth_flow', 'workflow', 'state_transition')
        add_vector('auth_flow', 'workflow', 'session_state')
    if target_type in {'web', 'auth'} and 'xss' in allow:
        add_family('client_input')
        add_vector('xss-safe-probes')
    if (
        'open redirect' in allow
        and target_type in {'web', 'auth'}
        and not str(domain or '').startswith('*.')
        and not any(k in surface_keywords for k in ['billing', 'wallet', 'payments', 'chat', 'messaging', 'integration', 'api', 'static', 'media'])
    ):
        add_family('redirect_trust')
        add_vector('redirect_trust')
    if 'ssrf' in allow and (target_type in {'api', 'integration'} or 'integration' in surface_keywords):
        add_family('input_tamper')
        add_vector('ssrf')
    if 'csrf' in allow and (credentials_required or target_type in {'web', 'auth', 'api'} or any(k in surface_keywords for k in ['session', 'account', 'auth', 'billing', 'wallet'])):
        add_family('auth_flow')
        add_vector('csrf')
    if 'idor' in allow and (credentials_required or target_type in {'web', 'api', 'integration', 'auth'} or any(k in surface_keywords for k in ['account', 'billing', 'wallet', 'admin'])):
        add_family('authz')
        add_vector('idor')

    # Broader low-risk surface work stays, but later unless nothing richer exists.
    if target_type in {'web', 'static', 'support'}:
        add_family('historical_url_mining', 'content_discovery')
        add_vector('historical_url_mining', 'content_discovery')
    if target_type == 'sandbox':
        add_family('subdomain_expansion', 'content_discovery')
        add_vector('subdomain_expansion', 'content_discovery')
    if target_type in {'api', 'integration'}:
        add_family('content_discovery')
        add_vector('content_discovery')

    add_family('recon', 'tls_assessment')
    add_vector('recon')
    return candidate_vectors[:8], fams


def _uplift_target_type_from_scope_assets(domain: str, target_type: str, authoritative_assets: list[dict[str, Any]]) -> str:
    dtype = str(target_type or 'host').strip().lower() or 'host'
    if dtype != 'host':
        return dtype
    host = str(domain or '').strip().lower()
    if not host:
        return dtype
    host_assets = [
        a for a in (authoritative_assets or [])
        if isinstance(a, dict)
        and str(a.get('host') or '').strip().lower() == host
        and str(a.get('asset_kind') or 'domain').strip().lower() == 'url'
    ]
    if not host_assets:
        return dtype
    lexical: set[str] = set(host.replace('-', '.').split('.'))
    for asset in host_assets:
        path = str(asset.get('path_prefix') or '/').strip().lower()
        lexical.update(part for part in path.replace('-', '/').replace('_', '/').split('/') if part)
    if any(k in lexical for k in {'api', 'json', 'callback', 'partner', 'integration'}):
        return 'integration'
    if any(k in lexical for k in {'auth', 'login', 'signin', 'account', 'id', 'oauth', 'sso', 'session'}):
        return 'auth'
    return 'web'


def _extract_program_label(text: str) -> str:
    for line in (text or "").splitlines():
        s = line.strip()
        if not s:
            continue
        s = re.sub(r"^[#\-\*\d\.)\s]+", "", s)
        s = re.sub(r"[^A-Za-z0-9\s_-]", "", s).strip()
        if len(s) >= 4:
            return s[:48]
    return "Campaign"


def parse_program_text(raw_text: str, operator_flags: Dict[str, Any] | None = None) -> Dict[str, Any]:
    text = raw_text or ""
    lowered = text.lower()
    flags = operator_flags or {}
    in_scope_region, out_scope_region = _extract_scope_regions(text)
    authoritative_assets = extract_scope_assets_from_scope_lines(in_scope_region)
    if not authoritative_assets:
        authoritative_assets = extract_scope_assets_from_scope_lines(text)
    out_scope_assets = extract_scope_assets_from_scope_lines(out_scope_region)
    out_domains = {str(item.get('host') or '').strip().lower() for item in out_scope_assets if str(item.get('host') or '').strip()}
    out_exact_targets = {str(item.get('target') or '').strip().lower() for item in out_scope_assets if str(item.get('asset_kind') or '') == 'url' and str(item.get('target') or '').strip()}
    authoritative_assets = [
        item for item in authoritative_assets
        if str(item.get('host') or '').strip().lower() not in out_domains
        and not (
            str(item.get('asset_kind') or '') == 'url'
            and str(item.get('target') or '').strip().lower() in out_exact_targets
        )
    ]
    domains = sorted({str(item.get('host') or '').strip().lower() for item in authoritative_assets if str(item.get('host') or '').strip()})

    disallow = [
        p for p in ["dos", "brute force", "social engineering", "phishing", "real user data"]
        if p in lowered
    ]
    allow = [
        p for p in ["xss", "idor", "csrf", "ssrf", "open redirect", "recon", "fuzz"]
        if p in lowered
    ]

    cred_markers = [
        p for p in ["auth required", "authorized testing", "use credentials", "authenticated", "login required", "session cookie", "bearer", "authorization"]
        if p in lowered
    ]
    credentials_required = any(k in lowered for k in ["auth required", "authenticated", "login required", "use credentials"])
    allow_auth_header = any(k in lowered for k in ["authorization", "bearer", "auth header"])
    allow_cookie_header = any(k in lowered for k in ["cookie", "session cookie"])
    allow_basic_auth = any(k in lowered for k in ["basic auth", "-u user:pass", "username password"])

    targets = [
        {
            'host': str(item.get('host') or '').strip().lower(),
            'target': str(item.get('target') or '').strip(),
            'asset_kind': str(item.get('asset_kind') or 'domain'),
            'path_prefix': str(item.get('path_prefix') or '/'),
            'scope_source': str(item.get('scope_source') or 'authoritative'),
            'source_line': str(item.get('source_line') or ''),
            'type': classify_target(str(item.get('host') or '')),
            'target_type': classify_target(str(item.get('host') or '')),
            'in_scope': True,
        }
        for item in authoritative_assets
        if str(item.get('host') or '').strip()
    ]
    for target in targets:
        uplifted = _uplift_target_type_from_scope_assets(
            str(target.get('host') or ''),
            str(target.get('target_type') or target.get('type') or 'host'),
            authoritative_assets,
        )
        target['type'] = uplifted
        target['target_type'] = uplifted

    invalid_domain_candidates = sorted({d.lower() for d in DOMAIN_RE.findall(text) if not _is_valid_domain_token(d)})
    target_profiles = {
        d: {
            'type': classify_target(d),
            'target_type': classify_target(d),
            'task_family_seeds': [],
            'surface_keywords': [],
            'candidate_vectors': [],
            'notes': [],
            'priority_tier': 'medium',
            'expected_depth': 'medium',
            'surface_role': 'primary',
            'target_cluster': 'general',
        }
        for d in domains
    }
    for d, profile in target_profiles.items():
        dtype = _uplift_target_type_from_scope_assets(
            d,
            str(profile.get('target_type') or profile.get('type') or 'host'),
            authoritative_assets,
        )
        profile['type'] = dtype
        profile['target_type'] = dtype
        surface_keywords = _surface_keywords_for_domain(d, target_type=dtype)
        candidate_vectors, fams = _seed_vectors_and_families(
            domain=d,
            target_type=dtype,
            allow_keywords=allow,
            credentials_required=credentials_required,
        )
        priority_tier, expected_depth, surface_role = _priority_profile_for_target(
            domain=d,
            target_type=dtype,
            surface_keywords=surface_keywords,
        )
        target_cluster = _target_cluster_for_domain(d, target_type=dtype, surface_keywords=surface_keywords)
        fams = _limit_seed_families_for_profile(
            domain=d,
            target_cluster=target_cluster,
            priority_tier=priority_tier,
            expected_depth=expected_depth,
            surface_role=surface_role,
            fams=list(dict.fromkeys(fams)),
        )
        profile['surface_keywords'] = surface_keywords
        profile['candidate_vectors'] = candidate_vectors
        profile['task_family_seeds'] = fams
        profile['priority_tier'] = priority_tier
        profile['expected_depth'] = expected_depth
        profile['surface_role'] = surface_role
        profile['target_cluster'] = target_cluster
        notes: list[str] = []
        if d.startswith('*.'):
            notes.append('wildcard_scope')
        if any(k in surface_keywords for k in ['billing', 'wallet', 'payments']):
            notes.append('high_value_stateful_surface')
        if any(k in surface_keywords for k in ['chat', 'messaging', 'session']):
            notes.append('session_or_conversation_surface')
        if dtype in {'api', 'auth', 'integration'}:
            notes.append('boundary_candidate_surface')
        if surface_role != 'primary':
            notes.append(f'{surface_role}_surface')
        profile['notes'] = notes[:4]

    return {
        "source_hash": hash_text(text),
        "program_label": _extract_program_label(text),
        "source_length": len(text),
        "authoritative_assets": authoritative_assets,
        "domains": domains,
        "out_of_scope_targets": sorted(out_domains),
        "targets": targets,
        "target_profiles": target_profiles,
        "invalid_domain_candidates": invalid_domain_candidates,
        "allow_keywords": sorted(set(allow)),
        "deny_keywords": sorted(set(disallow)),
        "credentials_policy": {
            "credentials_required": credentials_required,
            "allow_auth_header": allow_auth_header,
            "allow_cookie_header": allow_cookie_header,
            "allow_basic_auth": allow_basic_auth,
            "owner_approval_required": True,
            "signals": sorted(set(cred_markers)),
        },
        "operator_flags": flags,
    }
