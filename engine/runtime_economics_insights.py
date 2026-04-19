from __future__ import annotations

from collections import Counter
from typing import Any, Dict, Iterable


def build_runtime_explainability_insights(runs: Iterable[dict]) -> Dict[str, Any]:
    why_counter: Counter[str] = Counter()
    blocker_counter: Counter[str] = Counter()
    effective_status_counter: Counter[str] = Counter()
    quality_total = 0.0
    quality_count = 0
    utility_total = 0.0
    utility_count = 0

    for run in runs:
        if not isinstance(run, dict):
            continue
        explain = run.get('decision_explain') if isinstance(run.get('decision_explain'), dict) else {}
        why = explain.get('why') if isinstance(explain.get('why'), list) else []
        blockers = explain.get('blockers') if isinstance(explain.get('blockers'), list) else []
        for item in why:
            text = str(item or '').strip()
            if text:
                why_counter[text] += 1
        for item in blockers:
            text = str(item or '').strip()
            if text:
                blocker_counter[text] += 1

        effective_status = str(run.get('decision_effective_status') or ((run.get('runtime_decision') or {}).get('effective_status') if isinstance(run.get('runtime_decision'), dict) else '') or '').strip()
        if effective_status:
            effective_status_counter[effective_status] += 1

        decision_quality = run.get('decision_quality') if isinstance(run.get('decision_quality'), dict) else {}
        if decision_quality:
            quality_total += float(decision_quality.get('decision_quality_score', 0.0) or 0.0)
            quality_count += 1

        runtime_utility = run.get('runtime_utility') if isinstance(run.get('runtime_utility'), dict) else {}
        if runtime_utility:
            utility_total += float(runtime_utility.get('net_utility_score', 0.0) or 0.0)
            utility_count += 1

    return {
        'top_why': [{'key': key, 'count': count} for key, count in why_counter.most_common(6)],
        'top_blockers': [{'key': key, 'count': count} for key, count in blocker_counter.most_common(6)],
        'effective_status_top': [{'key': key, 'count': count} for key, count in effective_status_counter.most_common(6)],
        'avg_decision_quality': round(quality_total / max(1, quality_count), 3),
        'avg_net_utility': round(utility_total / max(1, utility_count), 3),
        'sample_size': max(quality_count, utility_count, sum(effective_status_counter.values())),
    }
