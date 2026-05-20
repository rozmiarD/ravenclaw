# OpenClaw Redaction Output Matrix

## Status

Contract/test surface only. This matrix does not implement an OpenClaw adapter,
does not authorize live target execution, and does not define a production
transport policy.

Machine-readable matrix helpers live in `engine/openclaw_adapter_readiness.py`.

## Channels

The current readiness contract covers these future OpenClaw output surfaces:

- direct chat;
- group chat;
- file output;
- embed output;
- attachment output;
- private/operator-only output.

Every channel requires deterministic redaction before send.

## Always redact

The following classes must be blocked from public-safe OpenClaw outputs:

- credentials;
- tokens;
- cookies;
- auth headers;
- private paths;
- operator memory;
- raw runtime logs;
- raw stdout;
- raw stderr;
- request/response bodies;
- private target identifiers.

## Public-safe fields

Public-safe OpenClaw outputs may carry compact references and status fields:

- scope reference;
- policy-decision status and reason code;
- prepared-spec reference;
- approved-spec reference;
- runner-receipt reference;
- execution-truth label;
- evidence-review reference;
- validation-receipt reference;
- explicit non-claims.

## Required non-claims

Any public-safe OpenClaw output must preserve these non-claims:

- no live target execution authorization;
- no chat-text command authority;
- no private operator state publication;
- no live-vulnerability claim from dry-run artifacts;
- no OpenClaw/MCP/A2A adapter implementation in this readiness slice.

## Validation

```bash
python -m pytest -q engine/tests/test_openclaw_adapter_readiness.py
```
