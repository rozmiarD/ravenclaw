# log_event.py — logdash compatible service event logger
# Compatible with both legacy (4 positional) and new flag-based CLI
# Usage (new): python log_event.py --tor ... --decision ... --status ... --result ... [--row-type ...] [--highlight] [--agent ...]
# Usage (legacy): python log_event.py SERVICE DECISION STATUS RESULT

import sys
import argparse
import datetime
import os
import sqlite3
from pathlib import Path

DB_PATH = Path(os.getenv("RAVENCLAW_LOGDASH_DB") or Path(__file__).resolve().parent / "logs.db").expanduser().resolve()

def main():
    parser = argparse.ArgumentParser(description="Insert a logdash service entry (pipeline/logger event)")
    parser.add_argument("--tor", type=str, help="Name of service/task/event")
    parser.add_argument("--decision", type=str, help="Decision label/operation")
    parser.add_argument("--status", type=str, help="Outcome/status")
    parser.add_argument("--result", type=str, help="Result/summary")
    parser.add_argument("--row-type", type=str, default="service", help="Row type (service/operation/entry)")
    parser.add_argument("--highlight", action="store_true", help="Highlight row in dashboard")
    parser.add_argument("--agent", type=str, default='', help="Agent name")

    # For legacy positional CLI
    parser.add_argument("args", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    # Use positional only if NOT provided new flags
    if args.tor is None and len(args.args) >= 4:
        tor, decision, status, result = args.args[:4]
        row_type = "service"
        highlight = 1
        agent = ''
    else:
        # Use flags
        if not (args.tor and args.decision and args.status and args.result):
            parser.error("Missing required log fields (use --tor, --decision, --status, --result)")
        tor = args.tor
        decision = args.decision
        status = args.status
        result = args.result
        row_type = args.row_type or "service"
        highlight = 1 if args.highlight else 0
        agent = args.agent or ''

    now = datetime.datetime.now(datetime.UTC).isoformat()
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO logs (timestamp, tor, agent, decision, status, result, row_type, highlight)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (now, tor, agent, decision, status, result, row_type, highlight)
    )
    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()
