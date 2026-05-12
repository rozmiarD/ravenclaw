# PLANER Agent (RAVEN-CLAW)

## Purpose
PLANER generates an immutable campaign blueprint from operator input + plain-text bug bounty scope.
Its parser core is deterministic, but the full planning pipeline may be **hybrid** when LLM-assisted interpretation/reconciliation contributes.

## Project structure
- `engine/plan_campaign.py` — entrypoint demo script
- `engine/planer/parser.py` — source text parsing + hashing
- `engine/planer/interpretation.py` — interpretation log generation
- `engine/planer/blueprint.py` — root blueprint builder
- `engine/planer/identity.py` — planner identity / provenance hashing helpers
- `engine/planer/schema.py` — internal schema checks
- `engine/planer/templates.py` — non-destructive overlay templates
- `engine/planer/registry.py` — immutable campaign registry/versioning
- `engine/planer/planner.py` — orchestrator API
- `engine/planer/schemas/*` — artifact schema files
- `engine/planer/tests/test_planer.py` — unit tests

## Deployment
1. Ensure Python deps: `pip install pyyaml`
2. Run tests:
   ```bash
   python3 -m unittest engine.planer.tests.test_planer
   ```
3. Run planner:
   ```bash
   python3 engine/plan_campaign.py --scope-txt engine/planer/examples/sample_scope.txt --flags-json '{"homelab":false}'
   ```

## Registry output
By default plans are stored in:
`<workspace>/reports/campaign_registry/<campaign_key>/versions/vXXXX/`

If you want the runtime root to differ from the script checkout, set `RAVENCLAW_WORKSPACE=/path/to/workspace`.

Each version contains:
- `blueprint.json`
- `blueprint.yaml`
- `templates/*.yaml|*.md`

## Integration with orchestrator
Preflight before campaign start:
```bash
python3 engine/plan_campaign.py --scope-txt /path/to/program.txt --flags-json '{"homelab":false}'
```
If status is `existing` or `created` with operator approval then proceed with `auto_campaign.py`.

## Notes
- PLANER parser behavior is deterministic for identical parser inputs.
- Full planning provenance may be `deterministic` or `hybrid` depending on LLM-assisted interpretation/reconciliation.
- PLANER prefers reusing existing plans by stronger `planner_identity_hash`, with fallback compatibility for older source-hash-only registry entries.
- PLANER does not overwrite existing campaign files; it emits overlays/templates only.
