"""
CareBloom consolidation MVP.

This module is deliberately copy-first. Runtime-dependent assets are not
removed from their original location during MVP execution. The sequence is:

1. Discover CareBloom-shaped files from known source roots.
2. Scan Rainmeter / Wallpaper text configs for literal source references.
3. Build a deterministic plan into docs.
4. Execute by copying files to a canonical staging root and verifying size.
5. For known dependent text configs, update references to the copied location.
6. Leave originals in place and record cleanup as future review, not action.
"""

import json
import hashlib
import os
import re
import shutil
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path


DEFAULT_SOURCE_ROOTS = [
    r"R:\Projects\CareBloomOS",
    r"R:\Projects\CareBloom",
    r"R:\RuneScript\_CareBloomArchive",
    r"C:\Users\Junior\Documents\Rainmeter\Skins\CareBloom",
    r"C:\Program Files (x86)\Steam\steamapps\common\wallpaper_engine\projects\myprojects",
]

DEFAULT_DEPENDENCY_ROOTS = [
    r"C:\Users\Junior\Documents\Rainmeter\Skins\CareBloom",
    r"C:\Users\Junior\AppData\Roaming\Rainmeter",
    r"C:\Program Files (x86)\Steam\steamapps\common\wallpaper_engine\projects\myprojects",
]

TEXT_EXTS = {
    ".ini", ".inc", ".lua", ".ps1", ".psm1", ".json", ".js", ".css",
    ".html", ".md", ".txt", ".csv", ".yaml", ".yml", ".xml",
}

ASSET_EXTS = {
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".ico",
    ".mp4", ".mov", ".mkv", ".webm", ".avi", ".mp3", ".wav", ".ogg",
    ".json", ".csv", ".ini", ".inc", ".lua", ".ps1", ".js", ".css", ".html", ".md", ".txt",
}

SKIP_DIR_NAMES = {
    "__pycache__", ".git", ".pytest_cache", "node_modules", "99_Consolidated_Assets",
}


@dataclass
class Asset:
    source_path: str
    destination_path: str
    size_bytes: int
    kind: str
    dependent_refs: int


@dataclass
class DependencyRef:
    asset_path: str
    config_path: str
    line_number: int
    line: str


def _now_stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H%M%S")


def _safe_part(value: str) -> str:
    value = value.strip().replace("\\", "_").replace("/", "_").replace(":", "")
    value = re.sub(r"[^A-Za-z0-9._ -]+", "_", value)
    value = re.sub(r"\s+", "_", value).strip("._- ")
    return value or "unnamed"


def _is_relative_to(path: Path, possible_parent: Path) -> bool:
    try:
        path.resolve().relative_to(possible_parent.resolve())
        return True
    except (ValueError, OSError):
        return False


def _iter_files(root: Path, excluded_roots: list[Path] | None = None):
    if not root.exists():
        return
    excluded_roots = excluded_roots or []
    for current, dirnames, filenames in os.walk(root):
        current_path = Path(current)
        if any(_is_relative_to(current_path, excluded) for excluded in excluded_roots):
            dirnames[:] = []
            continue
        dirnames[:] = [
            d for d in dirnames
            if d not in SKIP_DIR_NAMES
            and not any(_is_relative_to(current_path / d, excluded) for excluded in excluded_roots)
        ]
        for name in filenames:
            path = Path(current) / name
            try:
                if path.is_file():
                    yield path
            except OSError:
                continue


def _is_carebloom_path(path: Path) -> bool:
    text = str(path).lower()
    return any(token in text for token in (
        "carebloom", "carestone", "cloverstone", "moonstone", "heartstone",
        "musicstone", "wishstone", "cloudstone", "corerail", "carerail",
        "care rail", "care_rail", "carefield",
    ))


def _kind_for(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".ico"}:
        return "image"
    if ext in {".mp4", ".mov", ".mkv", ".webm", ".avi"}:
        return "video"
    if ext in {".mp3", ".wav", ".ogg"}:
        return "audio"
    if ext in {".ini", ".inc", ".lua", ".ps1", ".js", ".css", ".html"}:
        return "runtime_code"
    if ext in {".md", ".txt", ".csv", ".json", ".yaml", ".yml"}:
        return "project_text"
    return "other"


def _destination_for(source: Path, source_root: Path, canonical_root: Path) -> Path:
    root_label = _safe_part(str(source_root))
    digest = hashlib.sha1(str(source).lower().encode("utf-8")).hexdigest()[:12]
    safe_stem = _safe_part(source.stem)[:80]
    safe_name = f"{safe_stem}__{digest}{source.suffix.lower()}"
    return canonical_root / _kind_for(source) / root_label / safe_name


def discover_assets(source_roots: list[str], canonical_root: str, limit: int | None = None) -> list[Asset]:
    canonical = Path(canonical_root)
    assets: list[Asset] = []
    seen = set()
    for root_text in source_roots:
        root = Path(root_text)
        for path in _iter_files(root, excluded_roots=[canonical]):
            if limit is not None and len(assets) >= limit:
                return assets
            if path.suffix.lower() not in ASSET_EXTS:
                continue
            if not _is_carebloom_path(path):
                continue
            key = str(path).lower()
            if key in seen:
                continue
            seen.add(key)
            try:
                size = path.stat().st_size
            except OSError:
                continue
            assets.append(Asset(
                source_path=str(path),
                destination_path=str(_destination_for(path, root, canonical)),
                size_bytes=size,
                kind=_kind_for(path),
                dependent_refs=0,
            ))
    return assets


def scan_dependency_refs(assets: list[Asset], dependency_roots: list[str]) -> list[DependencyRef]:
    if not assets:
        return []
    path_needles = [
        (asset.source_path, asset.source_path.lower())
        for asset in sorted(assets, key=lambda item: len(item.source_path), reverse=True)
    ]
    refs: list[DependencyRef] = []
    for root_text in dependency_roots:
        root = Path(root_text)
        for config in _iter_files(root):
            if config.suffix.lower() not in TEXT_EXTS:
                continue
            try:
                lines = config.read_text(encoding="utf-8", errors="ignore").splitlines()
            except OSError:
                continue
            for line_number, line in enumerate(lines, start=1):
                lower = line.lower()
                for asset_path, needle in path_needles:
                    start = lower.find(needle)
                    if start < 0:
                        continue
                    next_char_index = start + len(needle)
                    if next_char_index < len(line) and line[next_char_index] in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-":
                        continue
                    refs.append(DependencyRef(asset_path, str(config), line_number, line.strip()))
    ref_counts = {}
    for ref in refs:
        ref_counts[ref.asset_path] = ref_counts.get(ref.asset_path, 0) + 1
    for asset in assets:
        asset.dependent_refs = ref_counts.get(asset.source_path, 0)
    return refs


def build_plan(source_roots: list[str], dependency_roots: list[str], canonical_root: str,
               docs_root: str, limit: int | None = None) -> dict:
    assets = discover_assets(source_roots, canonical_root, limit=limit)
    refs = scan_dependency_refs(assets, dependency_roots)
    stamp = _now_stamp()
    docs = Path(docs_root)
    docs.mkdir(parents=True, exist_ok=True)
    json_path = docs / f"CAREBLOOM_CONSOLIDATION_PLAN_{stamp}.json"
    md_path = docs / f"CAREBLOOM_CONSOLIDATION_PLAN_{stamp}.md"
    plan = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "mode": "plan",
        "canonical_root": canonical_root,
        "source_roots": source_roots,
        "dependency_roots": dependency_roots,
        "asset_count": len(assets),
        "dependent_asset_count": sum(1 for asset in assets if asset.dependent_refs),
        "dependency_reference_count": len(refs),
        "assets": [asdict(asset) for asset in assets],
        "dependency_refs": [asdict(ref) for ref in refs],
        "execution_policy": "copy_first_update_text_refs_leave_originals",
    }
    json_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    _write_markdown_plan(md_path, plan)
    plan["json_path"] = str(json_path)
    plan["markdown_path"] = str(md_path)
    return plan


def _write_markdown_plan(path: Path, plan: dict) -> None:
    lines = [
        "# CareBloom Consolidation Plan",
        "",
        f"- Created: {plan['created_at']}",
        f"- Canonical root: `{plan['canonical_root']}`",
        f"- Assets discovered: {plan['asset_count']}",
        f"- Assets with dependency refs: {plan['dependent_asset_count']}",
        f"- Dependency references: {plan['dependency_reference_count']}",
        "",
        "## Safety Policy",
        "",
        "- Copy first.",
        "- Verify copied size.",
        "- Update known text references only after copy verification.",
        "- Leave originals in place during MVP.",
        "- Do not stop Rainmeter or Wallpaper Engine.",
        "- Do not delete source assets.",
        "",
        "## Source Roots",
        "",
    ]
    for root in plan["source_roots"]:
        lines.append(f"- `{root}`")
    lines += ["", "## Dependency Roots", ""]
    for root in plan["dependency_roots"]:
        lines.append(f"- `{root}`")
    lines += ["", "## First Assets", ""]
    for asset in plan["assets"][:50]:
        lines.append(f"- `{asset['source_path']}` -> `{asset['destination_path']}` ({asset['kind']}, refs={asset['dependent_refs']})")
    if len(plan["assets"]) > 50:
        lines.append(f"- ... {len(plan['assets']) - 50} more in JSON plan")
    lines += ["", "## First Dependency References", ""]
    for ref in plan["dependency_refs"][:75]:
        destination = next(
            (asset["destination_path"] for asset in plan["assets"] if asset["source_path"] == ref["asset_path"]),
            "",
        )
        lines.append(f"- `{ref['config_path']}:{ref['line_number']}`")
        lines.append(f"  - Source: `{ref['asset_path']}`")
        lines.append(f"  - Destination: `{destination}`")
    if len(plan["dependency_refs"]) > 75:
        lines.append(f"- ... {len(plan['dependency_refs']) - 75} more in JSON plan")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def execute_plan(plan_path: str, update_refs: bool = False) -> dict:
    raise PermissionError(
        "STEWARDSHIP_REVIEW_REQUIRED: Legacy consolidation execution is held. "
        "Copy-first does not authorize destination replacement or reference edits. "
        "A journaled, identity-bound executor is required; no plan or source was read."
    )
    plan_file = Path(plan_path)
    plan = json.loads(plan_file.read_text(encoding="utf-8"))
    copied = []
    failed = []
    ref_updates = []
    asset_dest_by_source = {asset["source_path"]: asset["destination_path"] for asset in plan["assets"]}

    for asset in plan["assets"]:
        source = Path(asset["source_path"])
        dest = Path(asset["destination_path"])
        try:
            if not source.exists():
                raise FileNotFoundError(str(source))
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists() and dest.stat().st_size == source.stat().st_size:
                copied.append({"source": str(source), "dest": str(dest), "already_present": True})
                continue
            shutil.copy2(source, dest)
            if dest.stat().st_size != source.stat().st_size:
                raise RuntimeError("copy size verification failed")
            copied.append({"source": str(source), "dest": str(dest), "already_present": False})
        except Exception as exc:
            failed.append({"source": str(source), "dest": str(dest), "reason": f"{type(exc).__name__}: {exc}"})

    if update_refs and not failed:
        refs_by_config = {}
        for ref in plan["dependency_refs"]:
            refs_by_config.setdefault(ref["config_path"], []).append(ref)
        for config_path, refs in refs_by_config.items():
            config = Path(config_path)
            try:
                text = config.read_text(encoding="utf-8", errors="ignore")
                updated = text
                for ref in refs:
                    dest = asset_dest_by_source.get(ref["asset_path"])
                    if dest:
                        updated = updated.replace(ref["asset_path"], dest)
                if updated != text:
                    config.write_text(updated, encoding="utf-8")
                    ref_updates.append({"config": str(config), "refs_updated": len(refs)})
            except Exception as exc:
                failed.append({"source": str(config), "dest": str(config), "reason": f"reference update failed: {type(exc).__name__}: {exc}"})

    result_path = plan_file.with_name(plan_file.stem.replace("PLAN", "RESULT") + ".json")
    result = {
        "completed_at": datetime.now().isoformat(timespec="seconds"),
        "plan_path": str(plan_file),
        "update_refs": update_refs,
        "copied_count": len(copied),
        "failed_count": len(failed),
        "reference_update_count": len(ref_updates),
        "copied": copied[:200],
        "failed": failed,
        "reference_updates": ref_updates,
        "originals_left_in_place": True,
    }
    result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    result["result_path"] = str(result_path)
    return result


def _archive_bucket(asset: Asset, source_mtime: float, cutoff_ts: float) -> str:
    if asset.dependent_refs:
        return "02_DEPENDENCY_HOLD"
    if source_mtime <= cutoff_ts:
        return "90_ARCHIVE_PREP_DELETION_CANDIDATES_OLDER_THAN_60_DAYS"
    return "01_ACTIVE_RECENT_NONDEPENDENT"


def build_archive_map(source_roots: list[str], dependency_roots: list[str],
                      target_root: str, docs_root: str, older_than_days: int = 60,
                      limit: int | None = None) -> dict:
    target = Path(target_root)
    docs = Path(docs_root)
    docs.mkdir(parents=True, exist_ok=True)
    cutoff_ts = datetime.now().timestamp() - (older_than_days * 24 * 60 * 60)

    assets = discover_assets(source_roots, str(target), limit=limit)
    refs = scan_dependency_refs(assets, dependency_roots)
    ref_counts = {}
    for ref in refs:
        ref_counts[ref.asset_path] = ref_counts.get(ref.asset_path, 0) + 1

    mapped_assets = []
    for asset in assets:
        source = Path(asset.source_path)
        try:
            stat = source.stat()
            modified_ts = stat.st_mtime
            modified_at = datetime.fromtimestamp(modified_ts).isoformat(timespec="seconds")
        except OSError:
            modified_ts = 0
            modified_at = ""
        asset.dependent_refs = ref_counts.get(asset.source_path, 0)
        bucket = _archive_bucket(asset, modified_ts, cutoff_ts)
        digest = hashlib.sha1(asset.source_path.lower().encode("utf-8")).hexdigest()[:12]
        safe_name = f"{_safe_part(source.stem)[:80]}__{digest}{source.suffix.lower()}"
        destination = target / bucket / asset.kind / safe_name
        mapped_assets.append({
            "source_path": asset.source_path,
            "destination_path": str(destination),
            "size_bytes": asset.size_bytes,
            "kind": asset.kind,
            "dependent_refs": asset.dependent_refs,
            "modified_at": modified_at,
            "older_than_days": older_than_days,
            "bucket": bucket,
            "deletion_prep": bucket.startswith("90_ARCHIVE_PREP"),
        })

    stamp = _now_stamp()
    json_path = docs / f"CAREBLOOM_ARCHIVE_MAP_{stamp}.json"
    md_path = docs / f"CAREBLOOM_ARCHIVE_MAP_{stamp}.md"
    csv_path = docs / f"CAREBLOOM_ARCHIVE_MAP_{stamp}.csv"
    plan = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "target_root": target_root,
        "source_roots": source_roots,
        "dependency_roots": dependency_roots,
        "older_than_days": older_than_days,
        "asset_count": len(mapped_assets),
        "dependency_reference_count": len(refs),
        "dependent_hold_count": sum(1 for item in mapped_assets if item["dependent_refs"]),
        "deletion_prep_count": sum(1 for item in mapped_assets if item["deletion_prep"]),
        "active_recent_nondependent_count": sum(1 for item in mapped_assets if item["bucket"] == "01_ACTIVE_RECENT_NONDEPENDENT"),
        "assets": mapped_assets,
        "dependency_refs": [asdict(ref) for ref in refs],
        "execution_policy": "copy_first_archive_stage_no_deletes",
    }
    json_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    _write_archive_markdown(md_path, plan)
    _write_archive_csv(csv_path, mapped_assets)
    plan["json_path"] = str(json_path)
    plan["markdown_path"] = str(md_path)
    plan["csv_path"] = str(csv_path)
    return plan


def _write_archive_csv(path: Path, assets: list[dict]) -> None:
    import csv
    fields = [
        "bucket", "deletion_prep", "kind", "dependent_refs", "modified_at",
        "size_bytes", "source_path", "destination_path",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for item in assets:
            writer.writerow(item)


def _write_archive_markdown(path: Path, plan: dict) -> None:
    lines = [
        "# CareBloomOS Archive Map",
        "",
        f"- Created: {plan['created_at']}",
        f"- Target root: `{plan['target_root']}`",
        f"- Assets mapped: {plan['asset_count']}",
        f"- Dependency references: {plan['dependency_reference_count']}",
        f"- Dependency hold: {plan['dependent_hold_count']}",
        f"- Active recent non-dependent: {plan['active_recent_nondependent_count']}",
        f"- Deletion-prep candidates older than {plan['older_than_days']} days: {plan['deletion_prep_count']}",
        "",
        "## Safety Policy",
        "",
        "- Copy first.",
        "- Verify copied size.",
        "- Do not delete originals.",
        "- Do not move dependency-bearing assets.",
        "- Treat deletion-prep as a review queue, not deletion authorization.",
        "- Do not stop Rainmeter or Wallpaper Engine.",
        "",
        "## Target Structure",
        "",
        "- `00_MANIFESTS` - generated JSON/CSV/Markdown maps",
        "- `01_ACTIVE_RECENT_NONDEPENDENT` - non-dependent assets touched within the cutoff window",
        "- `02_DEPENDENCY_HOLD` - assets with detected Rainmeter/Wallpaper/text references",
        "- `90_ARCHIVE_PREP_DELETION_CANDIDATES_OLDER_THAN_60_DAYS` - non-dependent older assets staged for deletion review",
        "",
        "## First Deletion-Prep Candidates",
        "",
    ]
    candidates = [item for item in plan["assets"] if item["deletion_prep"]]
    for item in candidates[:100]:
        lines.append(f"- `{item['source_path']}`")
        lines.append(f"  - Destination: `{item['destination_path']}`")
        lines.append(f"  - Modified: {item['modified_at']}")
    if len(candidates) > 100:
        lines.append(f"- ... {len(candidates) - 100} more in JSON/CSV maps")
    lines += ["", "## Dependency Holds", ""]
    holds = [item for item in plan["assets"] if item["dependent_refs"]]
    for item in holds[:100]:
        lines.append(f"- `{item['source_path']}` ({item['dependent_refs']} refs)")
    if len(holds) > 100:
        lines.append(f"- ... {len(holds) - 100} more in JSON/CSV maps")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def execute_archive_map(plan_path: str) -> dict:
    raise PermissionError(
        "STEWARDSHIP_REVIEW_REQUIRED: Legacy archive staging is held pending "
        "journaled, no-replace execution and affirmative action evidence. "
        "No plan or source was read."
    )
    plan_file = Path(plan_path)
    plan = json.loads(plan_file.read_text(encoding="utf-8"))
    target = Path(plan["target_root"])
    manifests = target / "00_MANIFESTS"
    manifests.mkdir(parents=True, exist_ok=True)

    copied = []
    failed = []
    for item in plan["assets"]:
        source = Path(item["source_path"])
        dest = Path(item["destination_path"])
        try:
            if not source.exists():
                raise FileNotFoundError(str(source))
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists() and dest.stat().st_size == source.stat().st_size:
                copied.append({"source": str(source), "dest": str(dest), "already_present": True, "bucket": item["bucket"]})
                continue
            shutil.copy2(source, dest)
            if dest.stat().st_size != source.stat().st_size:
                raise RuntimeError("copy size verification failed")
            copied.append({"source": str(source), "dest": str(dest), "already_present": False, "bucket": item["bucket"]})
        except Exception as exc:
            failed.append({"source": str(source), "dest": str(dest), "bucket": item["bucket"], "reason": f"{type(exc).__name__}: {exc}"})

    stamp = _now_stamp()
    result_path = manifests / f"CAREBLOOM_ARCHIVE_STAGE_RESULT_{stamp}.json"
    manifest_json = manifests / Path(plan_file.name).name
    manifest_json.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    result = {
        "completed_at": datetime.now().isoformat(timespec="seconds"),
        "plan_path": str(plan_file),
        "target_root": plan["target_root"],
        "copied_count": len(copied),
        "failed_count": len(failed),
        "deletion_prep_count": plan["deletion_prep_count"],
        "dependent_hold_count": plan["dependent_hold_count"],
        "originals_left_in_place": True,
        "files_deleted": 0,
        "copied": copied[:200],
        "failed": failed,
    }
    result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    result["result_path"] = str(result_path)
    result["manifest_json"] = str(manifest_json)
    return result
