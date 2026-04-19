from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from planer.parser import parse_program_text
from planer.interpretation import build_interpretations
from planer.blueprint import build_blueprint
from planer.schema import validate_blueprint
from planer.planner import build_or_load_campaign_plan

SCOPE = """
Program scope:
- app.example.com
- api.example.com
Allowed: recon, xss, idor
Disallowed: dos, brute force
""".strip()


class TestPlaner(unittest.TestCase):
    def test_deterministic_parsing(self):
        a = parse_program_text(SCOPE, {"homelab": False})
        b = parse_program_text(SCOPE, {"homelab": False})
        self.assertEqual(a, b)

    def test_interpretation_logging(self):
        parsed = parse_program_text(SCOPE, None)
        logs = build_interpretations(parsed, SCOPE)
        self.assertTrue(len(logs) >= 1)
        for item in logs:
            self.assertIn("source_fragment", item)
            self.assertIn("rule_id", item)
            self.assertIn("confidence", item)

    def test_schema_conformance(self):
        parsed = parse_program_text(SCOPE, None)
        logs = build_interpretations(parsed, SCOPE)
        blueprint = build_blueprint(parsed, {"flags": {}}, logs)
        validate_blueprint(blueprint)

    def test_parser_and_blueprint_emit_target_type_for_runtime_consumers(self):
        parsed = parse_program_text(SCOPE, None)
        self.assertTrue(all('target_type' in t for t in parsed['targets']))
        self.assertTrue(all('target_type' in p for p in parsed['target_profiles'].values()))
        logs = build_interpretations(parsed, SCOPE)
        blueprint = build_blueprint(parsed, {"flags": {}}, logs)
        self.assertTrue(all('target_type' in p for p in blueprint['target_profiles'].values()))

    def test_blueprint_emits_planner_directives_and_experiment_intents(self):
        parsed = parse_program_text(SCOPE, None)
        logs = build_interpretations(parsed, SCOPE)
        blueprint = build_blueprint(parsed, {"flags": {}}, logs)
        self.assertIn('planner_directives', blueprint)
        self.assertIn('experiment_intents', blueprint)
        self.assertTrue(blueprint['experiment_intents'])
        directives = blueprint['planner_directives']
        self.assertIn('constraints', directives)
        self.assertIn('preferences', directives)
        self.assertIn('unknowns', directives)
        intent = blueprint['experiment_intents'][0]
        self.assertIn('capability_candidates', intent)
        self.assertIn('recommended_action_types', intent)
        self.assertIn('planner_constraints', intent)
        self.assertIn('planner_preferences', intent)
        self.assertIn('runtime_task_contract', intent)
        self.assertIn('planning_ladder', intent)
        self.assertEqual(intent['runtime_task_contract']['schema_version'], 2)
        self.assertEqual(intent['action_type'], intent['runtime_task_contract']['action_type'])
        self.assertEqual(intent['capability'], intent['runtime_task_contract']['capability'])
        self.assertEqual(intent['planning_ladder']['current_stage'], intent['exploit_ladder']['stage'])
        self.assertEqual(intent['planning_ladder']['planning_mode'], 'laddered')
        self.assertIn('exploit_ladder', intent)
        self.assertIn('actor_requirements', intent)
        self.assertIn('session_requirements', intent)
        self.assertIn('promotion_policy', intent)
        self.assertIn('approval_sensitivity', intent)
        if intent['task_family'] == 'authz':
            self.assertEqual(intent['exploit_ladder']['stage'], 'control_boundary_confirmation')
            self.assertTrue(intent['actor_requirements']['differential'])
            self.assertIn(intent['runtime_task_contract']['task_success_criteria'], [
                'Demonstrate a stable actor or object-boundary delta with a valid negative control.',
                'Demonstrate a stable actor or object-boundary delta with a valid negative control.'
            ])

    def test_multi_variant_generation(self):
        parsed = parse_program_text(SCOPE, None)
        logs = build_interpretations(parsed, SCOPE)
        blueprint = build_blueprint(parsed, {"flags": {}}, logs)
        self.assertEqual(len(blueprint["variants"]), 3)
        names = {v["name"] for v in blueprint["variants"]}
        self.assertEqual(names, {"cost_effective", "easy_to_hard", "high_reward_high_effort"})

    def test_blueprint_contains_stronger_identity_and_hybrid_provenance(self):
        parsed = parse_program_text(SCOPE, {"homelab": False})
        logs = build_interpretations(parsed, SCOPE)
        blueprint = build_blueprint(parsed, {
            "flags": {"homelab": False},
            "llm_interpretation": {"enabled": True, "used": True, "errors": [], "llm_confidence": 0.8, "conflicts": [], "suggested_attack_vectors": ["authz"], "ambiguities": ["subdomain overlap"]},
        }, logs)
        self.assertIn("operator_flags_hash_sha256", blueprint)
        self.assertIn("planner_semantics_hash_sha256", blueprint)
        self.assertIn("planner_identity_hash_sha256", blueprint)
        self.assertEqual(blueprint["planner_provenance_mode"], "hybrid")
        self.assertFalse(blueprint["versioning"]["deterministic"])
        self.assertEqual(blueprint["versioning"]["planner_provenance_mode"], "hybrid")

    def test_blueprint_emits_target_specific_ladders(self):
        scope = """
Program scope:
- api.example.com
- static.example.com
Allowed: recon, idor
""".strip()
        parsed = parse_program_text(scope, None)
        logs = build_interpretations(parsed, scope)
        blueprint = build_blueprint(parsed, {"flags": {}}, logs)
        api_authz = next(i for i in blueprint['experiment_intents'] if i['target_host'] == 'api.example.com' and i['task_family'] == 'authz')
        static_tls = next(i for i in blueprint['experiment_intents'] if i['target_host'] == 'static.example.com' and i['task_family'] == 'tls_assessment')
        self.assertEqual(api_authz['planning_ladder']['current_stage'], 'control_boundary_confirmation')
        self.assertIn('bounded_exploit_proof', api_authz['planning_ladder']['stage_progression'])
        self.assertEqual(api_authz['planning_ladder']['recommended_action_types'][0], 'differential_probe')
        self.assertEqual(static_tls['planning_ladder']['current_stage'], 'discovery')
        self.assertEqual(static_tls['planning_ladder']['stage_progression'], ['discovery', 'report_artifact_capture'])
        self.assertEqual(static_tls['planning_ladder']['recommended_action_types'][0], 'fingerprint_probe')

    def test_existing_plan_reuse_same_flags(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            first = build_or_load_campaign_plan(SCOPE, {"homelab": False}, {}, root)
            self.assertEqual(first["status"], "created")
            second = build_or_load_campaign_plan(SCOPE, {"homelab": False}, {}, root)
            self.assertEqual(second["status"], "existing")

    def test_different_flags_change_planner_identity_and_avoid_reuse(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            first = build_or_load_campaign_plan(SCOPE, {"homelab": False}, {}, root)
            self.assertEqual(first["status"], "created")
            second = build_or_load_campaign_plan(SCOPE, {"homelab": True}, {}, root)
            self.assertEqual(second["status"], "created")
            self.assertNotEqual(first["planner_identity_hash"], second["planner_identity_hash"])

    def test_legacy_source_hash_registry_entry_remains_readable(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            parsed = parse_program_text(SCOPE, {"homelab": False})
            legacy_dir = root / parsed["source_hash"][:16]
            legacy_dir.mkdir(parents=True, exist_ok=True)
            (legacy_dir / "latest.json").write_text(json.dumps({
                "campaign_id": "legacy-campaign",
                "campaign_name": "LEGACY-V1-OLD",
                "version": 1,
                "source_program_hash_sha256": parsed["source_hash"],
                "path": "versions/v0001"
            }), encoding="utf-8")

            reused = build_or_load_campaign_plan(SCOPE, {"homelab": False}, {}, root)
            self.assertEqual(reused["status"], "existing")
            self.assertEqual(reused["registry"]["campaign_id"], "legacy-campaign")

    def test_legacy_registry_entry_with_mismatched_identity_is_not_reused(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            parsed = parse_program_text(SCOPE, {"homelab": False})
            legacy_dir = root / parsed["source_hash"][:16]
            legacy_dir.mkdir(parents=True, exist_ok=True)
            (legacy_dir / "latest.json").write_text(json.dumps({
                "campaign_id": "legacy-campaign",
                "campaign_name": "LEGACY-V1-OLD",
                "version": 1,
                "source_program_hash_sha256": parsed["source_hash"],
                "planner_identity_hash_sha256": "deadbeef" * 8,
                "path": "versions/v0001"
            }), encoding="utf-8")

            result = build_or_load_campaign_plan(SCOPE, {"homelab": False}, {}, root)
            self.assertEqual(result["status"], "created")
            self.assertNotEqual(result["planner_identity_hash"], "deadbeef" * 8)


if __name__ == "__main__":
    unittest.main()
