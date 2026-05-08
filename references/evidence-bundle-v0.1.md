# EvidenceBundle v0.1

## Purpose

`EvidenceBundle` is the public-safe evidence artifact at the end of the Security Contract Layer proof trace.

For v0.1 it is intentionally narrow: it captures dry-run contract-proof criteria and explicit non-claims for the public demo bundle. It does not publish live-target evidence, raw stdout/stderr, credentials, or private operator state.

## Producer

Current public demo producer:
- `build_evidence_bundle_artifact(...)` in `engine/public_demo_bundle.py`

The markdown companion is produced by:
- `build_evidence_summary_markdown(...)` in `engine/public_demo_bundle.py`

## Schema

Schema file:
- `schemas/evidence_bundle.v0.1.schema.json`

Schema version:

```json
"schema_version": "2026-04-28.evidence-bundle.v0.1"
```

Artifact type:

```json
"artifact_type": "evidence_bundle"
```

## Required fields

Top-level required fields:
- `schema_version`
- `artifact_type`
- `proof_mode`
- `status`
- `met`
- `gap`
- `evidence_items`
- `criteria`
- `non_claims`
- `source_artifacts`
- `public_safety`

Criteria items require:
- `id`
- `claim`
- `source`
- `status`

## Public proof semantics

A v0.1 public demo evidence bundle can claim:
- demo mode was used;
- policy decision was captured;
- prepared spec was redacted;
- approved spec was produced;
- execution receipt records dry-run/mock execution;
- public target remains `example.com` / local-safe.

## OODA control decisions

If a receipt includes GovEngine OODA control decisions, an evidence bundle may reference them as governance evidence: OODA control was evaluated, an interrupting decision stopped or reshaped execution, and the decision is linked to the approved execution shape.

The evidence bundle must still keep OODA data compact and public-safe. It should reference decision/reason/summary fields, not raw telemetry or raw output.

See `references/ooda-receipt-evidence-notes.md`.

## Non-claims

A v0.1 public demo evidence bundle must not claim:
- live vulnerability evidence;
- successful exploitation;
- execution against private/live operator targets;
- that raw stdout/stderr or sensitive local paths are safe to publish.

## Compatibility notes

This is not yet the full runtime qualification/evidence schema used for live campaigns. It is a public-stable demo proof artifact. A later schema can extend this toward qualification outputs from `engine/vuln_qualification.py` and policy checks from `engine/evidence_policy.py` without weakening the public safety guarantees here.
