This directory is an assembled public snapshot scaffold.

It intentionally excludes mixed local/internal areas such as:
- reports/ (except prepared examples added later)
- memory/
- logs/
- pending/
- tmp/
- state/
- workspace/operator-specific bootstrap files

It also prunes obvious snapshot noise such as:
- engine/tmp/
- legacy generated engine JSON mirrors like `engine/public_targets_plan.json` and `engine/context_summary.json`
- internal runtime role guidance under `engine/system_memory/`
- embedded virtualenvs like `logdash/.venv`
- internal model wiring like `logdash/agents_config.json`
- __pycache__/
- test/tool caches
- *.log, `logdash.out`, and `logs.db` artifacts

`auth-harness/` is not included by default in this scaffold and should only be considered for publication after separate secret-flow review.

Before publishing, review the assembled snapshot and populate examples/ with intentionally prepared redacted samples.
