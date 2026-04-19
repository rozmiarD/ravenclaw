from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def ensure_registry(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    return root


def campaign_key(identity_hash: str) -> str:
    return str(identity_hash or '')[:16]


def campaign_dir(registry_root: Path, identity_hash: str) -> Path:
    return registry_root / campaign_key(identity_hash)


def _load_latest(path: Path) -> Dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def find_existing_plan(registry_root: Path, source_hash: str, planner_identity_hash: str | None = None) -> Dict[str, Any] | None:
    if planner_identity_hash:
        latest = _load_latest(campaign_dir(registry_root, planner_identity_hash) / 'latest.json')
        if latest:
            return latest
    legacy_latest = _load_latest(campaign_dir(registry_root, source_hash) / 'latest.json')
    if not legacy_latest:
        return None
    legacy_identity = str(legacy_latest.get('planner_identity_hash_sha256') or '').strip()
    if legacy_identity and planner_identity_hash and legacy_identity != planner_identity_hash:
        return None
    return legacy_latest


def next_version(cdir: Path) -> int:
    versions_dir = cdir / 'versions'
    if not versions_dir.exists():
        return 1
    existing = []
    for child in versions_dir.iterdir():
        if child.is_dir() and child.name.startswith('v'):
            try:
                existing.append(int(child.name[1:]))
            except ValueError:
                continue
    return (max(existing) + 1) if existing else 1


def store_plan(registry_root: Path, blueprint: Dict[str, Any], templates: Dict[str, str]) -> Dict[str, Any]:
    source_hash = blueprint['source_program_hash_sha256']
    planner_identity_hash = str(blueprint.get('planner_identity_hash_sha256') or source_hash)
    cdir = campaign_dir(ensure_registry(registry_root), planner_identity_hash)
    version = next_version(cdir)

    version_dir = cdir / 'versions' / f'v{version:04d}'
    templates_dir = version_dir / 'templates'
    version_dir.mkdir(parents=True, exist_ok=True)
    templates_dir.mkdir(parents=True, exist_ok=True)

    blueprint = dict(blueprint)
    blueprint['version'] = version
    template = str(blueprint.get('campaign_name_template') or 'CAMPAIGN-V{version}-AUTO')
    campaign_name = template.replace('{version}', str(version))
    blueprint['campaign_name'] = campaign_name

    (version_dir / 'blueprint.json').write_text(json.dumps(blueprint, ensure_ascii=False, indent=2), encoding='utf-8')

    import yaml  # type: ignore
    (version_dir / 'blueprint.yaml').write_text(yaml.safe_dump(blueprint, sort_keys=False, allow_unicode=True), encoding='utf-8')

    for name, body in templates.items():
        (templates_dir / name).write_text(body, encoding='utf-8')

    latest_meta = {
        'campaign_id': blueprint['campaign_id'],
        'campaign_name': blueprint.get('campaign_name'),
        'version': version,
        'source_program_hash_sha256': source_hash,
        'operator_flags_hash_sha256': blueprint.get('operator_flags_hash_sha256'),
        'planner_semantics_hash_sha256': blueprint.get('planner_semantics_hash_sha256'),
        'planner_identity_hash_sha256': blueprint.get('planner_identity_hash_sha256'),
        'planner_provenance_mode': blueprint.get('planner_provenance_mode'),
        'blueprint_hash_sha256': blueprint['blueprint_hash_sha256'],
        'operator_approval': blueprint['operator_approval'],
        'path': str(Path('versions') / f'v{version:04d}'),
    }
    (cdir / 'latest.json').write_text(json.dumps(latest_meta, ensure_ascii=False, indent=2), encoding='utf-8')
    return latest_meta
