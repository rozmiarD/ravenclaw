from __future__ import annotations

import json
import subprocess
import uuid
from typing import Any, Dict

OPENCLAW_BIN = "/usr/local/bin/openclaw"


def run_agent(agent_id: str, message: str, timeout: int = 180) -> str:
    session_id = str(uuid.uuid4())
    cmd = [
        OPENCLAW_BIN, 'agent',
        '--agent', agent_id,
        '--session-id', session_id,
        '--message', message,
        '--json'
    ]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if p.returncode != 0:
        raise RuntimeError(f"agent {agent_id} failed: {p.stderr.strip() or p.stdout.strip()}")
    data = json.loads(p.stdout)
    payloads = data.get('result', {}).get('payloads', [])
    if not payloads:
        raise RuntimeError(f"agent {agent_id} returned no payload")
    return (payloads[0].get('text') or '').strip()


def as_json(text: str) -> Dict[str, Any]:
    if text is None:
        raise ValueError('invalid json: <none>')
    raw = str(text).strip()
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict):
            return obj
        raise ValueError('json root is not object')
    except Exception:
        pass
    dec = json.JSONDecoder()
    pos = raw.find('{')
    while pos != -1:
        try:
            obj, _end = dec.raw_decode(raw[pos:])
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass
        pos = raw.find('{', pos + 1)
    raise ValueError(f"invalid json: {raw[:400]}")


def truncate_prompt_for_budget(text: str, token_budget: int | None) -> str:
    if token_budget is None:
        return text
    tb = max(0, int(token_budget))
    char_budget = max(120, tb * 4)
    t = str(text or '')
    if len(t) <= char_budget:
        return t
    if char_budget < 240:
        return t[:char_budget]
    head = int(char_budget * 0.65)
    tail = int(char_budget * 0.30)
    return t[:head] + "\n...<truncated_for_prompt_budget>...\n" + t[-tail:]


def ask_json(agent_id: str, base_prompt: str, contract_hint: str, retries: int = 1, timeout: int = 180, prompt_token_budget: int | None = None) -> Dict[str, Any]:
    tuned_prompt = truncate_prompt_for_budget(base_prompt, prompt_token_budget)
    base = (
        f"{tuned_prompt}\n"
        "CRITICAL OUTPUT RULES:\n"
        "1) Output must be VALID JSON object only.\n"
        "2) No intro, no explanation, no markdown, no code fence.\n"
        f"3) JSON shape must match: {contract_hint}\n"
        "4) If uncertain, still return best-effort JSON in the required shape."
    )
    prompt = base
    retry_suffix = (
        "\nRETRY: Previous response was invalid. Return ONLY valid JSON, nothing else.\n"
        f"Required shape: {contract_hint}"
    )
    last_err = None
    for _ in range(retries + 1):
        raw = run_agent(agent_id, prompt, timeout=timeout)
        try:
            return as_json(raw)
        except Exception as e:
            last_err = e
            prompt = base + retry_suffix
    raise RuntimeError(f"{agent_id} JSON contract failure: {last_err}")
