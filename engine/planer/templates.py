from __future__ import annotations

from typing import Any, Dict


def build_templates(blueprint: Dict[str, Any]) -> Dict[str, str]:
    campaign_id = blueprint["campaign_id"]
    source_hash = blueprint["source_program_hash_sha256"]
    scope = blueprint.get('structured_scope') if isinstance(blueprint.get('structured_scope'), dict) else {}
    task_families = blueprint.get('task_family_seeds') if isinstance(blueprint.get('task_family_seeds'), dict) else {}
    hints = blueprint.get('planner_hints') if isinstance(blueprint.get('planner_hints'), dict) else {}
    domains = [str(d) for d in (scope.get('domains') or [])]
    oos = [str(d) for d in (scope.get('out_of_scope_targets') or [])]
    fam_lines = []
    for host, fams in list(task_families.items())[:40]:
        fam_lines.append(f"- {host}: {', '.join(str(x) for x in (fams or []))}")
    candidate_targets = [str(x) for x in (hints.get('candidate_targets') or [])]

    return {
        "campaign.md": f"""# RAVEN-CLAW Campaign Configuration

Generated from PLANER blueprint: {blueprint.get('campaign_name', blueprint.get('campaign_name_template', 'CAMPAIGN'))}

<!-- PLANER:BEGIN campaign -->
Campaign ID: {campaign_id}
Source Hash: {source_hash}
PLANER Version: {blueprint['schema_version']}
Interpretation Markers: enabled
<!-- PLANER:END campaign -->

## Campaign Scope

""" + '\n'.join(f"- {d}" for d in domains) + f"""

## Out of Scope

""" + ('\n'.join(f"- {d}" for d in oos) if oos else '- (none)') + f"""

## Recommended Task Families

""" + ('\n'.join(fam_lines) if fam_lines else '- recon') + f"""

## Candidate Targets From LLM

""" + ('\n'.join(f"- {d}" for d in candidate_targets) if candidate_targets else '- (none)') + f"""

## Rules
- Stay in-scope only.
- No destructive testing.
- Owner approval required for risky vectors.
""",
        "policy.yaml": f"""# PLANER overlay (non-destructive)
planer:
  campaign_id: {campaign_id}
  source_hash: {source_hash}
  interpretation_enabled: true
""",
        "whitelist.yaml": """# PLANER overlay (non-destructive)
planer:
  recommendations:
    - curl
    - ffuf
    - nmap
""",
        "budgets.yaml": """# PLANER overlay (non-destructive)
planer:
  variant_budgets:
    cost_effective: 0
    easy_to_hard: 0
    high_reward_high_effort: 0
""",
        "proxy.yaml": """# PLANER overlay (non-destructive)
planer:
  recommended_mode: per_target
  requires_owner_approval_for_override: true
""",
    }
