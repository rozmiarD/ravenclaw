from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from campaign_utils import extract_host_from_url  # type: ignore
from govengine.contracts.execution import apply_request_decoration_to_args
from govengine_security_helpers import compile_action_spec  # type: ignore
from paths import wp  # type: ignore


def _apply_required_headers_to_args(tool: str, args: List[Any], creds: Dict[str, Any]) -> List[str]:
    return apply_request_decoration_to_args(str(tool or ''), list(args or []), creds)



def apply_required_headers(brain: Dict[str, Any], creds: Dict[str, Any]) -> Dict[str, Any]:
    tool = str(brain.get('tool') or '').lower().strip()
    args = brain.get('args', [])
    if not isinstance(args, list):
        return brain
    brain['args'] = _apply_required_headers_to_args(tool, args, creds)
    return brain



def _sanitize_action_args(args: List[Any]) -> List[str]:
    out: List[str] = []
    for a in (args or []):
        s = str(a).strip()
        if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
            if len(s) >= 2:
                s = s[1:-1]
        if s in {'<output_file>', '<metrics_format>'}:
            continue
        out.append(s)

    neutral_ua = 'User-Agent: Mozilla/5.0 (compatible; Security-Research/1.0)'
    for i, token in enumerate(out):
        if token in {'-H', '--header'} and i + 1 < len(out):
            hv = str(out[i + 1])
            low = hv.lower()
            if low.startswith('user-agent:') and 'raven-claw' in low:
                out[i + 1] = neutral_ua
    return out



def _append_target_if_missing(args: List[str], target: str) -> List[str]:
    out = [str(a) for a in (args or [])]
    if not target:
        return out
    has_url = any((isinstance(a, str) and str(a).strip().strip("'").strip('"').startswith(('http://', 'https://'))) for a in out)
    if not has_url:
        out.append(target)
    return out


def _sanitize_stdin_text(value: Any) -> str:
    text = str(value or '')
    return text if text.endswith('\n') or not text else (text + '\n')



def _normalize_curl_execution_args(args: List[str], *, target: str, output_stub: str, execution_mode: str) -> List[str]:
    spec_args = list(args or [])
    if execution_mode == 'faithful':
        return _append_target_if_missing(spec_args, target)
    cleaned: List[str] = []
    i = 0
    while i < len(spec_args):
        tok = str(spec_args[i])
        if tok in {'-o', '--output', '-w', '--write-out'}:
            nxt = spec_args[i + 1] if i + 1 < len(spec_args) else None
            if nxt is not None and not str(nxt).startswith('-'):
                i += 2
            else:
                i += 1
            continue
        cleaned.append(tok)
        i += 1
    spec_args = cleaned
    if '-s' in spec_args and '-S' not in spec_args and '--show-error' not in spec_args:
        spec_args = ['-S', *spec_args]
    outputs_dir = Path(wp('.')) / 'workspace-brain' / 'outputs'
    outputs_dir.mkdir(parents=True, exist_ok=True)
    out_path = str(outputs_dir / f"{output_stub}.txt")
    spec_args = [*spec_args, '-o', out_path]
    spec_args = [
        *spec_args,
        '-w',
        "\n__RC_METRICS__ code=%{http_code} ip=%{remote_ip} dns=%{time_namelookup} connect=%{time_connect} tls=%{time_appconnect} ttfb=%{time_starttransfer} total=%{time_total} size=%{size_download} redirects=%{num_redirects}",
    ]
    if '--connect-timeout' not in spec_args:
        spec_args = ['--connect-timeout', '10', '--max-time', '25', *spec_args]
    elif '--max-time' not in spec_args:
        spec_args = ['--max-time', '25', *spec_args]
    return _append_target_if_missing(spec_args, target)



def prepare_action_spec_for_execution(raw_action_spec: Dict[str, Any], *, target: str, creds: Dict[str, Any], execution_mode: str) -> tuple[Dict[str, Any], Dict[str, Any]]:
    compiled = compile_action_spec(raw_action_spec)
    raw_plan = compiled.get('execution_plan') if isinstance(compiled.get('execution_plan'), list) else []
    normalized_chain: List[Dict[str, Any]] = []
    safe_host = (extract_host_from_url(target) or 'target').replace('.', '_')
    for idx, step in enumerate(raw_plan, 1):
        if not isinstance(step, dict):
            continue
        step_tool = str(step.get('tool') or '').strip().lower()
        step_args = _sanitize_action_args(list(step.get('args') or []))
        step_stdin = _sanitize_stdin_text(step.get('stdin'))
        step_args = _apply_required_headers_to_args(step_tool, step_args, creds)
        if step_tool == 'curl':
            step_args = _normalize_curl_execution_args(step_args, target=target if idx == 1 else '', output_stub=f"{safe_host}_probe_{idx}", execution_mode=execution_mode)
        elif idx == 1 and not step_stdin:
            step_args = _append_target_if_missing(step_args, target)
        normalized_step = {
            'tool': step_tool,
            'role': str(step.get('role') or 'probe'),
            'args': step_args,
        }
        if step_stdin:
            normalized_step['stdin'] = step_stdin
        normalized_chain.append(normalized_step)
    final_spec = dict(raw_action_spec)
    final_spec['execution_mode'] = execution_mode
    final_spec['resolved_planner_profiles'] = list(compiled.get('resolved_planner_profiles') or raw_action_spec.get('resolved_planner_profiles') or [])
    final_spec['tool'] = str(compiled.get('tool') or raw_action_spec.get('tool') or '')
    final_spec['tool_candidates'] = list(compiled.get('tool_candidates') or raw_action_spec.get('tool_candidates') or [])
    final_spec['recipe_name'] = str(compiled.get('recipe_name') or raw_action_spec.get('recipe_name') or '')
    final_spec['target'] = str(target or raw_action_spec.get('target') or '')
    if normalized_chain:
        final_spec['tool_chain'] = normalized_chain
        final_spec['args'] = list(normalized_chain[0].get('args') or [])
        if normalized_chain[0].get('stdin'):
            final_spec['stdin'] = str(normalized_chain[0].get('stdin') or '')
    return final_spec, compiled
