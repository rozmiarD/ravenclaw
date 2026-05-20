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
