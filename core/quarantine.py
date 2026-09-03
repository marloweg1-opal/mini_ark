"""
Mini ARK quarantine.

Constitutional constraint: Mini ARK never performs a true, irreversible
delete as its first action. A JSON snapshot in the action_log can
describe that a file existed -- it cannot resurrect the file's actual
bytes. So "delete" is never a real filesystem delete; it is always a
MOVE to a quarantine holding area, which is what makes restore
physically possible rather than a database claim about the past.

True permanent removal only happens as a SEPARATE, later, explicitly
confirmed purge of items that have sat in quarantine past a grace
period. Nothing in this module performs that purge automatically.
"""

import json
import shutil
import time
from pathlib import Path

QUARANTINE_ROOT_NAME = "_ark_quarantine"
DEFAULT_GRACE_PERIOD_DAYS = 14


def get_quarantine_root(anchor_path: Path) -> Path:
    """
    Quarantine lives as a sibling to whatever drive/root is being
    operated on, not buried in Mini ARK's own install directory --
    if C: is being organized, quarantined items should stay on C:,
    not silently migrate to wherever Mini ARK happens to be installed.
    """
    drive_root = Path(anchor_path).anchor or Path(anchor_path).parts[0]
    q = Path(drive_root) / QUARANTINE_ROOT_NAME
    q.mkdir(exist_ok=True)
    return q


def quarantine_item(conn, source_path: str, action_log_id: int) -> dict:
    """
    Moves (never copies-then-deletes-original in a way that could lose
    data mid-operation -- shutil.move is atomic where the OS supports
    it) an item into quarantine. Records a manifest entry so a human
    (or Mini ARK later) can identify what came from where.

    Returns the quarantine destination and manifest info. Does NOT
    delete anything permanently. Ever. That is a separate function
    that does not exist yet in this build on purpose.
    """
    src = Path(source_path)
    if not src.exists():
        return {"status": "failed", "reason": "source_not_found"}

    q_root = get_quarantine_root(src)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    dest_name = f"{timestamp}_{src.name}"
    dest = q_root / dest_name

    manifest_entry = {
        "original_path": str(src),
        "quarantined_path": str(dest),
        "quarantined_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "action_log_id": action_log_id,
        "grace_period_expires": time.strftime(
            "%Y-%m-%dT%H:%M:%S",
            time.localtime(time.time() + DEFAULT_GRACE_PERIOD_DAYS * 86400),
        ),
    }

    shutil.move(str(src), str(dest))

    manifest_path = q_root / "_manifest.jsonl"
    with open(manifest_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(manifest_entry) + "\n")

    print(f"[SUCCESS] Quarantined (not deleted): {src}")
    print(f"  Now at: {dest}")
    print(f"  Grace period expires: {manifest_entry['grace_period_expires']}")
    print(f"  Restore anytime before then -- nothing has been permanently removed.")

    return {"status": "quarantined", **manifest_entry}


def restore_from_quarantine(quarantined_path: str) -> dict:
    """Reads the manifest, moves the item back to its original location."""
    q_path = Path(quarantined_path)
    q_root = q_path.parent
    manifest_path = q_root / "_manifest.jsonl"

    if not manifest_path.exists():
        return {"status": "failed", "reason": "no_manifest_found"}

    entry = None
    with open(manifest_path, encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            if record["quarantined_path"] == str(q_path):
                entry = record
                break

    if entry is None:
        return {"status": "failed", "reason": "not_in_manifest"}

    original = Path(entry["original_path"])
    if original.exists():
        return {"status": "failed", "reason": "original_location_occupied"}

    shutil.move(str(q_path), str(original))
    print(f"[SUCCESS] Restored: {original}")
    return {"status": "restored", "path": str(original)}


def list_quarantine(anchor_path: str) -> list:
    """Read-only listing of what's currently quarantined, for human review."""
    q_root = get_quarantine_root(Path(anchor_path))
    manifest_path = q_root / "_manifest.jsonl"
    if not manifest_path.exists():
        return []
    entries = []
    with open(manifest_path, encoding="utf-8") as f:
        for line in f:
            entries.append(json.loads(line))
    return entries
