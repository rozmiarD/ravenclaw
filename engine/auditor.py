#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RAVEN-CLAW AUDITOR

Local governance gate implementation used for structured evaluation paths and
maintenance tooling.

It evaluates actions from BRAIN and returns one of:
- approve
- reject
- owner_approval_required

Supported local action forms:
- run_command
- read_file
- write_file
- append_file
- list_dir
- mkdir
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from paths import WORKSPACE  # type: ignore
from campaign_utils import resolve_scope_text_path  # type: ignore

try:
    import yaml  # type: ignore
except Exception as e:  # pragma: no cover
    raise RuntimeError("Brak PyYAML. Zainstaluj: pip install pyyaml") from e


PROJECT_DIR = WORKSPACE.resolve()
SYSTEM_MEMORY_DIR = Path(__file__).resolve().parent / "system_memory"
AUDITOR_SYSTEM_MEMORY_PATH = SYSTEM_MEMORY_DIR / "auditor.md"


# ------------------------- helpers -------------------------


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _risk_to_num(risk: str) -> int:
    # low/medium/high + fallback
    mapping = {
        "none": 0,
        "low": 1,
        "medium": 2,
        "high": 3,
        "critical": 4,
    }
    return mapping.get((risk or "").strip().lower(), 1)


def _max_risk_for_aggression(level: int) -> str:
    # Prosty, praktyczny mapping
    if level <= 2:
        return "low"
    if level <= 5:
        return "medium"
    return "high"


def _resolve_in_project(path_raw: str) -> Path:
    if not path_raw:
        raise ValueError("Missing path")

    p = Path(path_raw).expanduser()
    if not p.is_absolute():
        p = PROJECT_DIR / p

    rp = p.resolve()
    try:
        rp.relative_to(PROJECT_DIR)
    except ValueError as e:
        raise ValueError(f"Path outside project: {rp}") from e
    return rp


def _is_under(path_obj: Path, base: Path) -> bool:
    try:
        path_obj.resolve().relative_to(base.resolve())
        return True
    except Exception:
        return False


# ------------------------- models -------------------------


@dataclass
class AuditResult:
    role: str
    decision: str
    reasons: List[str]
    warnings: List[str]
    approved_action: Optional[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "decision": self.decision,
            "reasons": self.reasons,
            "warnings": self.warnings,
            "approved_action": self.approved_action,
        }


# ------------------------- auditor core -------------------------


class Auditor:
    def __init__(self, policy_path: Path, budgets_path: Path, campaign_path: Path) -> None:
        self.policy_path = policy_path
        self.budgets_path = budgets_path
        self.campaign_path = campaign_path

        self.policy = _load_yaml(self.policy_path)
        self.budgets = _load_yaml(self.budgets_path)
        self.campaign_text = _read_text(self.campaign_path)

        self.system_memory_path = AUDITOR_SYSTEM_MEMORY_PATH
        self.system_memory = self._load_system_memory()

        self.default_aggression = int(
            self.policy.get("aggression", {}).get("default_level", 4)
        )

        # ---- Header / tag enforcement (configurable via policy) ----
        header_cfg = self.policy.get("request_headers", {}) or {}
        self.required_headers: List[str] = header_cfg.get("required", []) or []
        self.header_expected_values: Dict[str, str] = header_cfg.get("expected_values", {}) or {}
        self.enforce_headers: bool = bool(
            header_cfg.get("enforce", bool(self.required_headers or self.header_expected_values))
        )

        # limity file write/appends
        self.max_write_chars_auto = 200_000
        self.max_append_chars_auto = 200_000
        self.max_read_chars_auto = 100_000

        # critical files requiring owner approval on write
        self.critical_write_files = {
            "policy.yaml",
            "whitelist.yaml",
            "budgets.yaml",
            "proxy.yaml",
            "campaign.md",
            "soul.md",
        }

        # krytyczne katalogi (engine = kod wykonawczy)
        self.critical_dirs = {
            "engine",
        }

        # podejrzane wzorce shell
        self.suspicious_command_patterns: List[Tuple[str, re.Pattern[str]]] = [
            (r"\brm\b", re.compile(r"\brm\b", re.IGNORECASE)),
            (r"\bdd\b", re.compile(r"\bdd\b", re.IGNORECASE)),
            (r"\bmkfs", re.compile(r"\bmkfs(\.\w+)?\b", re.IGNORECASE)),
            (r":\(\)\s*\{", re.compile(r":\(\)\s*\{")),  # fork bomb
            (r"\bshutdown\b", re.compile(r"\bshutdown\b", re.IGNORECASE)),
            (r"\breboot\b", re.compile(r"\breboot\b", re.IGNORECASE)),
            (r"\bpoweroff\b", re.compile(r"\bpoweroff\b", re.IGNORECASE)),
            (r"\binit\s+0\b", re.compile(r"\binit\s+0\b", re.IGNORECASE)),
            (r"curl\ .*\|\s*(sh|bash)", re.compile(r"curl\b.*\|\s*(sh|bash)\b", re.IGNORECASE)),
            (r"wget\ .*\|\s*(sh|bash)", re.compile(r"wget\b.*\|\s*(sh|bash)\b", re.IGNORECASE)),
            (r">\s*/dev/sd[a-z]", re.compile(r">\s*/dev/sd[a-z]\b", re.IGNORECASE)),
            (r"\bchmod\s+777\b", re.compile(r"\bchmod\s+777\b", re.IGNORECASE)),
        ]

        # suspicious paths in action.path
        self.suspicious_path_fragments = [
            "..",
            "/etc/",
            "/root/",
            "/var/lib/",
            "/boot/",
            "/dev/",
            "/proc/",
            "/sys/",
        ]

    # ---------- system memory helpers ----------

    def _load_system_memory(self) -> str:
        SYSTEM_MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        if not self.system_memory_path.exists():
            self.system_memory_path.write_text(
                "# Auditor System Memory\n\n(autocreated)\n", encoding="utf-8"
            )
        return self.system_memory_path.read_text(encoding="utf-8")

    def append_system_memory(self, note: str) -> None:
        note = note.strip()
        if not note:
            return
        current = self._load_system_memory().rstrip()
        if current:
            current += "\n"
        updated = f"{current}- {note}\n"
        self.system_memory_path.write_text(updated, encoding="utf-8")
        self.system_memory = updated

    # ---------- public API ----------

    def evaluate(self, action: Dict[str, Any]) -> Dict[str, Any]:
        reasons: List[str] = []
        warnings: List[str] = []

        # minimalna walidacja
        role = str(action.get("role", "")).strip()
        action_type = str(action.get("action", "")).strip()

        # ---- Header / tag validation governed by policy ----
        if self.enforce_headers:
            headers = action.get("headers", {}) or {}
            missing = [h for h in self.required_headers if h not in headers]
            mismatched = []
            for h, expected in self.header_expected_values.items():
                if h not in headers:
                    missing.append(h)
                    continue
                if expected is not None and str(headers[h]).strip() != str(expected).strip():
                    mismatched.append(h)

            if missing:
                return AuditResult(
                    role="AUDITOR",
                    decision="reject",
                    reasons=[f"missing_required_headers:{','.join(sorted(set(missing)))}"],
                    warnings=[],
                    approved_action=None,
                ).to_dict()

            if mismatched:
                return AuditResult(
                    role="AUDITOR",
                    decision="owner_approval_required",
                    reasons=[f"header_value_mismatch:{','.join(sorted(set(mismatched)))}"],
                    warnings=[],
                    approved_action=None,
                ).to_dict()

        if role != "BRAIN":
            return AuditResult(
                role="AUDITOR",
                decision="reject",
                reasons=["role_must_be_BRAIN"],
                warnings=[],
                approved_action=None,
            ).to_dict()

        if not action_type:
            return AuditResult(
                role="AUDITOR",
                decision="reject",
                reasons=["missing_action_type"],
                warnings=[],
                approved_action=None,
            ).to_dict()

        # shared checks: aggression/risk
        requested_risk = str(action.get("risk", "low")).strip().lower()
        max_allowed_risk = _max_risk_for_aggression(self.default_aggression)
        reasons.append(
            f"aggression_level={self.default_aggression}, "
            f"max_allowed_risk={max_allowed_risk}, requested_risk={requested_risk}"
        )

        if _risk_to_num(requested_risk) > _risk_to_num(max_allowed_risk):
            return AuditResult(
                role="AUDITOR",
                decision="owner_approval_required",
                reasons=reasons + ["risk_above_aggression_limit"],
                warnings=warnings,
                approved_action=None,
            ).to_dict()

        # routing wg typu akcji
        try:
            if action_type == "run_command":
                decision, extra_reasons, extra_warnings, approved = self._eval_run_command(action)
            elif action_type in {"read_file", "write_file", "append_file", "list_dir", "mkdir"}:
                decision, extra_reasons, extra_warnings, approved = self._eval_file_action(action)
            else:
                return AuditResult(
                    role="AUDITOR",
                    decision="reject",
                    reasons=reasons + [f"unsupported_action:{action_type}"],
                    warnings=warnings,
                    approved_action=None,
                ).to_dict()
        except Exception as e:
            return AuditResult(
                role="AUDITOR",
                decision="reject",
                reasons=reasons + [f"audit_exception:{type(e).__name__}:{e}"],
                warnings=warnings,
                approved_action=None,
            ).to_dict()

        reasons.extend(extra_reasons)
        warnings.extend(extra_warnings)

        return AuditResult(
            role="AUDITOR",
            decision=decision,
            reasons=reasons,
            warnings=warnings,
            approved_action=approved,
        ).to_dict()

    # ---------- action evaluators ----------

    def _eval_run_command(
        self, action: Dict[str, Any]
    ) -> Tuple[str, List[str], List[str], Optional[Dict[str, Any]]]:
        reasons: List[str] = []
        warnings: List[str] = []

        cmd = str(action.get("command", "")).strip()
        cwd_raw = str(action.get("cwd", "")).strip()

        if not cmd:
            return "reject", ["missing_command"], warnings, None
        if not cwd_raw:
            return "reject", ["missing_cwd"], warnings, None

        # cwd scope
        try:
            cwd = _resolve_in_project(cwd_raw)
            reasons.append("cwd_in_scope")
        except Exception:
            return "reject", ["cwd_out_of_scope"], warnings, None

        # suspicious patterns
        suspicious_hits: List[str] = []
        for label, pattern in self.suspicious_command_patterns:
            if pattern.search(cmd):
                suspicious_hits.append(label)

        if suspicious_hits:
            for hit in suspicious_hits:
                reasons.append(f"suspicious_pattern_detected: {hit}")
            return "owner_approval_required", reasons, warnings, None
        else:
            reasons.append("no_suspicious_patterns")

        # budget hint (soft check na estimated_tokens)
        budget_reasons, budget_warnings, budget_decision = self._budget_hint(action)
        reasons.extend(budget_reasons)
        warnings.extend(budget_warnings)
        if budget_decision == "owner_approval_required":
            return "owner_approval_required", reasons, warnings, None
        if budget_decision == "reject":
            return "reject", reasons, warnings, None

        # Optional: simple heuristic for overly long commands
        if len(cmd) > 4000:
            warnings.append("very_long_command_string")
            return "owner_approval_required", reasons, warnings, None

        approved = dict(action)
        approved["cwd"] = str(cwd)
        return "approve", reasons, warnings, approved

    def _eval_file_action(
        self, action: Dict[str, Any]
    ) -> Tuple[str, List[str], List[str], Optional[Dict[str, Any]]]:
        reasons: List[str] = []
        warnings: List[str] = []

        action_type = str(action.get("action", "")).strip()

        # path / cwd fallback dla list_dir
        path_raw = str(action.get("path", "") or action.get("cwd", "")).strip()
        if not path_raw:
            return "reject", ["missing_path_or_cwd"], warnings, None

        # quick check for "ugly" paths before resolve
        path_raw_expanded = str(Path(path_raw).expanduser())
        for frag in self.suspicious_path_fragments:
            if frag in path_raw_expanded:
                return "reject", [f"suspicious_path_fragment:{frag}"], warnings, None

        # scope
        try:
            target = _resolve_in_project(path_raw)
            reasons.append("path_in_scope")
        except Exception:
            return "reject", ["path_out_of_scope"], warnings, None

        # budget hint (still useful for read/write if BRAIN provides estimated_tokens)
        budget_reasons, budget_warnings, budget_decision = self._budget_hint(action)
        reasons.extend(budget_reasons)
        warnings.extend(budget_warnings)
        if budget_decision == "owner_approval_required":
            return "owner_approval_required", reasons, warnings, None
        if budget_decision == "reject":
            return "reject", reasons, warnings, None

        # type-specific rules
        if action_type == "read_file":
            max_chars = int(action.get("max_chars", 20000) or 20000)
            if max_chars > self.max_read_chars_auto:
                warnings.append(f"max_chars_high:{max_chars}")
                return "owner_approval_required", reasons, warnings, None
            reasons.append("read_file_safe")

        elif action_type == "list_dir":
            reasons.append("list_dir_safe")

        elif action_type == "mkdir":
            # mkdir in critical directories? engine/ is also okay, but require owner approval if it is deep/execution-related
            rel = target.relative_to(PROJECT_DIR)
            first = rel.parts[0] if rel.parts else ""
            if first in self.critical_dirs:
                warnings.append("mkdir_in_critical_dir")
                return "owner_approval_required", reasons, warnings, None
            reasons.append("mkdir_safe")

        elif action_type in {"write_file", "append_file"}:
            content = str(action.get("content", ""))
            if not content:
                return "reject", ["missing_content"], warnings, None

            content_len = len(content)
            max_auto = (
                self.max_write_chars_auto if action_type == "write_file" else self.max_append_chars_auto
            )
            if content_len > max_auto:
                warnings.append(f"content_too_large_for_auto:{content_len}")
                return "owner_approval_required", reasons, warnings, None

            # krytyczny plik / kod wykonawczy -> owner approval
            rel = target.relative_to(PROJECT_DIR)
            first = rel.parts[0] if rel.parts else ""
            file_name = target.name

            if file_name in self.critical_write_files:
                reasons.append(f"critical_file_write:{file_name}")
                return "owner_approval_required", reasons, warnings, None

            if first in self.critical_dirs:
                reasons.append(f"write_in_critical_dir:{first}")
                return "owner_approval_required", reasons, warnings, None

            # heuristics for "weird" content
            suspicious_content = [
                r"\brm\s+-rf\b",
                r"\bdd\s+if=",
                r"\bmkfs",
                r"curl\b.*\|\s*(sh|bash)\b",
                r"wget\b.*\|\s*(sh|bash)\b",
            ]
            for pat in suspicious_content:
                if re.search(pat, content, re.IGNORECASE):
                    reasons.append(f"suspicious_content_pattern:{pat}")
                    return "owner_approval_required", reasons, warnings, None

            reasons.append(f"{action_type}_safe_noncritical")

        else:
            return "reject", [f"unsupported_file_action:{action_type}"], warnings, None

        approved = dict(action)
        approved["path"] = str(target)
        if "cwd" in approved and approved.get("cwd"):
            # normalize cwd too if provided
            try:
                approved["cwd"] = str(_resolve_in_project(str(approved["cwd"])))
            except Exception:
                # do not break approval for file actions if cwd was only decorative
                approved["cwd"] = str(PROJECT_DIR)

        return "approve", reasons, warnings, approved

    # ---------- budget checks ----------

    def _budget_hint(
        self, action: Dict[str, Any]
    ) -> Tuple[List[str], List[str], str]:
        """
        Soft-check:
        - estimated_tokens vs budget.max_tokens_per_cycle
        - estimated_tokens vs policy.safety.max_token_loss_per_cycle (if present)
        """
        reasons: List[str] = []
        warnings: List[str] = []

        est = action.get("estimated_tokens", None)
        if est is None:
            reasons.append("budget_hint_skipped_no_estimated_tokens")
            return reasons, warnings, "approve"

        try:
            est_int = int(est)
        except Exception:
            warnings.append("estimated_tokens_not_int")
            return reasons, warnings, "owner_approval_required"

        if est_int < 0:
            return ["estimated_tokens_negative"], warnings, "reject"

        budget_cfg = self.budgets.get("budget", {})
        max_tokens_per_cycle = int(budget_cfg.get("max_tokens_per_cycle", 0) or 0)

        safety_cfg = self.policy.get("safety", {})
        max_token_loss_per_cycle = int(safety_cfg.get("max_token_loss_per_cycle", 0) or 0)

        if max_tokens_per_cycle > 0 and est_int > max_tokens_per_cycle:
            reasons.append(
                f"budget_hint_exceeds_max_tokens_per_cycle:{est_int}>{max_tokens_per_cycle}"
            )
            return reasons, warnings, "reject"

        # "token loss" traktujemy jako bardziej restrykcyjny soft gate dla owner approval
        if max_token_loss_per_cycle > 0 and est_int > max_token_loss_per_cycle:
            reasons.append(
                f"budget_hint_above_token_loss_threshold:{est_int}>{max_token_loss_per_cycle}"
            )
            return reasons, warnings, "owner_approval_required"

        reasons.append("budget_hint_ok")
        return reasons, warnings, "approve"


# ------------------------- CLI -------------------------


def _default_paths() -> Tuple[Path, Path, Path]:
    base = PROJECT_DIR
    return base / "policy.yaml", base / "budgets.yaml", resolve_scope_text_path()


def main() -> int:
    default_policy, default_budgets, default_campaign = _default_paths()

    parser = argparse.ArgumentParser(description="RAVEN-CLAW Auditor")
    parser.add_argument("--action", required=True, help="JSON akcji od BRAIN")
    parser.add_argument("--policy", default=str(default_policy))
    parser.add_argument("--budgets", default=str(default_budgets))
    parser.add_argument("--campaign", default=str(default_campaign))
    args = parser.parse_args()

    try:
        action = json.loads(args.action)
        if not isinstance(action, dict):
            raise ValueError("Action JSON must be object")
    except Exception as e:
        print(json.dumps({
            "role": "AUDITOR",
            "decision": "reject",
            "reasons": [f"invalid_action_json:{e}"],
            "warnings": [],
            "approved_action": None
        }, ensure_ascii=False, indent=2))
        return 2

    auditor = Auditor(
        policy_path=Path(args.policy).expanduser(),
        budgets_path=Path(args.budgets).expanduser(),
        campaign_path=Path(args.campaign).expanduser(),
    )
    result = auditor.evaluate(action)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("decision") == "approve" else 1


if __name__ == "__main__":
    raise SystemExit(main())
