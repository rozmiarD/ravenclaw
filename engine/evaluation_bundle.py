from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Dict

from semantic_lineage import ensure_semantic_lineage, ensure_semantic_lineage_summary  # type: ignore


REPLAY_BUNDLE_SCHEMA_VERSION = 'phase5-replay-bundle-v1'
REPLAY_DATASET_SCHEMA_VERSION = 'phase5-replay-dataset-v1'
DEFAULT_VARIANT_ID = 'baseline'


def _safe_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _safe_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _safe_str(value: Any) -> str:
    return str(value or '').strip()


def _clean(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(k): _clean(v)
            for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))
            if v not in (None, '', [], {})
        }
    if isinstance(value, list):
        return [_clean(v) for v in value if v not in (None, '', [], {})]
    return value


def _sha256_json(value: Any) -> str:
    payload = json.dumps(_clean(value), ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def normalize_variant_ref(value: Any) -> Dict[str, Any]:
    raw = _safe_dict(value)
    variant_id = _safe_str(raw.get('variant_id') or raw.get('id') or DEFAULT_VARIANT_ID).lower() or DEFAULT_VARIANT_ID
    family = _safe_str(raw.get('family') or 'runtime_evaluation').lower() or 'runtime_evaluation'
    metric_version = _safe_str(raw.get('metric_version') or 'phase5-metrics-v1') or 'phase5-metrics-v1'
    replay_version = _safe_str(raw.get('replay_version') or 'phase5-replay-v1') or 'phase5-replay-v1'
    return {
        'variant_id': variant_id,
        'label': _safe_str(raw.get('label') or variant_id),
        'family': family,
        'description': _safe_str(raw.get('description') or ''),
        'metric_version': metric_version,
        'replay_version': replay_version,
        'overrides': copy.deepcopy(_safe_dict(raw.get('overrides'))),
    }


def estimate_request_count(run: Dict[str, Any] | None) -> int:
    run = _safe_dict(run)
    compiler = _safe_dict(run.get('engine_compiler'))
    runtime_task = _safe_dict(run.get('runtime_task'))
    candidates = [
        _safe_list(compiler.get('tool_chain')),
        _safe_list(compiler.get('tool_chain_requested')),
        _safe_list(runtime_task.get('tool_chain')),
    ]
    for item in candidates:
        if item:
            return max(1, len(item))
    return 1


def _normalized_runtime_decision(run: Dict[str, Any]) -> Dict[str, Any]:
    runtime_decision = _safe_dict(run.get('runtime_decision'))
    explain = _safe_dict(runtime_decision.get('explain') or run.get('decision_explain'))
    runtime_decision['requested_action'] = _safe_str(runtime_decision.get('requested_action') or runtime_decision.get('selected_primary_action') or run.get('decision_selected_action'))
    runtime_decision['requested_reason'] = _safe_str(runtime_decision.get('requested_reason') or runtime_decision.get('selection_reason') or run.get('decision_selection_reason'))
    runtime_decision['selected_primary_action'] = _safe_str(runtime_decision.get('selected_primary_action') or runtime_decision['requested_action'])
    runtime_decision['selection_reason'] = _safe_str(runtime_decision.get('selection_reason') or runtime_decision['requested_reason'])
    runtime_decision['selected_secondary_action'] = _safe_str(runtime_decision.get('selected_secondary_action') or run.get('decision_selected_secondary_action'))
    runtime_decision['secondary_selection_reason'] = _safe_str(runtime_decision.get('secondary_selection_reason') or run.get('decision_secondary_selection_reason'))
    runtime_decision['effective_status'] = _safe_str(runtime_decision.get('effective_status') or run.get('decision_effective_status') or 'pending')
    runtime_decision['effective_action'] = _safe_str(runtime_decision.get('effective_action') or run.get('decision_effective_action'))
    runtime_decision['effective_secondary_action'] = _safe_str(runtime_decision.get('effective_secondary_action') or run.get('decision_effective_secondary_action'))
    runtime_decision['intent_flags'] = _safe_dict(runtime_decision.get('intent_flags') or runtime_decision.get('action_flags') or run.get('decision_intent_flags'))
    runtime_decision['effective_flags'] = _safe_dict(runtime_decision.get('effective_flags') or run.get('decision_effective_flags') or run.get('decision_flags'))
    runtime_decision['effective_reasons'] = _safe_dict(runtime_decision.get('effective_reasons') or run.get('decision_effective_reasons'))
    runtime_decision['effective_blockers'] = _safe_dict(runtime_decision.get('effective_blockers') or run.get('decision_effective_blockers'))
    runtime_decision['effective_summary'] = _safe_str(runtime_decision.get('effective_summary') or run.get('decision_effective_summary'))
    runtime_decision['eligibility'] = _safe_dict(runtime_decision.get('eligibility') or run.get('decision_eligibility'))
    runtime_decision['economics'] = copy.deepcopy(_safe_dict(runtime_decision.get('economics') or run.get('decision_economics')))
    runtime_decision['explain'] = copy.deepcopy(explain)
    return runtime_decision


def build_replay_bundle(
    run: Dict[str, Any],
    *,
    run_id: str = '',
    campaign_key: str = '',
    source_artifact: str = 'summary_vector',
    variant: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    run = _safe_dict(run)
    runtime_task = copy.deepcopy(_safe_dict(run.get('runtime_task')))
    lineage = ensure_semantic_lineage(
        lineage=_safe_dict(run.get('semantic_lineage')),
        task=run,
        runtime_task=runtime_task,
        source='evaluation_bundle',
    )
    lineage_summary = ensure_semantic_lineage_summary(
        summary=_safe_dict(run.get('semantic_lineage_summary')),
        lineage=lineage,
        task=run,
        runtime_task=runtime_task,
        source='evaluation_bundle',
    )
    runtime_decision = _normalized_runtime_decision(run)
    analysis_contract = copy.deepcopy(_safe_dict(run.get('analysis_contract')))
    signal_contract = copy.deepcopy(_safe_dict(run.get('signal_contract')))
    variant_ref = normalize_variant_ref(variant)
    contamination = copy.deepcopy(_safe_dict(run.get('run_contamination')))
    request_count_estimate = int(run.get('request_count_estimate') or estimate_request_count(run) or 1)
    replay_core = {
        'schema_version': REPLAY_BUNDLE_SCHEMA_VERSION,
        'source_artifact': _safe_str(source_artifact or 'summary_vector'),
        'run_identity': {
            'run_id': _safe_str(run_id),
            'campaign_key': _safe_str(campaign_key or run.get('campaign_key')),
            'index': int(run.get('index') or 0),
            'plan_name': _safe_str(run.get('plan_name')),
            'objective': _safe_str(run.get('objective')),
            'target': _safe_str(run.get('target')),
            'task_family': _safe_str(run.get('task_family') or lineage_summary.get('task_family')),
        },
        'variant': variant_ref,
        'runtime_task': runtime_task,
        'runtime_decision': runtime_decision,
        'signal_contract': signal_contract,
        'semantic_lineage': lineage,
        'semantic_lineage_summary': lineage_summary,
        'execution': {
            'engine_status': _safe_str(run.get('engine_status')),
            'auditor_decision': _safe_str(run.get('auditor_decision')),
            'classification': _safe_str(run.get('classification')),
            'mode': _safe_str(run.get('mode')),
            'aggression': run.get('aggression'),
            'owner_override': bool(run.get('owner_override', False)),
            'owner_approved_auth': bool(run.get('owner_approved_auth', False)),
            'execution_gate': copy.deepcopy(_safe_dict(run.get('execution_gate'))),
            'semantic_loss_class': _safe_str(run.get('semantic_loss_class') or analysis_contract.get('semantic_loss_class') or (_safe_dict(_safe_dict(run.get('engine_compiler')).get('semantic_loss_policy')).get('loss_class'))),
        },
        'analysis': {
            'analysis_contract': analysis_contract,
            'success_semantics': copy.deepcopy(_safe_dict(run.get('success_semantics'))),
        },
        'governance': {
            'run_contamination': contamination,
            'request_count_estimate': max(1, request_count_estimate),
        },
    }
    replay_core['bundle_id'] = _sha256_json({
        'source_artifact': replay_core['source_artifact'],
        'run_identity': replay_core['run_identity'],
        'variant': replay_core['variant'],
        'lineage_sha256': replay_core['semantic_lineage_summary'].get('lineage_sha256'),
    })
    return replay_core


MANDATORY_TOP_LEVEL_FIELDS = (
    'schema_version',
    'bundle_id',
    'run_identity',
    'runtime_decision',
    'signal_contract',
    'execution',
    'semantic_lineage_summary',
    'variant',
)


def validate_replay_bundle(bundle: Dict[str, Any] | None) -> Dict[str, Any]:
    raw = _safe_dict(bundle)
    missing = [field for field in MANDATORY_TOP_LEVEL_FIELDS if field not in raw]
    if missing:
        raise ValueError(f'replay_bundle_missing:{",".join(missing)}')
    if _safe_str(raw.get('schema_version')) != REPLAY_BUNDLE_SCHEMA_VERSION:
        raise ValueError('replay_bundle_schema_version_invalid')
    run_identity = _safe_dict(raw.get('run_identity'))
    if not _safe_str(run_identity.get('target')):
        raise ValueError('replay_bundle_missing:run_identity.target')
    if not _safe_str(run_identity.get('objective')):
        raise ValueError('replay_bundle_missing:run_identity.objective')
    if not isinstance(raw.get('runtime_decision'), dict):
        raise ValueError('replay_bundle_runtime_decision_invalid')
    if not isinstance(raw.get('signal_contract'), dict):
        raise ValueError('replay_bundle_signal_contract_invalid')
    if not isinstance(raw.get('execution'), dict):
        raise ValueError('replay_bundle_execution_invalid')
    if not isinstance(raw.get('semantic_lineage_summary'), dict):
        raise ValueError('replay_bundle_lineage_summary_invalid')
    if not _safe_str(_safe_dict(raw.get('variant')).get('variant_id')):
        raise ValueError('replay_bundle_variant_invalid')
    normalized = copy.deepcopy(raw)
    normalized['variant'] = normalize_variant_ref(raw.get('variant'))
    normalized['runtime_decision'] = _normalized_runtime_decision(_safe_dict({'runtime_decision': raw.get('runtime_decision')}))
    normalized['run_identity'] = {
        'run_id': _safe_str(run_identity.get('run_id')),
        'campaign_key': _safe_str(run_identity.get('campaign_key')),
        'index': int(run_identity.get('index') or 0),
        'plan_name': _safe_str(run_identity.get('plan_name')),
        'objective': _safe_str(run_identity.get('objective')),
        'target': _safe_str(run_identity.get('target')),
        'task_family': _safe_str(run_identity.get('task_family')),
    }
    normalized['governance'] = _safe_dict(raw.get('governance'))
    normalized['governance']['request_count_estimate'] = max(1, int(normalized['governance'].get('request_count_estimate') or 1))
    return normalized


def build_replay_dataset_from_summary(summary: Dict[str, Any] | None, *, variant: Dict[str, Any] | None = None) -> Dict[str, Any]:
    summary = _safe_dict(summary)
    run_id = _safe_str(summary.get('run_id'))
    campaign_key = _safe_str(_safe_dict(summary.get('campaign_validation')).get('campaign_key'))
    bundles = [
        build_replay_bundle(item, run_id=run_id, campaign_key=campaign_key, source_artifact='auto_campaign_summary_vector', variant=variant)
        for item in _safe_list(summary.get('vectors'))
        if isinstance(item, dict)
    ]
    dataset_core = {
        'schema_version': REPLAY_DATASET_SCHEMA_VERSION,
        'run_id': run_id,
        'campaign_key': campaign_key,
        'variant': normalize_variant_ref(variant),
        'bundle_count': len(bundles),
        'bundles': bundles,
    }
    dataset_core['dataset_id'] = _sha256_json({
        'schema_version': dataset_core['schema_version'],
        'run_id': dataset_core['run_id'],
        'campaign_key': dataset_core['campaign_key'],
        'variant': dataset_core['variant'],
        'bundle_ids': [bundle.get('bundle_id') for bundle in bundles],
    })
    return dataset_core
