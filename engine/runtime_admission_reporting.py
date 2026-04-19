from __future__ import annotations

from collections import Counter
from typing import Any


ADMISSION_SKIP_EXCLUDED_REASONS = {'unresolved_host', 'dns_unresolved', 'host_cooldown', 'allowed'}


def admission_skip_bucket(reason_code: str | None) -> str:
    reason = str(reason_code or '').strip().lower()
    if reason in {'unresolved_host', 'dns_unresolved'}:
        return 'dns'
    if reason == 'host_cooldown':
        return 'cooldown'
    if reason == 'allowed':
        return 'allowed'
    return 'execution_gate'


def track_execution_gate_skip(reason_code: str | None) -> bool:
    return admission_skip_bucket(reason_code) == 'execution_gate' and str(reason_code or '').strip().lower() not in ADMISSION_SKIP_EXCLUDED_REASONS


def execution_gate_skip_example(target: str, gate_payload: dict[str, Any] | None) -> str:
    payload = gate_payload if isinstance(gate_payload, dict) else {}
    sample_bits = [str(target or '-').strip() or '-']
    family = str(payload.get('family') or '').strip()
    state_band = str(payload.get('state_band') or '').strip()
    synthesis_action = str(payload.get('synthesis_recommended_action') or '').strip()
    synthesis_reason = str(payload.get('synthesis_reason') or '').strip()
    synthesis_stage = str(payload.get('synthesis_next_stage') or '').strip()
    synthesis_family = str(payload.get('synthesis_gate_family') or '').strip()
    if family:
        sample_bits.append(f'family={family}')
    if state_band:
        sample_bits.append(f'state={state_band}')
    if synthesis_action:
        sample_bits.append(f'synthesis_action={synthesis_action}')
    if synthesis_reason:
        sample_bits.append(f'synthesis_reason={synthesis_reason}')
    if synthesis_stage:
        sample_bits.append(f'synthesis_stage={synthesis_stage}')
    if synthesis_family:
        sample_bits.append(f'synthesis_family={synthesis_family}')
    return ';'.join(sample_bits)


def record_execution_gate_skip(reason_code: str | None, target: str, gate_payload: dict[str, Any] | None, gate_skip_count: dict[str, int], gate_skip_examples: dict[str, list[str]]) -> None:
    reason = str(reason_code or '').strip() or 'gate_blocked'
    if not track_execution_gate_skip(reason):
        return
    gate_skip_count[reason] = int(gate_skip_count.get(reason, 0)) + 1
    sample = execution_gate_skip_example(target, gate_payload)
    ref = gate_skip_examples.setdefault(reason, [])
    if sample not in ref and len(ref) < 3:
        ref.append(sample)


def execution_gate_log_parts(gate_payload: dict[str, Any] | None, mode: str) -> tuple[str, str, str]:
    payload = gate_payload if isinstance(gate_payload, dict) else {}
    parts = [
        f"host={payload.get('host') or '-'}",
        f"family={payload.get('family') or '-'}",
        f'mode={mode}',
        f"state_band={payload.get('state_band') or '-'}",
    ]
    blockers = [str(x) for x in (payload.get('blockers') or []) if str(x).strip()]
    if blockers:
        parts.append(f"blockers={','.join(blockers)}")
    synthesis_action = str(payload.get('synthesis_recommended_action') or '').strip()
    synthesis_reason = str(payload.get('synthesis_reason') or '').strip()
    synthesis_stage = str(payload.get('synthesis_next_stage') or '').strip()
    synthesis_family = str(payload.get('synthesis_gate_family') or '').strip()
    if synthesis_action:
        parts.append(f'synthesis_action={synthesis_action}')
    if synthesis_reason:
        parts.append(f'synthesis_reason={synthesis_reason}')
    if synthesis_stage:
        parts.append(f'synthesis_stage={synthesis_stage}')
    if synthesis_family:
        parts.append(f'synthesis_family={synthesis_family}')
    if payload.get('cooldown_until') is not None:
        parts.append(f"cooldown_until={payload.get('cooldown_until')}")
    detail = str(payload.get('detail') or '').strip()
    if detail:
        parts.append(detail)
    return (
        str(payload.get('reason_code') or 'gate_blocked'),
        str(payload.get('host') or ''),
        ';'.join(parts),
    )


def _parse_skip_example_fields(sample: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for bit in [str(x).strip() for x in str(sample or '').split(';') if str(x).strip()]:
        if '=' not in bit:
            if 'target' not in fields:
                fields['target'] = bit
            continue
        key, value = bit.split('=', 1)
        fields[str(key or '').strip()] = str(value or '').strip()
    return fields


def synthesis_skip_summary(gate_counts: dict[str, int] | None, gate_examples: dict[str, list[str]] | None) -> dict[str, Any]:
    counts = gate_counts if isinstance(gate_counts, dict) else {}
    examples = gate_examples if isinstance(gate_examples, dict) else {}
    total = int(counts.get('planner_synthesis_skip', 0) or 0)
    samples = [str(x) for x in (examples.get('planner_synthesis_skip') or []) if str(x).strip()]
    action_counts: Counter[str] = Counter()
    stage_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()
    for sample in samples:
        fields = _parse_skip_example_fields(sample)
        action = str(fields.get('synthesis_action') or '').strip()
        stage = str(fields.get('synthesis_stage') or '').strip()
        reason = str(fields.get('synthesis_reason') or '').strip()
        family = str(fields.get('synthesis_family') or '').strip()
        if action:
            action_counts[action] += 1
        if stage:
            stage_counts[stage] += 1
        if reason:
            reason_counts[reason] += 1
        if family:
            family_counts[family] += 1
    action_text = '; '.join(f'{k}:{v}' for k, v in action_counts.most_common()) if action_counts else '-'
    stage_text = '; '.join(f'{k}:{v}' for k, v in stage_counts.most_common()) if stage_counts else '-'
    reason_text = '; '.join(f'{k}:{v}' for k, v in reason_counts.most_common()) if reason_counts else '-'
    family_text = '; '.join(f'{k}:{v}' for k, v in family_counts.most_common()) if family_counts else '-'
    return {
        'total': total,
        'actions': action_counts.most_common(),
        'stages': stage_counts.most_common(),
        'reasons': reason_counts.most_common(),
        'families': family_counts.most_common(),
        'action_text': action_text,
        'stage_text': stage_text,
        'reason_text': reason_text,
        'family_text': family_text,
        'example': samples[0] if samples else '-',
    }


def execution_gate_summary_payload(gate_counts: dict[str, int] | None, gate_examples: dict[str, list[str]] | None, *, top_limit: int = 4, example_limit: int = 2) -> dict[str, Any]:
    counts = gate_counts if isinstance(gate_counts, dict) else {}
    examples = gate_examples if isinstance(gate_examples, dict) else {}
    total = sum(int(v) for v in counts.values())
    top = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:max(1, int(top_limit or 4))]
    top_text = '; '.join(f'{reason}:{count}' for reason, count in top) if top else '-'
    example_parts: list[str] = []
    for reason, _count in top[:max(1, int(example_limit or 2))]:
        samples = [str(x) for x in (examples.get(reason) or []) if str(x).strip()]
        if samples:
            example_parts.append(f'{reason}=>{samples[0]}')
    example_text = '; '.join(example_parts) if example_parts else '-'
    return {
        'total': total,
        'top': top,
        'top_text': top_text,
        'example_text': example_text,
        'synthesis_skip': synthesis_skip_summary(counts, examples),
    }
