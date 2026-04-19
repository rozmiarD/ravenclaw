#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from paths import REPORTS_DIR  # type: ignore
from planer import build_or_load_campaign_plan


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="PLANER pre-campaign blueprint generator")
    p.add_argument("--scope-txt", required=True, help="Path to plain-text bug bounty scope/program file")
    p.add_argument("--flags-json", default="{}", help="Operator flags JSON")
    p.add_argument("--history-json", default="{}", help="Optional campaign history JSON")
    p.add_argument("--force-new-blueprint", action="store_true", help="Force new blueprint even when source hash matches existing campaign")
    p.add_argument(
        "--registry",
        default=str(REPORTS_DIR / "campaign_registry"),
        help="Campaign registry directory",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    scope_text = Path(args.scope_txt).read_text(encoding="utf-8")
    flags = json.loads(args.flags_json)
    history = json.loads(args.history_json)

    result = build_or_load_campaign_plan(
        raw_scope_text=scope_text,
        operator_flags=flags,
        history=history,
        registry_root=Path(args.registry),
        force_new_blueprint=bool(args.force_new_blueprint),
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))

    if result.get("status") == "created":
        print("\nInterpretive decisions:")
        for item in result.get("interpretations", []):
            print(f"- [{item['confidence']}] {item['rule_id']} -> {item['decision']}")


if __name__ == "__main__":
    main()
