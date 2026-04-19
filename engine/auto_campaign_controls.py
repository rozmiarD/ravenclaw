from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


def derive_control_target(target: str) -> str:
    """Create a conservative control URL from a probe target.

    Rules:
    - keep same scheme/host/path
    - deduplicate repeated query keys (keep first)
    - neutralize obviously high-risk values (admin/root/true/1 -> user/false/0)
    - if URL has no transformable query, append a benign control marker to enable delta checks
    """
    try:
        raw = str(target or "")
        p = urlparse(raw)
        if not p.scheme or not p.netloc:
            return raw
        seen = set()
        q_out = []
        for k, v in parse_qsl(p.query, keep_blank_values=True):
            lk = (k or "").lower()
            if lk in seen:
                continue
            seen.add(lk)
            lv = (v or "").lower()
            if lv in {"admin", "root", "superuser"}:
                v = "user"
            elif lv in {"true", "yes"}:
                v = "false"
            elif lv == "1":
                v = "0"
            q_out.append((k, v))

        if not q_out:
            q_out = [("rc_control", "1")]
        else:
            # ensure control marker exists for deterministic comparison
            if not any((k or "").lower() == "rc_control" for k, _ in q_out):
                q_out.append(("rc_control", "1"))

        new_q = urlencode(q_out, doseq=True)
        candidate = urlunparse((p.scheme, p.netloc, p.path, p.params, new_q, p.fragment))
        if candidate == raw:
            # final fallback, minimal path-safe perturbation
            new_q = (new_q + "&rc_cmp=1") if new_q else "rc_cmp=1"
            candidate = urlunparse((p.scheme, p.netloc, p.path, p.params, new_q, p.fragment))
        return candidate
    except Exception:
        return str(target or "")


def _extract_output_path(cmd: list[str]) -> str:
    for i, tok in enumerate(cmd):
        if tok in {"-o", "--output"} and i + 1 < len(cmd):
            return str(cmd[i + 1])
    return ""


def _extract_url(cmd: list[str]) -> str:
    for tok in reversed(cmd):
        t = str(tok).strip().strip('"').strip("'")
        if t.startswith("http://") or t.startswith("https://"):
            return t
    return ""


def _sha256(path: str) -> str:
    p = Path(path)
    if not p.exists() or p.stat().st_size <= 0:
        return ""
    h = hashlib.sha256()
    with p.open("rb") as f:
        while True:
            b = f.read(8192)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def run_control_comparison(planned_cmd: object, timeout_sec: int = 20) -> dict:
    """Run a paired control request for curl probes (safe subset).

    Returns dict with:
      performed, control_target, control_delta_observed, control_http_code,
      probe_hash, control_hash, reason
    """
    out = {
        "performed": False,
        "control_target": "",
        "control_delta_observed": False,
        "control_http_code": "",
        "probe_hash": "",
        "control_hash": "",
        "reason": "not_applicable",
    }
    if not isinstance(planned_cmd, list) or not planned_cmd:
        return out
    if str(planned_cmd[0]).lower() != "curl":
        out["reason"] = "non_curl"
        return out

    # only run control for GET-like probes to avoid side effects
    toks = [str(x) for x in planned_cmd]
    low_toks = [t.lower() for t in toks]
    if "-x" in toks or "--proxy" in low_toks:
        out["reason"] = "skip_proxy_cmd"
        return out

    method = "GET"
    for i, t in enumerate(toks):
        tl = t.lower()
        if tl in {"-x", "--request"} and i + 1 < len(toks):
            method = str(toks[i + 1]).upper()
            break

    control_method = "GET"
    if method in {"PUT", "PATCH", "DELETE"}:
        out["reason"] = "skip_non_safe_method"
        return out
    if method == "HEAD":
        control_method = "HEAD"
    elif method in {"POST", "OPTIONS"}:
        # Safe control fallback: downgrade control to GET to avoid side effects while still checking response-path delta.
        control_method = "GET"

    probe_url = _extract_url(planned_cmd)
    if not probe_url:
        out["reason"] = "missing_probe_url"
        return out

    control_target = derive_control_target(probe_url)
    out["control_target"] = control_target
    if control_target == probe_url:
        out["reason"] = "no_control_transform"
        return out

    probe_out = _extract_output_path(planned_cmd)
    out["probe_hash"] = _sha256(probe_out) if probe_out else ""

    control_out = str(Path("/tmp") / "ravenclaw_control_probe.txt")
    control_cmd = [
        "curl", "-sS", "--connect-timeout", "10", "--max-time", str(max(10, timeout_sec)),
        "-X", control_method,
        "-o", control_out,
        "-w", "__RC_CTRL__ code=%{http_code}",
        control_target,
    ]
    try:
        res = subprocess.run(control_cmd, capture_output=True, text=True, timeout=max(10, timeout_sec))
        std = (res.stdout or "") + " " + (res.stderr or "")
        marker = "__RC_CTRL__ code="
        if marker in std:
            out["control_http_code"] = std.split(marker, 1)[1].strip().split()[0]
        out["control_hash"] = _sha256(control_out)
        out["performed"] = True
        out["reason"] = "ok" if control_method == method else f"ok_method_downgraded:{method}->{control_method}"
        out["control_delta_observed"] = bool(out["probe_hash"] and out["control_hash"] and out["probe_hash"] != out["control_hash"])
        return out
    except Exception as exc:
        out["reason"] = f"control_exec_error:{str(exc)[:80]}"
        return out
