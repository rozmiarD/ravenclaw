from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


def _campaign_key_from_hash(raw: str | None) -> str:
    return str(raw or '').strip()[:16]

from flask import Flask, jsonify, request

from context_contract import require_ctx
from planner_registry_loader import load_blueprint_json, load_json_list_file  # type: ignore


_PLANNER_API_CTX_KEYS = (
    "STATE",
    "selected_campaign_key",
    "load_campaign_blueprint_for_key",
    "runtime_plan_entries_from_blueprint",
    "write_runtime_plan",
    "load_runtime_plan_meta",
    "load_runtime_state",
    "load_runtime_snapshot",
    "selected_runtime_snapshot_view",
    "build_selected_campaign_projection",
    "projection_source_label",
    "load_planner_ui_state",
    "load_latest_blueprint",
    "_list_campaign_registry_items",
    "save_planner_ui_state",
    "activate_campaign_key",
    "RUNTIME_PLAN_PATH",
    "ENGINE_DIR",
    "WORKSPACE_DIR",
    "SCOPE_DIR",
    "BUDGETS_PATH",
    "PLAN_CAMPAIGN_SCRIPT",
    "PLANNER_REGISTRY_ROOT",
)


def register_planner_api(app: Flask, ctx: dict[str, Any]) -> None:
    ctx = require_ctx(ctx, *_PLANNER_API_CTX_KEYS)
    STATE = ctx["STATE"]
    selected_campaign_key = ctx["selected_campaign_key"]
    load_campaign_blueprint_for_key = ctx["load_campaign_blueprint_for_key"]
    runtime_plan_entries_from_blueprint = ctx["runtime_plan_entries_from_blueprint"]
    write_runtime_plan = ctx["write_runtime_plan"]
    load_runtime_plan_meta = ctx["load_runtime_plan_meta"]
    load_runtime_state = ctx["load_runtime_state"]
    load_runtime_snapshot = ctx["load_runtime_snapshot"]
    selected_runtime_snapshot_view = ctx["selected_runtime_snapshot_view"]
    build_selected_campaign_projection = ctx["build_selected_campaign_projection"]
    projection_source_label = ctx["projection_source_label"]
    load_planner_ui_state = ctx["load_planner_ui_state"]
    load_latest_blueprint = ctx["load_latest_blueprint"]
    _list_campaign_registry_items = ctx["_list_campaign_registry_items"]
    save_planner_ui_state = ctx["save_planner_ui_state"]
    activate_campaign_key = ctx["activate_campaign_key"]
    RUNTIME_PLAN_PATH = ctx["RUNTIME_PLAN_PATH"]
    ENGINE_DIR = ctx["ENGINE_DIR"]
    WORKSPACE_DIR = ctx["WORKSPACE_DIR"]
    SCOPE_DIR = ctx["SCOPE_DIR"]
    BUDGETS_PATH = ctx["BUDGETS_PATH"]
    PLAN_CAMPAIGN_SCRIPT = ctx["PLAN_CAMPAIGN_SCRIPT"]
    PLANNER_REGISTRY_ROOT = ctx["PLANNER_REGISTRY_ROOT"]

    def _resolve_scope_path(scope_txt: str | None) -> Path:
        raw = str(scope_txt or "").strip()
        if not raw:
            return SCOPE_DIR / "scope.txt"
        p = Path(raw)
        if p.is_absolute():
            return p
        workspace_candidate = (WORKSPACE_DIR / raw).resolve()
        scope_candidate = (SCOPE_DIR / raw).resolve()
        if workspace_candidate.exists() or '/' in raw or '\\' in raw:
            return workspace_candidate
        if scope_candidate.exists():
            return scope_candidate
        return workspace_candidate

    def _normalize_scope_txt_for_ui(scope_txt: str | None) -> str:
        path = _resolve_scope_path(scope_txt)
        try:
            return str(path.relative_to(WORKSPACE_DIR))
        except Exception:
            return str(path)

    def _ui_llm_interpret_value(data: dict[str, Any] | None = None, ui: dict[str, Any] | None = None) -> bool:
        if isinstance(data, dict) and 'llm_interpret' in data:
            return bool(data.get('llm_interpret'))
        flags = data.get('flags') if isinstance(data, dict) and isinstance(data.get('flags'), dict) else {}
        if 'llm_interpret' in flags:
            return bool(flags.get('llm_interpret'))
        return bool((ui or {}).get('llm_interpret', False))

    def _normalize_target_url(value: object) -> str:
        raw = str(value or '').strip()
        if not raw.startswith(('http://', 'https://')):
            return ''
        parsed = urlparse(raw)
        host = str(parsed.hostname or '').strip().lower()
        if not host:
            return ''
        out = f'{parsed.scheme.lower()}://{host}{parsed.path or "/"}'
        if parsed.query:
            out += f'?{parsed.query}'
        if parsed.fragment:
            out += f'#{parsed.fragment}'
        return out

    def _authoritative_scope_constraints(bp: dict[str, Any] | None) -> tuple[set[str], set[str], dict[str, set[str]]]:
        ss = bp.get('structured_scope') if isinstance(bp, dict) and isinstance(bp.get('structured_scope'), dict) else {}
        raw_assets = ss.get('authoritative_assets') if isinstance(ss.get('authoritative_assets'), list) else []
        domains = [str(x).strip().lower() for x in (ss.get('authoritative_domains', ss.get('domains')) or []) if str(x).strip()]
        exact_hosts: set[str] = set()
        domain_hosts: set[str] = set()
        exact_targets_by_host: dict[str, set[str]] = {}
        for raw in raw_assets:
            if not isinstance(raw, dict):
                continue
            asset_kind = str(raw.get('asset_kind') or 'domain').strip().lower() or 'domain'
            host = str(raw.get('host') or '').strip().lower()
            target = str(raw.get('target') or '').strip()
            if not host:
                continue
            if asset_kind == 'url':
                norm = _normalize_target_url(target)
                if norm:
                    exact_hosts.add(host)
                    exact_targets_by_host.setdefault(host, set()).add(norm)
            else:
                domain_hosts.add(host)
        if not domain_hosts and not exact_targets_by_host:
            domain_hosts.update(domains)
        return set(domains), domain_hosts, exact_targets_by_host

    def _runtime_snapshot_sections() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], bool]:
        runtime = load_runtime_state()
        snapshot = runtime.get('snapshot') if isinstance(runtime.get('snapshot'), dict) else load_runtime_snapshot()
        snapshot = snapshot if isinstance(snapshot, dict) else {}
        runtime = dict(runtime) if isinstance(runtime, dict) else {}
        runtime['snapshot'] = snapshot
        selected_view = selected_runtime_snapshot_view(runtime, selected_campaign_key())
        current = build_selected_campaign_projection(runtime, selected_view, STATE)
        filtered_snapshot = current.get('filtered_snapshot') if isinstance(current.get('filtered_snapshot'), dict) else {}
        snap_campaign = current.get('snap_campaign') if isinstance(current.get('snap_campaign'), dict) else {}
        snap_plan = current.get('snap_plan') if isinstance(current.get('snap_plan'), dict) else {}
        snapshot_matches_selected = bool(current.get('snapshot_matches_selected', False))
        return runtime, filtered_snapshot, snap_campaign, snap_plan, snapshot_matches_selected

    def _selected_campaign_plan_counts() -> tuple[int, int]:
        runtime, _filtered_snapshot, snap_campaign, snap_plan, _snapshot_matches_selected = _runtime_snapshot_sections()
        plan = runtime.get('runtime_plan') if isinstance(runtime.get('runtime_plan'), dict) else {}
        selected_key = str(selected_campaign_key() or '').strip()
        if not selected_key:
            return 0, 0
        generated = int(plan.get('generated') or plan.get('prepared_attacks') or STATE.get('prepared_attacks') or 0)
        target_count = int(plan.get('target_count') or plan.get('input_total') or STATE.get('planner_scope_targets') or 0)
        if str(snap_campaign.get('campaign_key') or '').strip() == selected_key:
            generated = int(snap_plan.get('generated') or snap_plan.get('prepared_attacks') or generated)
            target_count = int(snap_plan.get('target_count') or snap_plan.get('input_total') or target_count)
        return target_count, generated

    def _latest_campaign_key() -> str:
        items = _list_campaign_registry_items()
        if not items:
            return ''
        latest = max(items, key=lambda item: (int(item.get('version') or 0), str(item.get('key') or '')))
        return str(latest.get('key') or '').strip()

    def _campaign_key_from_planner_result(parsed: dict[str, Any] | None) -> str:
        if not isinstance(parsed, dict):
            return ''
        direct = _campaign_key_from_hash(parsed.get('planner_identity_hash'))
        if direct:
            return direct
        registry = parsed.get('registry') if isinstance(parsed.get('registry'), dict) else {}
        direct = _campaign_key_from_hash(registry.get('planner_identity_hash_sha256') or parsed.get('source_hash'))
        if direct:
            return direct
        return _latest_campaign_key()

    def _persist_blueprint_and_templates(version_dir: Path, bp_path: Path, blueprint: dict) -> None:
        bp_path.write_text(json.dumps(blueprint, indent=2, ensure_ascii=False), encoding="utf-8")
        try:
            import yaml  # type: ignore
            (version_dir / "blueprint.yaml").write_text(yaml.safe_dump(blueprint, sort_keys=False, allow_unicode=True), encoding="utf-8")
        except Exception:
            pass
        try:
            if str(ENGINE_DIR) not in sys.path:
                sys.path.insert(0, str(ENGINE_DIR))
            from planer.templates import build_templates  # type: ignore
            templates = build_templates(blueprint)
            tdir = version_dir / 'templates'
            tdir.mkdir(parents=True, exist_ok=True)
            for name, body in templates.items():
                (tdir / name).write_text(body, encoding='utf-8')
        except Exception:
            pass

    @app.route("/api/planner/run", methods=["POST"])
    def api_planner_run():
        data = request.get_json(silent=True) or {}
        scope_path = _resolve_scope_path(data.get("scope_txt"))
        if not scope_path.exists():
            return jsonify({"ok": False, "error": "scope_txt_missing", "path": str(scope_path)}), 400
        ui = load_planner_ui_state()
        if isinstance(ui, dict):
            ui["scope_txt"] = _normalize_scope_txt_for_ui(str(data.get("scope_txt") or str(scope_path)))
            ui["llm_interpret"] = _ui_llm_interpret_value(data, ui)
            save_planner_ui_state(ui)
        flags = data.get("flags") if isinstance(data.get("flags"), dict) else {}
        cmd = [
            sys.executable,
            str(PLAN_CAMPAIGN_SCRIPT),
            "--scope-txt",
            str(scope_path),
            "--flags-json",
            json.dumps(flags),
            "--registry",
            str(PLANNER_REGISTRY_ROOT),
        ]
        proc = subprocess.run(cmd, cwd=str(WORKSPACE_DIR), capture_output=True, text=True)
        if proc.returncode != 0:
            return jsonify({"ok": False, "error": "planner_run_failed", "stdout": proc.stdout[-4000:], "stderr": proc.stderr[-4000:]}), 500
        parsed = None
        for line in proc.stdout.splitlines():
            line = line.strip()
            if line.startswith("{") and line.endswith("}"):
                try:
                    parsed = json.loads(line)
                    break
                except Exception:
                    continue
        if parsed is None:
            try:
                parsed = json.loads(proc.stdout)
            except Exception:
                parsed = {"status": "ok"}
        selected_key = _campaign_key_from_planner_result(parsed)
        if selected_key:
            ui = load_planner_ui_state()
            if isinstance(ui, dict):
                ui["selected_campaign_key"] = selected_key
                save_planner_ui_state(ui)
            STATE["selected_campaign_key"] = selected_key
        return jsonify({"ok": True, "result": parsed, "stdout": proc.stdout[-4000:], "selected_campaign_key": selected_key})

    @app.route("/api/planner/scope-view")
    def api_planner_scope_view():
        scope_path = _resolve_scope_path(request.args.get("scope_txt"))
        if not scope_path.exists():
            return jsonify({"ok": False, "error": "scope_txt_missing", "path": str(scope_path)}), 404
        return jsonify({"ok": True, "content": scope_path.read_text(encoding="utf-8", errors="ignore"), "path": str(scope_path)})

    @app.route("/api/planner/scope-files")
    def api_planner_scope_files():
        items: list[str] = []
        if SCOPE_DIR.exists():
            for path in sorted(p for p in SCOPE_DIR.rglob('*') if p.is_file()):
                try:
                    items.append(str(path.relative_to(WORKSPACE_DIR)))
                except Exception:
                    items.append(str(path))
        return jsonify({"ok": True, "items": items, "root": str(SCOPE_DIR)})

    @app.route("/api/planner/blueprint-view")
    def api_planner_blueprint_view():
        key = str(request.args.get("campaign_key") or selected_campaign_key()).strip()
        if not key:
            return jsonify({"ok": False, "error": "missing_campaign_key"}), 400
        version_dir, bp_path, bp = load_campaign_blueprint_for_key(key)
        if not bp_path or not isinstance(bp, dict):
            return jsonify({"ok": False, "error": "blueprint_missing"}), 404
        return jsonify({"ok": True, "content": json.dumps(bp, indent=2, ensure_ascii=False), "path": str(bp_path)})

    @app.route("/api/planner/budgets-view")
    def api_planner_budgets_view():
        if not BUDGETS_PATH.exists():
            return jsonify({"ok": False, "error": "budgets_missing", "path": str(BUDGETS_PATH)}), 404
        return jsonify({"ok": True, "content": BUDGETS_PATH.read_text(encoding="utf-8", errors="ignore"), "path": str(BUDGETS_PATH)})

    @app.route("/api/planner/approve", methods=["POST"])
    def api_planner_approve():
        data = request.get_json(silent=True) or {}
        key = str(data.get("campaign_key") or selected_campaign_key()).strip()
        if not key:
            return jsonify({"ok": False, "error": "missing_campaign_key"}), 400
        version_dir, bp_path, bp = load_campaign_blueprint_for_key(key)
        if not bp_path or not isinstance(bp, dict):
            return jsonify({"ok": False, "error": "blueprint_missing"}), 404
        bp["operator_approval"] = {"status": "approved", "approved": True}
        _persist_blueprint_and_templates(version_dir, bp_path, bp)
        return jsonify({"ok": True})

    @app.route("/api/planner/promote-candidate-target", methods=["POST"])
    def api_planner_promote_candidate_target():
        data = request.get_json(silent=True) or {}
        key = str(data.get("campaign_key") or selected_campaign_key()).strip()
        host = str(data.get("host") or "").strip().lower()
        if not key or not host:
            return jsonify({"ok": False, "error": "missing_campaign_key_or_host"}), 400
        version_dir, bp_path, bp = load_campaign_blueprint_for_key(key)
        if not bp_path or not isinstance(bp, dict):
            return jsonify({"ok": False, "error": "blueprint_missing"}), 404
        ss = bp.get('structured_scope') if isinstance(bp.get('structured_scope'), dict) else {}
        if not isinstance(ss, dict):
            return jsonify({"ok": False, "error": "structured_scope_missing"}), 400
        cand = [str(x).strip().lower() for x in (ss.get('candidate_targets_from_llm') or []) if str(x).strip()]
        lifecycle = bp.get('candidate_target_lifecycle') if isinstance(bp.get('candidate_target_lifecycle'), dict) else {}
        if host not in cand and str(((lifecycle.get(host) or {}).get('state') if isinstance(lifecycle.get(host), dict) else '') or '') != 'pending':
            return jsonify({"ok": False, "error": "candidate_not_found"}), 404
        auth = [str(x).strip().lower() for x in (ss.get('authoritative_domains', ss.get('domains')) or []) if str(x).strip()]
        if host not in auth:
            auth.append(host)
            auth = sorted(set(auth))
        cand = [x for x in cand if x != host]
        ss['authoritative_domains'] = auth
        ss['domains'] = auth
        ss['candidate_targets_from_llm'] = cand
        lifecycle[host] = {'state': 'promoted', 'reviewed_at': utc_now_iso(), 'review_note': str(data.get('note') or '')}
        bp['candidate_target_lifecycle'] = lifecycle
        profs = bp.get('target_profiles') if isinstance(bp.get('target_profiles'), dict) else {}
        seeds = bp.get('task_family_seeds') if isinstance(bp.get('task_family_seeds'), dict) else {}
        if host not in profs:
            profs[host] = {'type': 'host', 'task_family_seeds': ['recon', 'tls_assessment']}
        if host not in seeds:
            seeds[host] = list((profs.get(host) or {}).get('task_family_seeds') or ['recon', 'tls_assessment'])
        bp['target_profiles'] = profs
        bp['task_family_seeds'] = seeds
        _persist_blueprint_and_templates(version_dir, bp_path, bp)
        return jsonify({"ok": True, "host": host, "authoritative_domains": len(auth), "remaining_candidates": len(cand)})

    @app.route("/api/planner/candidate-targets")
    def api_planner_candidate_targets():
        key = str(request.args.get("campaign_key") or selected_campaign_key()).strip()
        if not key:
            return jsonify({"ok": False, "error": "missing_campaign_key"}), 400
        version_dir, bp_path, bp = load_campaign_blueprint_for_key(key)
        if not bp_path or not isinstance(bp, dict):
            return jsonify({"ok": False, "error": "blueprint_missing"}), 404
        ss = bp.get('structured_scope') if isinstance(bp.get('structured_scope'), dict) else {}
        profs = bp.get('target_profiles') if isinstance(bp.get('target_profiles'), dict) else {}
        seeds = bp.get('task_family_seeds') if isinstance(bp.get('task_family_seeds'), dict) else {}
        lifecycle = bp.get('candidate_target_lifecycle') if isinstance(bp.get('candidate_target_lifecycle'), dict) else {}
        raw_candidates = [str(x).strip().lower() for x in (ss.get('candidate_targets_from_llm') or []) if str(x).strip()]
        for host, meta in lifecycle.items():
            if isinstance(meta, dict) and str(meta.get('state') or 'pending') == 'pending' and host not in raw_candidates:
                raw_candidates.append(str(host).strip().lower())
        items = []
        for host in raw_candidates:
            prof = profs.get(host) if isinstance(profs.get(host), dict) else {}
            meta = lifecycle.get(host) if isinstance(lifecycle.get(host), dict) else {}
            items.append({'host': host,'type': str(prof.get('target_type') or prof.get('type') or 'host'),'state': str(meta.get('state') or 'pending'),'review_note': str(meta.get('review_note') or ''),'task_family_seeds': list(seeds.get(host) or prof.get('task_family_seeds') or ['recon','tls_assessment'])})
        return jsonify({"ok": True, "campaign_key": key, "items": items})

    @app.route("/api/planner/review-candidate-target", methods=["POST"])
    def api_planner_review_candidate_target():
        data = request.get_json(silent=True) or {}
        key = str(data.get('campaign_key') or selected_campaign_key()).strip()
        host = str(data.get('host') or '').strip().lower()
        state = str(data.get('state') or '').strip().lower()
        note = str(data.get('note') or '').strip()
        if not key or not host or state not in {'rejected','deferred','pending'}:
            return jsonify({'ok': False, 'error': 'missing_or_invalid_review_payload'}), 400
        version_dir, bp_path, bp = load_campaign_blueprint_for_key(key)
        if not bp_path or not isinstance(bp, dict):
            return jsonify({'ok': False, 'error': 'blueprint_missing'}), 404
        lifecycle = bp.get('candidate_target_lifecycle') if isinstance(bp.get('candidate_target_lifecycle'), dict) else {}
        lifecycle[host] = {'state': state, 'reviewed_at': utc_now_iso(), 'review_note': note}
        bp['candidate_target_lifecycle'] = lifecycle
        _persist_blueprint_and_templates(version_dir, bp_path, bp)
        return jsonify({'ok': True, 'host': host, 'state': state})

    @app.route("/api/planner/generate-runtime-plan", methods=["POST"])
    def api_planner_generate_runtime_plan():
        data = request.get_json(silent=True) or {}
        key = str(data.get("campaign_key") or selected_campaign_key() or _latest_campaign_key()).strip()
        if not key:
            return jsonify({"ok": False, "error": "missing_campaign_key"}), 400
        version_dir, bp_path, bp = load_campaign_blueprint_for_key(key)
        if not bp_path or not isinstance(bp, dict):
            return jsonify({"ok": False, "error": "blueprint_missing"}), 404
        entries = runtime_plan_entries_from_blueprint(bp)
        if not entries:
            return jsonify({"ok": False, "error": "runtime_plan_empty_after_scope_filters"}), 400
        res = write_runtime_plan(entries, key, reason=str(data.get('reason') or 'manual_or_ui'))
        if not res.get('ok'):
            return jsonify(res), 400
        STATE["selected_campaign_key"] = key
        ui = load_planner_ui_state()
        if isinstance(ui, dict):
            ui["selected_campaign_key"] = key
            save_planner_ui_state(ui)
        STATE["prepared_attacks"] = len(entries)
        STATE["planner_scope_targets"] = int(res.get("target_count") or 0)
        STATE["runtime_plan_ok"] = True
        STATE["runtime_plan_error_preview"] = "-"
        return jsonify({"ok": True, "generated": len(entries), "target_count": int(res.get("target_count") or 0), "selected_campaign_key": key})

    @app.route("/api/campaign/validate-plan")
    def api_campaign_validate_plan():
        if not RUNTIME_PLAN_PATH.exists():
            return jsonify({"ok": False, "error": "runtime_plan_missing", "errors": ["runtime_plan_missing"]})
        data, source = load_json_list_file(RUNTIME_PLAN_PATH, description='runtime_plan_entries')
        if source == 'invalid_json_file':
            return jsonify({"ok": False, "error": "runtime_plan_invalid_json", "errors": ["runtime_plan_invalid_json"], "source": source})
        errors = []
        key = str(selected_campaign_key() or (load_runtime_plan_meta().get('campaign_key') if isinstance(load_runtime_plan_meta(), dict) else '') or '').strip()
        _version_dir, _bp_path, bp = load_campaign_blueprint_for_key(key) if key else (None, None, None)
        authoritative_domains, authoritative_domain_hosts, exact_targets_by_host = _authoritative_scope_constraints(bp if isinstance(bp, dict) else {})
        if not isinstance(data, list) or not data:
            errors.append("runtime_plan_not_list_or_empty")
        else:
            for i, e in enumerate(data[:200]):
                if not isinstance(e, dict):
                    errors.append(f"entry_{i}_not_object")
                    continue
                if not e.get("objective"):
                    errors.append(f"entry_{i}_missing_objective")
                if not e.get("target"):
                    errors.append(f"entry_{i}_missing_target")
                    continue
                target = str(e.get('target') or '').strip()
                host = str(urlparse(target).hostname or '').strip().lower() if target.startswith(('http://', 'https://')) else ''
                if not host:
                    errors.append(f"entry_{i}_invalid_target_host")
                    continue
                host_allowed = host in authoritative_domain_hosts or host in exact_targets_by_host
                if not host_allowed and authoritative_domains:
                    host_allowed = any(host == d[2:] or host.endswith('.' + d[2:]) for d in authoritative_domains if d.startswith('*.')) or host in authoritative_domains
                if not host_allowed:
                    errors.append(f"entry_{i}_target_host_not_authoritative")
                    continue
                exact_targets = exact_targets_by_host.get(host) or set()
                if exact_targets and host not in authoritative_domain_hosts:
                    norm_target = _normalize_target_url(target)
                    if not norm_target or norm_target not in exact_targets:
                        errors.append(f"entry_{i}_target_broadens_exact_scope")
        return jsonify({"ok": len(errors) == 0, "errors": errors[:20], "source": source})

    @app.route("/api/planner/runtime-plan-view")
    def api_planner_runtime_plan_view():
        if not RUNTIME_PLAN_PATH.exists():
            return jsonify({"ok": False, "error": "runtime_plan_missing"}), 404
        _runtime, _filtered_snapshot, _snap_campaign, snap_plan, _snapshot_matches_selected = _runtime_snapshot_sections()
        meta = load_runtime_plan_meta()
        merged_meta = dict(meta if isinstance(meta, dict) else {})
        if snap_plan:
            for key, value in snap_plan.items():
                if value not in (None, '', [], {}):
                    merged_meta[key] = value
        merged_meta['source'] = 'snapshot' if snap_plan else 'normalized_runtime_plan_meta'
        return jsonify({"ok": True, "content": RUNTIME_PLAN_PATH.read_text(encoding="utf-8", errors="ignore"), "meta": merged_meta})

    @app.route("/api/campaign/activate-from-blueprint", methods=["POST"])
    def api_campaign_activate_from_blueprint():
        data = request.get_json(silent=True) or {}
        key = str(data.get("campaign_key") or selected_campaign_key()).strip()
        if not key:
            return jsonify({"ok": False, "error": "missing_campaign_key"}), 400
        STATE["selected_campaign_key"] = key
        STATE["state"] = "idle"
        res = activate_campaign_key(key)
        return jsonify({"ok": bool(res.get("ok")), "selected_campaign_key": key})

    @app.route("/api/planner-info")
    def api_planner_info():
        ui = load_planner_ui_state()
        _runtime, filtered_snapshot, snap_campaign, snap_plan, snapshot_matches_selected = _runtime_snapshot_sections()
        planner_scope_targets, prepared_attacks = _selected_campaign_plan_counts()
        bp = load_latest_blueprint()
        llm_conf = None
        llm_conflicts = []
        llm_amb = []
        status = "idle"
        bp_source = 'missing'
        if bp:
            status = "ok"
            try:
                bp_json = Path(str(bp.get("path") or "")) / "blueprint.json"
                if bp_json.exists():
                    data, bp_source = load_blueprint_json(Path(str(bp.get("path") or "")))
                    hints = data.get("planner_hints") if isinstance(data.get("planner_hints"), dict) else {}
                    llm_conf = hints.get("llm_confidence")
                    if llm_conf is None and isinstance(data.get("aggression_profile"), dict):
                        llm_conf = data.get("aggression_profile", {}).get("confidence")
                    llm_conflicts = [str(x) for x in (hints.get("interpretation_conflicts") or [])][:8]
                    llm_amb = [str(x) for x in (hints.get("ambiguities") or [])][:8]
            except Exception:
                bp_source = 'invalid_json_file'
        return jsonify({
            "scope_txt": str(ui.get("scope_txt") or "scope/scope.txt"),
            "llm_interpret": bool(ui.get('llm_interpret', False)),
            "status": status,
            "llm_confidence": llm_conf,
            "llm_conflicts": llm_conflicts,
            "llm_ambiguities": llm_amb,
            "runtime_snapshot_source": projection_source_label(snapshot=(filtered_snapshot if snapshot_matches_selected else {}), fallback='legacy'),
            "plan_revision": snap_plan.get('plan_revision') or 0,
            "prepared_attacks": prepared_attacks,
            "planner_scope_targets": planner_scope_targets,
            "campaign_started_at": snap_campaign.get('started_at') or '',
            "blueprint_source": bp_source,
        })

    @app.route("/api/planner/campaigns")
    def api_planner_campaigns():
        return jsonify({"ok": True, "items": _list_campaign_registry_items(), "selected_campaign_key": selected_campaign_key()})

    @app.route("/api/planner/selection", methods=["GET", "POST"])
    def api_planner_selection():
        if request.method == "GET":
            ui = load_planner_ui_state()
            return jsonify({"ok": True, "selected_campaign_key": selected_campaign_key(), "scope_txt": str((ui or {}).get("scope_txt") or "scope/scope.txt"), "llm_interpret": bool((ui or {}).get('llm_interpret', False))})
        data = request.get_json(silent=True) or {}
        key = str(data.get("selected_campaign_key") or data.get("campaign_key") or "").strip()
        ui = load_planner_ui_state()
        if isinstance(ui, dict):
            ui["selected_campaign_key"] = key
            if "scope_txt" in data or str(data.get("scope_txt") or "").strip():
                ui["scope_txt"] = _normalize_scope_txt_for_ui(data.get("scope_txt"))
            if 'llm_interpret' in data:
                ui['llm_interpret'] = bool(data.get('llm_interpret'))
            save_planner_ui_state(ui)
        STATE["selected_campaign_key"] = key
        return jsonify({"ok": True, "selected_campaign_key": key, "scope_txt": str((ui or {}).get("scope_txt") or "scope/scope.txt"), "llm_interpret": bool((ui or {}).get('llm_interpret', False))})
