from __future__ import annotations

import math
from typing import Any, Dict, Iterable

from runtime_economics_insights import build_runtime_explainability_insights  # type: ignore


def _learning_excluded(run: dict) -> bool:
    contamination = run.get('run_contamination') if isinstance(run.get('run_contamination'), dict) else {}
    return bool(contamination.get('learning_excluded', False))


def _run_capability(run: dict) -> str:
    brain = run.get('brain') if isinstance(run.get('brain'), dict) else {}
    summary = run.get('brain_reasoning_summary') if isinstance(run.get('brain_reasoning_summary'), dict) else {}
    return str(brain.get('capability') or summary.get('capability') or '').strip().lower()


def aggregate_runtime_economics(runs: Iterable[dict]) -> Dict[str, Any]:
    runs_list = [r for r in runs if isinstance(r, dict)]
    total = len(runs_list)
    insights = build_runtime_explainability_insights(runs_list)
    if total == 0:
        return {
            'cost_per_run': 0.0,
            'cost_per_promising': 0.0,
            'cost_per_probable': 0.0,
            'cost_per_confirmed': 0.0,
            'confirm_conversion_rate': 0.0,
            'reconsult_roi': 0.0,
            'avg_net_utility': 0.0,
            'family_efficiency': [],
            'host_efficiency': [],
            'capability_efficiency': [],
            'empirical_steering': {'excluded_runs': 0, 'family_prior_top': [], 'capability_prior_top': []},
            'explainability': insights,
        }

    total_cost = 0.0
    promising = 0
    probable = 0
    confirmed = 0
    confirm_selected = 0
    reconsult_hits = 0
    family_stats: dict[str, dict[str, float]] = {}
    host_stats: dict[str, dict[str, float]] = {}
    capability_stats: dict[str, dict[str, float]] = {}
    total_net_utility = 0.0
    excluded_runs = 0

    for run in runs_list:
        if _learning_excluded(run):
            excluded_runs += 1
            continue
        econ = run.get('decision_economics') if isinstance(run.get('decision_economics'), dict) else {}
        explain = run.get('decision_explain') if isinstance(run.get('decision_explain'), dict) else {}
        scores = explain.get('scores') if isinstance(explain.get('scores'), dict) else {}
        total_cost += float(econ.get('cost_weight') or 0.0)
        if bool(run.get('promising')):
            promising += 1
        verdict = str(((run.get('qualification') or {}).get('verdict') if isinstance(run.get('qualification'), dict) else '') or '').lower()
        if verdict == 'probable':
            probable += 1
        elif verdict == 'confirmed':
            confirmed += 1
        flags = run.get('decision_flags') if isinstance(run.get('decision_flags'), dict) else {}
        if bool(flags.get('confirm')):
            confirm_selected += 1
        why = explain.get('why') if isinstance(explain.get('why'), list) else []
        if any('reconsult' in str(x) for x in why):
            reconsult_hits += 1
        utility = run.get('runtime_utility') if isinstance(run.get('runtime_utility'), dict) else {}
        total_net_utility += float(utility.get('net_utility_score') or 0.0)

        family = str(run.get('task_family') or 'generic')
        host = str(run.get('host') or '') or _host_from_target(str(run.get('target') or ''))
        capability = _run_capability(run) or 'unknown'
        _update_bucket(family_stats, family, run, econ, scores)
        _update_bucket(host_stats, host or 'unknown', run, econ, scores)
        _update_bucket(capability_stats, capability, run, econ, scores)

    return {
        'cost_per_run': round(total_cost / max(1, total), 3),
        'cost_per_promising': round(total_cost / max(1, promising), 3),
        'cost_per_probable': round(total_cost / max(1, probable), 3),
        'cost_per_confirmed': round(total_cost / max(1, confirmed), 3),
        'confirm_conversion_rate': round(confirmed / max(1, confirm_selected), 3),
        'reconsult_roi': round(reconsult_hits / max(1, total), 3),
        'avg_net_utility': round(total_net_utility / max(1, max(1, total - excluded_runs)), 3),
        'family_efficiency': _finalize_buckets(family_stats),
        'host_efficiency': _finalize_buckets(host_stats),
        'capability_efficiency': _finalize_buckets(capability_stats),
        'empirical_steering': {
            'excluded_runs': excluded_runs,
            'family_prior_top': _empirical_prior_top(family_stats),
            'capability_prior_top': _empirical_prior_top(capability_stats),
        },
        'explainability': insights,
    }


def _host_from_target(target: str) -> str:
    try:
        from urllib.parse import urlparse
        return (urlparse(target).hostname or '').strip().lower()
    except Exception:
        return ''


def _update_bucket(buckets: dict[str, dict[str, float]], key: str, run: dict, econ: dict, scores: dict) -> None:
    b = buckets.setdefault(key, {'runs': 0.0, 'promising': 0.0, 'probable': 0.0, 'confirmed': 0.0, 'value': 0.0, 'cost': 0.0, 'priority': 0.0, 'partial_or_better': 0.0, 'utility': 0.0})
    b['runs'] += 1
    if bool(run.get('promising')):
        b['promising'] += 1
    verdict = str(((run.get('qualification') or {}).get('verdict') if isinstance(run.get('qualification'), dict) else '') or '').lower()
    if verdict == 'probable':
        b['probable'] += 1
    elif verdict == 'confirmed':
        b['confirmed'] += 1
    success_status = str(((run.get('signal_contract') or {}).get('success_outcome') or {}).get('status') or run.get('success_criteria_eval') or '').strip().lower()
    if success_status in {'partial', 'met'}:
        b['partial_or_better'] += 1
    utility = run.get('runtime_utility') if isinstance(run.get('runtime_utility'), dict) else {}
    b['utility'] += float(utility.get('net_utility_score') or 0.0)
    b['value'] += float(econ.get('value_estimate') or 0.0)
    b['cost'] += float(econ.get('cost_weight') or 0.0)
    b['priority'] += float(econ.get('priority_score') or scores.get('priority_score') or 0.0)


def _finalize_buckets(buckets: dict[str, dict[str, float]]) -> list[dict[str, Any]]:
    out = []
    for key, data in buckets.items():
        runs = max(1.0, data['runs'])
        avg_value = round(data['value'] / runs, 3)
        avg_cost = round(data['cost'] / runs, 3)
        avg_priority = round(data['priority'] / runs, 3)
        partial_or_better_rate = round(data['partial_or_better'] / runs, 3)
        avg_utility = round(data['utility'] / runs, 3)
        explain_parts: list[str] = []
        if int(data['confirmed']) > 0:
            explain_parts.append(f"confirmed={int(data['confirmed'])}")
        elif int(data['probable']) > 0:
            explain_parts.append(f"probable={int(data['probable'])}")
        if partial_or_better_rate >= 0.5:
            explain_parts.append(f"partial+={partial_or_better_rate}")
        if avg_utility > 0.4:
            explain_parts.append(f"utility={avg_utility}")
        if avg_cost > avg_value:
            explain_parts.append(f"cost>{avg_value}")
        out.append({
            'key': key,
            'runs': int(data['runs']),
            'promising': int(data['promising']),
            'probable': int(data['probable']),
            'confirmed': int(data['confirmed']),
            'avg_value': avg_value,
            'avg_cost': avg_cost,
            'avg_priority': avg_priority,
            'partial_or_better_rate': partial_or_better_rate,
            'avg_utility': avg_utility,
            'explain': '; '.join(explain_parts[:3]) or 'steady sample',
        })
    out.sort(key=lambda x: (-x['avg_priority'], -x['confirmed'], -x['probable'], x['key']))
    return out[:12]


def _empirical_prior_top(buckets: dict[str, dict[str, float]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for key, data in buckets.items():
        runs = max(1.0, data['runs'])
        sample = float(data['runs'])
        yield_rate = (data['promising'] + data['probable'] + (data['confirmed'] * 1.2) + data['partial_or_better']) / (runs * 2.8)
        avg_priority = data['priority'] / runs
        avg_utility = data['utility'] / runs
        exploration_bonus = min(0.12, math.sqrt(1.75 / (sample + 1.0)) * 0.18)
        empirical_score = max(-0.5, min(1.5, (yield_rate * 0.8) + (avg_priority * 0.18) + (avg_utility * 0.14) + exploration_bonus))
        out.append({
            'key': key,
            'runs': int(data['runs']),
            'yield_rate': round(yield_rate, 3),
            'avg_priority': round(avg_priority, 3),
            'avg_utility': round(avg_utility, 3),
            'exploration_bonus': round(exploration_bonus, 3),
            'empirical_score': round(empirical_score, 3),
        })
    out.sort(key=lambda x: (-x['empirical_score'], -x['runs'], x['key']))
    return out[:8]
