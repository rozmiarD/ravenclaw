from __future__ import annotations

"""OpenClaw carrier-readiness contracts for Ravenclaw.

These helpers describe the minimum redaction/output and approval-UX boundaries
for a future OpenClaw carrier.  They do not implement an adapter and must stay
free of transport/runtime side effects.
"""

from typing import Any, Mapping


CHANNELS = (
    'direct_chat',
    'group_chat',
    'file_output',
    'embed_output',
    'attachment_output',
    'private_operator_output',
)

ALWAYS_REDACT = (
    'credentials',
    'tokens',
    'cookies',
    'auth_headers',
    'private_paths',
    'operator_memory',
    'raw_runtime_logs',
    'raw_stdout',
    'raw_stderr',
    'request_response_bodies',
    'private_target_identifiers',
)

PUBLIC_SAFE_FIELDS = (
    'scope_ref',
    'policy_decision_status',
    'reason_code',
    'prepared_spec_ref',
    'approved_spec_ref',
    'runner_receipt_ref',
    'execution_truth_label',
    'evidence_review_ref',
    'validation_receipt_ref',
    'non_claims',
)

FIXTURE_INPUT_FIELDS = PUBLIC_SAFE_FIELDS + (
    'policy_decision',
    'runner_supervision_status',
    'chat_text_contains_command',
    'stop_signal',
)

APPROVAL_UX_STEPS = (
    'show_scope_before_action',
    'show_policy_decision',
    'show_prepared_spec_as_proposal',
    'show_approved_spec_as_authority_boundary',
    'show_runner_supervision_state',
    'show_dry_run_live_truth',
    'show_evidence_review_and_non_claims',
    'require_operator_confirmation_for_sensitive_actions',
)

REQUIRED_NON_CLAIMS = (
    'does_not_authorize_live_target_execution',
    'does_not_turn_chat_text_into_command_authority',
    'does_not_publish_private_operator_state',
    'does_not_claim_live_vulnerability_discovery_from_dry_run',
    'does_not_implement_openclaw_mcp_or_a2a_adapter',
)

COMMAND_AUTHORITY_STOP_REASONS = (
    'chat_text_contains_command',
    'missing_policy_decision',
    'missing_prepared_spec',
    'missing_approved_spec',
    'prepared_spec_treated_as_approved',
    'missing_runner_supervision',
)

ROLLBACK_STOP_STATES = (
    'scope_ambiguity',
    'owner_review_required',
    'pause_requested',
    'abort_requested',
    'cooldown_required',
    'validation_failed',
    'redaction_failed',
    'dry_run_live_truth_ambiguous',
)


def openclaw_redaction_matrix() -> dict[str, Any]:
    outputs = []
    for channel in CHANNELS:
        public = channel != 'private_operator_output'
        outputs.append({
            'channel': channel,
            'public_safe': public,
            'requires_redaction_before_send': True,
            'always_redact': list(ALWAYS_REDACT),
            'allowed_fields': list(PUBLIC_SAFE_FIELDS) if public else list(PUBLIC_SAFE_FIELDS) + ['operator_only_notes'],
            'blocked_fields': list(ALWAYS_REDACT),
            'non_claims_required': list(REQUIRED_NON_CLAIMS),
        })
    return {
        'artifact_type': 'openclaw_redaction_output_matrix',
        'schema_version': 'v0.1',
        'target_carrier': 'openclaw',
        'adapter_status': 'not_implemented',
        'outputs': outputs,
        'non_claims': list(REQUIRED_NON_CLAIMS),
    }


def openclaw_approval_ux_sketch() -> dict[str, Any]:
    return {
        'artifact_type': 'openclaw_approval_ux_sketch',
        'schema_version': 'v0.1',
        'target_carrier': 'openclaw',
        'adapter_status': 'not_implemented',
        'steps': [
            {
                'step': 'show_scope_before_action',
                'required_artifact': 'scope/input',
                'authority_boundary': 'operator_scope',
            },
            {
                'step': 'show_policy_decision',
                'required_artifact': 'PolicyDecision',
                'authority_boundary': 'ravenclaw_policy_auditor',
            },
            {
                'step': 'show_prepared_spec_as_proposal',
                'required_artifact': 'PreparedExecutionSpec',
                'authority_boundary': 'proposal_not_execution_authority',
            },
            {
                'step': 'show_approved_spec_as_authority_boundary',
                'required_artifact': 'ApprovedExecutionSpec',
                'authority_boundary': 'execution_engine_input',
            },
            {
                'step': 'show_runner_supervision_state',
                'required_artifact': 'GovSupervisionPlan/GovRunnerLease/GovRunnerReceipt',
                'authority_boundary': 'govengine_runner_supervision',
            },
            {
                'step': 'show_dry_run_live_truth',
                'required_artifact': 'ExecutionReceipt',
                'authority_boundary': 'receipt_truth_label',
            },
            {
                'step': 'show_evidence_review_and_non_claims',
                'required_artifact': 'GovEvidenceQualification/GovReviewResult',
                'authority_boundary': 'evidence_review_not_live_vuln_claim',
            },
            {
                'step': 'require_operator_confirmation_for_sensitive_actions',
                'required_artifact': 'ApprovalRequest',
                'authority_boundary': 'operator_confirmation',
            },
        ],
        'required_step_order': list(APPROVAL_UX_STEPS),
        'non_claims': list(REQUIRED_NON_CLAIMS),
    }


def openclaw_command_authority_policy() -> dict[str, Any]:
    return {
        'artifact_type': 'openclaw_command_authority_policy',
        'schema_version': 'v0.1',
        'target_carrier': 'openclaw',
        'adapter_status': 'not_implemented',
        'required_authority_chain': [
            'operator_scope',
            'policy_decision',
            'prepared_execution_spec',
            'approved_execution_spec',
            'runner_supervision',
            'execution_receipt',
        ],
        'blocked_inputs': [
            'chat_text_command',
            'model_prose_command',
            'raw_shell_snippet',
            'unapproved_tool_call',
            'prepared_spec_without_approval',
        ],
        'stop_reasons': list(COMMAND_AUTHORITY_STOP_REASONS),
        'non_claims': list(REQUIRED_NON_CLAIMS),
    }


def evaluate_command_authority_request(request: Mapping[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    if request.get('chat_text_contains_command') is True:
        reasons.append('chat_text_contains_command')
    if request.get('policy_decision') != 'approved':
        reasons.append('missing_policy_decision')
    if not request.get('prepared_spec_ref'):
        reasons.append('missing_prepared_spec')
    if not request.get('approved_spec_ref'):
        reasons.append('missing_approved_spec')
    if request.get('prepared_spec_ref') and request.get('prepared_spec_ref') == request.get('approved_spec_ref'):
        reasons.append('prepared_spec_treated_as_approved')
    if request.get('runner_supervision_status') != 'ready':
        reasons.append('missing_runner_supervision')
    return {
        'status': 'blocked' if reasons else 'ready_for_ravenclaw_execution_engine',
        'stop_reasons': reasons,
        'non_claims': list(REQUIRED_NON_CLAIMS),
    }


def openclaw_rollback_stop_contract() -> dict[str, Any]:
    return {
        'artifact_type': 'openclaw_rollback_stop_contract',
        'schema_version': 'v0.1',
        'target_carrier': 'openclaw',
        'adapter_status': 'not_implemented',
        'states': list(ROLLBACK_STOP_STATES),
        'required_propagation': [
            'surface_to_operator',
            'preserve_structured_reason',
            'block_execution_until_reviewed',
            'record_validation_receipt_ref',
        ],
        'non_claims': list(REQUIRED_NON_CLAIMS),
    }


def build_openclaw_fixture_packet(carrier_input: Mapping[str, Any]) -> dict[str, Any]:
    """Project carrier-shaped fixture input into a public-safe presenter packet."""

    raw = dict(carrier_input)
    public_summary = {
        field: raw[field]
        for field in PUBLIC_SAFE_FIELDS
        if field in raw and field != 'non_claims'
    }
    authority = evaluate_command_authority_request(raw)
    redacted_fields = sorted(str(field) for field in ALWAYS_REDACT if field in raw)
    stop_signal = raw.get('stop_signal') if isinstance(raw.get('stop_signal'), Mapping) else None
    stop_state = evaluate_rollback_stop_signal(stop_signal) if stop_signal is not None else None
    failed_checks = []
    if redacted_fields:
        failed_checks.append('sensitive_fields_redacted')
    if authority['status'] == 'blocked':
        failed_checks.append('authority_chain_blocked')
    if stop_state is not None and stop_state['status'] != 'propagated':
        failed_checks.append('stop_signal_blocked')
    public_summary['non_claims'] = list(REQUIRED_NON_CLAIMS)
    return {
        'artifact_type': 'openclaw_fixture_presenter_packet',
        'schema_version': 'v0.1',
        'target_carrier': 'openclaw',
        'adapter_status': 'not_implemented',
        'fixture_mode': 'presenter_only',
        'status': 'blocked' if failed_checks else 'presentable_fixture_packet',
        'accepted_input_fields': sorted(str(field) for field in raw if field in FIXTURE_INPUT_FIELDS),
        'redacted_input_fields': redacted_fields,
        'public_summary': public_summary,
        'authority_decision': authority,
        'stop_signal_decision': stop_state,
        'failed_checks': failed_checks,
        'non_claims': list(REQUIRED_NON_CLAIMS),
    }


def evaluate_rollback_stop_signal(signal: Mapping[str, Any]) -> dict[str, Any]:
    state = str(signal.get('state') or '').strip()
    receipt_ref = str(signal.get('validation_receipt_ref') or '').strip()
    operator_visible = signal.get('operator_visible') is True
    structured_reason = str(signal.get('reason_code') or '').strip()
    failed = []
    if state not in ROLLBACK_STOP_STATES:
        failed.append('unknown_stop_state')
    if not operator_visible:
        failed.append('not_operator_visible')
    if not structured_reason:
        failed.append('missing_structured_reason')
    if state == 'validation_failed' and not receipt_ref:
        failed.append('missing_validation_receipt_ref')
    return {
        'status': 'propagated' if not failed else 'blocked',
        'failed_checks': failed,
        'state': state,
        'non_claims': list(REQUIRED_NON_CLAIMS),
    }


def evaluate_openclaw_readiness(
    matrix: Mapping[str, Any],
    ux: Mapping[str, Any],
) -> dict[str, Any]:
    outputs = [item for item in matrix.get('outputs', []) if isinstance(item, Mapping)]
    steps = [item for item in ux.get('steps', []) if isinstance(item, Mapping)]
    step_order = [str(item.get('step')) for item in steps]
    public_outputs = [item for item in outputs if item.get('public_safe') is True]

    checks = {
        'matrix_artifact_type': matrix.get('artifact_type') == 'openclaw_redaction_output_matrix',
        'ux_artifact_type': ux.get('artifact_type') == 'openclaw_approval_ux_sketch',
        'adapter_not_implemented': matrix.get('adapter_status') == 'not_implemented'
        and ux.get('adapter_status') == 'not_implemented',
        'all_channels_present': [str(item.get('channel')) for item in outputs] == list(CHANNELS),
        'all_channels_redact_before_send': all(item.get('requires_redaction_before_send') is True for item in outputs),
        'public_outputs_block_secrets': all(
            set(ALWAYS_REDACT).issubset(set(str(field) for field in item.get('blocked_fields', [])))
            for item in public_outputs
        ),
        'public_outputs_require_non_claims': all(
            set(REQUIRED_NON_CLAIMS).issubset(set(str(claim) for claim in item.get('non_claims_required', [])))
            for item in public_outputs
        ),
        'approval_step_order': step_order == list(APPROVAL_UX_STEPS),
        'prepared_before_approved': step_order.index('show_prepared_spec_as_proposal')
        < step_order.index('show_approved_spec_as_authority_boundary')
        if set(('show_prepared_spec_as_proposal', 'show_approved_spec_as_authority_boundary')).issubset(step_order)
        else False,
        'command_policy_blocks_chat_authority': evaluate_command_authority_request({
            'chat_text_contains_command': True,
            'policy_decision': 'approved',
            'prepared_spec_ref': 'prepared-1',
            'approved_spec_ref': 'approved-1',
            'runner_supervision_status': 'ready',
        })['status'] == 'blocked',
        'rollback_contract_requires_operator_visibility': evaluate_rollback_stop_signal({
            'state': 'abort_requested',
            'reason_code': 'operator_abort',
            'operator_visible': False,
        })['status'] == 'blocked',
    }
    failed = [name for name, passed in checks.items() if not passed]
    return {
        'status': 'passed' if not failed else 'failed',
        'checks': checks,
        'failed_checks': failed,
        'non_claims': list(REQUIRED_NON_CLAIMS),
    }


def openclaw_readiness_status() -> dict[str, Any]:
    return evaluate_openclaw_readiness(openclaw_redaction_matrix(), openclaw_approval_ux_sketch())
