# LogDash Service Notes

This file documents how the Flask/SQLite log dashboard is managed as a user-level systemd service.

## Service location
- Unit file: `~/.config/systemd/user/logdash.service`
- Working dir: `<workspace>/logdash`
- Virtualenv Python: `<workspace>/logdash/.venv/bin/python`
- Port: `9091` (loopback-only, use SSH tunnel if you need remote access)

If the runtime root should differ from the unit checkout path, set `RAVENCLAW_WORKSPACE=/path/to/workspace` in the systemd unit environment. If runtime state, SQLite storage, or pipeline configuration must live elsewhere, also set `RAVENCLAW_REPORTS_DIR=/path/to/reports`, `RAVENCLAW_LOGDASH_DB=/path/to/logs.db`, and `RAVENCLAW_PIPELINE_CONFIG=/path/to/pipeline_config.json`.

## Managing the service
```bash
systemctl --user status logdash.service   # check current state
systemctl --user restart logdash.service  # restart after code changes
journalctl --user -u logdash.service -f   # live logs
```

The unit is enabled, so it auto-starts when the user session comes up. Service restarts automatically on crash with a 5 second backoff.

## Deployment workflow
1. Activate the virtual environment to install/update dependencies:
   ```bash
   cd <workspace>/logdash
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Apply code changes and restart the service (`systemctl --user restart logdash.service`).

## Troubleshooting checklist
- Ensure `curl -I http://127.0.0.1:9091` returns `200 OK`.
- If the port is busy, check for old processes (`ps -ef | grep app.py`).
- For permission/logging issues, inspect `journalctl --user -u logdash.service`.
- If the service fails repeatedly, check the configured SQLite file for corruption (`sqlite3 "$RAVENCLAW_LOGDASH_DB" "PRAGMA integrity_check;"`, or `logs.db` when no override is set).

Keep this README alongside the Flask app so anyone touching LogDash knows how it's kept alive.
