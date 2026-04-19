# Output target formats

PLANER emits both JSON and YAML artifacts:

1. Root immutable blueprint
- `blueprint.json`
- `blueprint.yaml`

2. Registry metadata
- `latest.json`

3. Non-destructive configuration templates/overlays
- `templates/campaign.md`
- `templates/policy.yaml`
- `templates/whitelist.yaml`
- `templates/budgets.yaml`
- `templates/proxy.yaml`

All interpretation decisions are stored under `interpretations[]` inside blueprint.
