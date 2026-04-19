# Prepare public examples

Use this note when filling `public-snapshot/examples/` after running `scripts/assemble_public_snapshot.sh`.

## Campaign registry example
Create one sanitized example campaign-registry entry that:
- preserves versioned blueprint structure
- removes private target references
- replaces deployment-specific campaign names/templates
- avoids real operator notes or local identifiers

## Runtime/state examples
Create small redacted JSON/YAML examples that show schema shape only.
Do not copy live local files such as:
- `reports/.auto_campaign.state.json`
- `reports/.runtime_snapshot.json`
- `reports/.host_state.json`
- `reports/.owner_approval_actions.json`
- `reports/state/*.json`

## Auth and harness caution
`auth-harness/` is not part of the default public snapshot scaffold.
If it is ever considered for publication, review it separately for secret-loading assumptions, cookie handling, and deployment-specific auth flow instructions.

## Rule
Examples should be intentionally authored for publication, not copied blindly from the live working tree.
