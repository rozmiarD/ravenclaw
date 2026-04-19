from __future__ import annotations

import hashlib
import socket
from urllib.parse import parse_qsl, urlparse


def host_from_target(target: str) -> str:
    try:
        host = urlparse(target).netloc
    except Exception:
        host = ""
    return host or target


def is_resolvable_host(host: str) -> bool:
    h = str(host or '').strip().lower()
    if not h:
        return False
    try:
        socket.getaddrinfo(h, None)
        return True
    except Exception:
        return False


def attack_family(objective: str, target: str) -> str:
    text = f"{objective} {target}".lower()
    families = [
        ('xss', ['xss', 'script', 'onerror', 'onload']),
        ('idor', ['idor', 'authorization', 'object id', 'insecure direct object']),
        ('sqli', ['sqli', 'sql injection', 'sqlmap']),
        ('csrf', ['csrf']),
        ('ssrf', ['ssrf']),
        ('recon', ['recon', 'robots', 'sitemap', 'fingerprint']),
    ]
    for fam, keys in families:
        if any(k in text for k in keys):
            return fam
    return 'generic'


def payload_signature(target: str) -> str:
    try:
        parsed = urlparse(target)
        q = parse_qsl(parsed.query, keep_blank_values=True)
        if not q:
            return 'nopayload'
        q_sorted = '&'.join(f"{k}={v}" for k, v in sorted(q))
        return hashlib.sha1(q_sorted.encode('utf-8')).hexdigest()[:12]
    except Exception:
        return 'nopayload'


def dedup_key(objective: str, target: str) -> tuple[str, str, str]:
    host = host_from_target(target).strip().lower()
    family = attack_family(objective, target)
    sig = payload_signature(target)
    return (host, family, sig)
