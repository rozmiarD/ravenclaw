from __future__ import annotations

from typing import Any, Dict

from govengine_security_helpers import evaluate_action_spec



def record_approval_transform(chain: list[dict], source: str, before: dict, after: dict) -> None:
    chain.append({
        'source': source,
        'before': {
            'decision': str(before.get('decision') or ''),
            'reason': str(before.get('reason') or '')[:220],
            'reason_code': str(before.get('reason_code') or ''),
        },
        'after': {
            'decision': str(after.get('decision') or ''),
            'reason': str(after.get('reason') or '')[:220],
            'reason_code': str(after.get('reason_code') or ''),
        },
    })



def tracked_auditor_replace(chain: list[dict], source: str, auditor: dict, **patch: Any) -> dict:
    before = dict(auditor or {})
    after = dict(before)
    after.update(patch)
    record_approval_transform(chain, source, before, after)
    return after



def tracked_auditor_constraint_raise(chain: list[dict], source: str, auditor: dict, aggression: int, reason_suffix: str, reason_code: str) -> dict:
    before = dict(auditor or {})
    constraints = dict(before.get('constraints') or {}) if isinstance(before.get('constraints'), dict) else {}
    constraints['aggression'] = int(aggression)
    after = dict(before)
    after['constraints'] = constraints
    after['reason'] = f"{str(before.get('reason') or '')} | {reason_suffix}"
    after['reason_code'] = reason_code
    record_approval_transform(chain, source, before, after)
    return after



def policy_gate(brain: Dict[str, Any], target: str, owner_approved_auth: bool, *, load_credentials_runtime_policy_fn) -> Dict[str, Any]:
    creds = load_credentials_runtime_policy_fn()
    effective_owner_approved_auth = bool(owner_approved_auth or creds.get('credentials_owner_approved', False))
    return evaluate_action_spec(brain, target, effective_owner_approved_auth, creds=creds)
