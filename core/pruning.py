"""
Mini ARK pruning -- finds folders that "lead to nothing" (contain no
files anywhere in their subtree) and proposes them for quarantine.

Constitutional constraint, same as organizer.py: this module NEVER
deletes or moves anything itself. It only writes proposals + per-file
proposal_items with requested_mode='quarantine'. A human reviews the
itemized list (list-items), skips whatever they want kept
(skip-item), approves, and only then does apply() touch the disk --
and even then, quarantine is a move to a holding area, never a true
delete (see core/quarantine.py).

Reserved folders (registered via apply.add_reservation) are treated
as occupied, never as candidates -- and because protection is
prefix-based, nothing above a reserved folder in the tree gets
flagged as empty either, since it isn't literally empty (it contains
the reserved scaffold).
"""

import os
from pathlib import Path

from core.apply import is_protected


def find_empty_branches(conn, root_path: str) -> list:
    """
    Live filesystem walk (read-only) finding the TOPMOST directory of
    each empty branch -- if a whole nested chain of folders is empty,
    this reports the highest one, not every folder within it.

    A directory counts as empty only if it has zero files AND every
    subdirectory beneath it is also empty (or doesn't exist). A
    reserved/protected directory is always treated as occupied, which
    correctly protects everything above it too.
    """
    root_path = str(Path(root_path))
    memo = {}  # dirpath -> bool (True = empty branch)

    for dirpath, dirnames, filenames in os.walk(root_path, topdown=False):
        if is_protected(conn, dirpath):
            memo[dirpath] = False
            continue
        if filenames:
            memo[dirpath] = False
            continue
        all_subs_empty = all(memo.get(os.path.join(dirpath, d), False) for d in dirnames) if dirnames else True
        memo[dirpath] = all_subs_empty

    candidates = []
    for dirpath, empty in memo.items():
        if not empty or dirpath == root_path:
            continue
        parent = os.path.dirname(dirpath)
        parent_already_reported = memo.get(parent, False) and parent != root_path
        if parent_already_reported:
            continue  # this dir will be covered by its (also-empty) parent instead

        subfolder_count = sum(1 for p in memo if p != dirpath and p.startswith(dirpath + os.sep))
        candidates.append({"path": dirpath, "nested_empty_subfolders": subfolder_count})

    candidates.sort(key=lambda c: c["path"])
    return candidates


def propose_prune(conn, root_path: str, project_id: int = None) -> dict:
    """
    Read-only analysis + PROPOSAL only. Writes one 'decision'-severity
    proposal plus one proposal_item per dead-end folder found, each
    defaulted to requested_mode='quarantine'. Nothing is deleted here
    or anywhere upstream of an explicit approve + apply.
    """
    candidates = find_empty_branches(conn, root_path)

    if not candidates:
        return {"status": "no_data", "message": "No empty folder branches found under this root."}

    description = (
        f"Found {len(candidates)} folder(s) that lead to nothing (no files "
        f"anywhere in their subtree). Review each with 'ark list-items', "
        f"skip anything you want kept with 'ark skip-item <item_id>', then "
        f"approve + apply. Quarantine is reversible within the grace period "
        f"-- nothing is permanently deleted by this."
    )
    cur = conn.execute(
        """INSERT INTO proposals (description, project_id, severity, batch_key, status)
           VALUES (?, ?, 'decision', ?, 'pending');""",
        (description, project_id, f"prune:{root_path}"),
    )
    proposal_id = cur.lastrowid

    for c in candidates:
        conn.execute(
            """INSERT INTO proposal_items
               (proposal_id, canonical_path, dest_path, requested_mode)
               VALUES (?, ?, NULL, 'quarantine');""",
            (proposal_id, c["path"]),
        )
    conn.commit()

    return {
        "status": "proposed",
        "proposal_id": proposal_id,
        "empty_folders_found": len(candidates),
        "candidates": candidates,
        "note": "NOTHING was deleted. Review with 'ark list-items " + str(proposal_id) + "'.",
    }
