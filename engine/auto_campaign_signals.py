from __future__ import annotations

import re
from pathlib import Path

SIGNAL_REGEX = {
    "jwt": re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    "akia": re.compile(r"AKIA[0-9A-Z]{16}"),
    "metrics": re.compile(r"__RC_METRICS__\s+([^\n]+)"),
}


def parse_rc_metrics(text: str) -> dict:
    out = {}
    if not text:
        return out
    m = SIGNAL_REGEX["metrics"].findall(text)
    if not m:
        return out
    seg = m[-1]
    for tok in seg.split():
        if '=' not in tok:
            continue
        k, v = tok.split('=', 1)
        out[k.strip()] = v.strip()
    return out


def inspect_json_signal_from_command(planned_cmd: object) -> dict:
    out = {'signal': False, 'severity': 'low', 'note': '', 'keys': [], 'info': [], 'findings': []}
    try:
        cmd = ' '.join(str(x) for x in planned_cmd) if isinstance(planned_cmd, list) else str(planned_cmd or '')
        m = re.search(r"(?:^|\s)-o\s+([^\s]+)", cmd)
        if not m:
            return out
        raw = m.group(1).strip().strip("'\"")
        pth = Path(raw)
        if not pth.exists() or pth.stat().st_size <= 0 or pth.stat().st_size > 300000:
            return out
        sample = pth.read_text(encoding='utf-8', errors='ignore')[:12000]
        low = sample.lower()
        stripped = sample.strip()
        if len(stripped) <= 8 and stripped in {'', '{}', '[]', 'null', 'ok'}:
            return out

        if any(k in low for k in ['traceback', 'exception', 'stack trace', 'sql syntax', 'whitelabel error', 'nullreference']):
            out['findings'].append({'code':'error_trace_signal','severity':'mid','message':'Error/stack fingerprint exposed in response body'})
        if SIGNAL_REGEX["jwt"].search(sample) or SIGNAL_REGEX["akia"].search(sample) or 'begin private key' in low:
            out['findings'].append({'code':'secret_leak_signal','severity':'high','message':'Potential credential/token material observed in response body'})
        if any(k in low for k in ['owner_id','account_id','user_id','tenant_id','permissions','role']):
            out['findings'].append({'code':'authz_boundary_signal','severity':'mid','message':'Object/ownership fields suggest possible authz boundary weakness'})
        if any(k in low for k in ['idempotency', 'duplicate', 'replay', 'state transition', 'settlement', 'insufficient funds']):
            out['findings'].append({'code':'business_logic_signal','severity':'mid','message':'Business-logic/idempotency/state anomaly indicators present'})

        if out['findings']:
            out['signal'] = True
            out['severity'] = out['findings'][0].get('severity', out['severity'])
            out['note'] = out['findings'][0].get('message', out['note'])

        out['findings'] = out['findings'][:8]
    except Exception:
        return out
    return out
