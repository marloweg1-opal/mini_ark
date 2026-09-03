"""
Mini ARK apply — the ONLY module allowed to actually touch a file's
real location. Everything upstream (organizer.py) proposes; this
module is where a proposal, once approved, becomes real filesystem
change.

Per Amendment 1, every item here walks:
    Preview -> Transaction -> Journal -> Verification -> Undo window

Two possible outcomes per file, decided PER ITEM, not per proposal:
  - 'shortcut': original file never moves. A Windows directory
    junction/symlink is created at dest_path pointing at the real file.
    Fully non-destructive; undo just removes the shortcut.
  - 'move': the file is physically relocated. canonical_path in the
    files table is updated to match. This is the destructive path and
    is the one this module is most defensive about.

Safety order, enforced before ANY disk write, in this sequence:
  1. Protected path check (hard floor, not just DB-editable)
  2. Dependent check (if 'move' requested and something depends on the
     current location, auto-downgrade to 'shortcut' + emit a
     code_change_needed proposal instead of silently breaking a
     Rainmeter skin, CareBloomOS reference, etc.)
  3. Circuit breaker (batch magnitude, independent of tier)
  4. Kill switch (checked again at the actual transaction boundary,
     inside journal.begin_transaction -- this module does not bypass it)
"""

import os
import platform
import shutil
from pathlib import Path

from core import journal
from core import quarantine
from core.circuit_breaker import check_operation_magnitude, OperationTooLarge

# Non-negotiable floor. Editable rows in protected_paths can ADD to
# this set; nothing can remove from it, because it isn't read from
# the database at all.
_HARDCODED_PROTECTED_PREFIXES = [
    r"C:\Windows",
    r"C:\Program Files\WindowsApps",
    r"C:\Program Files\Common Files",
    r"C:\ProgramData\Microsoft",
    r"C:\$Recycle.Bin",
    r"C:\System Volume Information",
]


class ProposalNotApproved(Exception):
    pass


# ---------------------------------------------------------------------
# Dependent tracking
# ---------------------------------------------------------------------

def register_dependent(conn, canonical_path: str, program_name: str,
                        reference_location: str = None,
                        reference_context: str = None) -> int:
    """
    Manually declare that some program depends on a path -- e.g.
    "Rainmeter reads M:\\Assets\\clock.png from skin.ini line 14".
    This is the ground truth apply() checks; an unregistered dependent
    is invisible to Mini ARK on purpose (no silent trust, no guessing).
    """
    cur = conn.execute(
        """INSERT INTO file_dependents
           (canonical_path, program_name, reference_location, reference_context)
           VALUES (?, ?, ?, ?);""",
        (canonical_path, program_name, reference_location, reference_context),
    )
    conn.commit()
    return cur.lastrowid


def scan_config_for_dependents(conn, config_path: str, program_name: str,
                                 candidate_paths: list) -> dict:
    """
    Plain-text scan of a config file (Rainmeter .ini, or any text-based
    config CareBloomOS/Welfare Witchcraft use) for literal references
    to any path in candidate_paths. Registers a dependent row for each
    hit found. This is intentionally simple (substring match per line)
    rather than format-aware -- extend per-program if a config format
    needs smarter parsing later.
    """
    config_file = Path(config_path)
    if not config_file.exists():
        return {"status": "failed", "reason": "config_not_found"}

    found = []
    with open(config_file, "r", encoding="utf-8", errors="ignore") as f:
        for line_no, line in enumerate(f, start=1):
            for candidate in candidate_paths:
                if candidate.lower() in line.lower():
                    register_dependent(
                        conn, candidate, program_name,
                        reference_location=f"{config_path}:{line_no}",
                        reference_context=line.strip(),
                    )
                    found.append({"path": candidate, "line": line_no, "context": line.strip()})

    return {"status": "scanned", "config": config_path, "dependents_found": found}


def get_active_dependents(conn, canonical_path: str) -> list:
    rows = conn.execute(
        "SELECT * FROM file_dependents WHERE canonical_path = ? AND status = 'active';",
        (canonical_path,),
    ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------
# Protection
# ---------------------------------------------------------------------

def is_protected(conn, path: str) -> str:
    """Returns a reason string if protected, None if not. Checks the
    hardcoded floor FIRST, then extends with any DB rows. Prefix-based,
    so anything nested under a reserved folder inherits the same
    protection automatically -- no separate ancestor bookkeeping needed."""
    norm = str(Path(path))
    for prefix in _HARDCODED_PROTECTED_PREFIXES:
        if norm.lower().startswith(prefix.lower()):
            return f"Hardcoded system-critical path: {prefix}"

    rows = conn.execute("SELECT path_prefix, reason FROM protected_paths;").fetchall()
    for row in rows:
        if norm.lower().startswith(row["path_prefix"].lower()):
            return row["reason"] or f"Protected path: {row['path_prefix']}"

    return None


def add_reservation(conn, path: str, reason: str = None) -> int:
    """
    Marks a folder (and everything under it) off-limits to Mini ARK --
    find-empty will never flag it or anything above it as a dead end,
    and apply() will never move/shortcut/quarantine it. For scaffolding
    you've deliberately built ahead of populating it.
    """
    norm = str(Path(path))
    cur = conn.execute(
        """INSERT INTO protected_paths (path_prefix, reason, category)
           VALUES (?, ?, 'user_reserved')
           ON CONFLICT(path_prefix) DO UPDATE SET reason=excluded.reason;""",
        (norm, reason or "Reserved by user"),
    )
    conn.commit()
    return cur.lastrowid


def remove_reservation(conn, path: str) -> dict:
    """Un-reserves a path. Only affects DB-backed reservations -- the
    hardcoded system floor cannot be removed this way, by design."""
    norm = str(Path(path))
    for prefix in _HARDCODED_PROTECTED_PREFIXES:
        if norm.lower() == prefix.lower():
            return {"status": "failed", "reason": "cannot unreserve a hardcoded system-floor path"}
    cur = conn.execute("DELETE FROM protected_paths WHERE path_prefix = ?;", (norm,))
    conn.commit()
    return {"status": "removed" if cur.rowcount else "not_found"}


def list_reservations(conn) -> list:
    rows = conn.execute(
        "SELECT path_prefix, reason, category FROM protected_paths ORDER BY category, path_prefix;"
    ).fetchall()
    hardcoded = [{"path_prefix": p, "reason": "Hardcoded system floor", "category": "system_floor"}
                 for p in _HARDCODED_PROTECTED_PREFIXES]
    return hardcoded + [dict(r) for r in rows]


def skip_item(conn, item_id: int, reason: str = "user declined") -> dict:
    """Marks a single proposal_item as skipped so plan_apply/execute_apply
    never act on it, without affecting sibling items in the same proposal.
    This is the itemized 'choose which ones' mechanism -- review with
    list_proposal_items, skip what you don't want, apply the rest."""
    row = conn.execute("SELECT id FROM proposal_items WHERE id = ?;", (item_id,)).fetchone()
    if row is None:
        return {"status": "failed", "reason": "not_found"}
    conn.execute(
        "UPDATE proposal_items SET status='skipped', block_reason=? WHERE id=?;",
        (reason, item_id),
    )
    conn.commit()
    return {"status": "skipped", "item_id": item_id}


def list_proposal_items(conn, proposal_id: int) -> list:
    rows = conn.execute(
        "SELECT id, canonical_path, dest_path, requested_mode, status, block_reason "
        "FROM proposal_items WHERE proposal_id = ? ORDER BY id;",
        (proposal_id,),
    ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------
# Resolve a proposal into concrete per-file rows
# ---------------------------------------------------------------------

def add_proposal_item(conn, proposal_id: int, canonical_path: str,
                       dest_path: str = None, requested_mode: str = "shortcut") -> int:
    if requested_mode not in ("move", "shortcut", "quarantine"):
        raise ValueError("requested_mode must be 'move', 'shortcut', or 'quarantine'")
    if requested_mode != "quarantine" and dest_path is None:
        raise ValueError("dest_path is required for 'move' and 'shortcut' modes")
    cur = conn.execute(
        """INSERT INTO proposal_items
           (proposal_id, canonical_path, dest_path, requested_mode)
           VALUES (?, ?, ?, ?);""",
        (proposal_id, canonical_path, dest_path, requested_mode),
    )
    conn.commit()
    return cur.lastrowid


# ---------------------------------------------------------------------
# PREVIEW: build the plan, decide real mode per item, no disk writes
# ---------------------------------------------------------------------

def plan_apply(conn, proposal_id: int) -> dict:
    """
    Step 1 of the ritual. Walks every pending proposal_item under this
    proposal, resolves protected/dependent status, and decides the
    ACTUAL mode per item. Writes nothing to disk. Writes a
    code_change_needed proposal for any item downgraded due to
    dependents, so the report exists whether or not the human proceeds.
    """
    proposal = conn.execute("SELECT * FROM proposals WHERE id = ?;", (proposal_id,)).fetchone()
    if proposal is None:
        return {"status": "failed", "reason": "proposal_not_found"}
    if proposal["status"] != "approved":
        raise ProposalNotApproved(
            f"Proposal {proposal_id} has status '{proposal['status']}', not 'approved'. "
            f"Approve it explicitly before planning apply."
        )

    items = conn.execute(
        "SELECT * FROM proposal_items WHERE proposal_id = ? AND status = 'pending';",
        (proposal_id,),
    ).fetchall()

    plan = []
    downgrade_report_lines = []

    for item in items:
        reason = is_protected(conn, item["canonical_path"])
        if reason:
            plan.append({"item_id": item["id"], "path": item["canonical_path"],
                         "action": "blocked", "reason": reason})
            continue

        actual_mode = item["requested_mode"]

        if actual_mode == "move":
            dependents = get_active_dependents(conn, item["canonical_path"])
            if dependents:
                actual_mode = "shortcut"
                lines = [f"  - {d['program_name']} references this at "
                         f"{d['reference_location']}: \"{d['reference_context']}\""
                         for d in dependents]
                downgrade_report_lines.append(
                    f"{item['canonical_path']} -> {item['dest_path']}:\n" + "\n".join(lines)
                )

        elif actual_mode == "quarantine":
            dependents = get_active_dependents(conn, item["canonical_path"])
            if dependents:
                # No sensible fallback for a delete -- unlike 'move' this
                # can't downgrade to something safer, so it's a hard block.
                lines = [f"{d['program_name']} references this at {d['reference_location']}"
                         for d in dependents]
                plan.append({"item_id": item["id"], "path": item["canonical_path"],
                             "action": "blocked",
                             "reason": "Has active dependent(s), cannot quarantine: " + "; ".join(lines)})
                continue

        plan.append({"item_id": item["id"], "path": item["canonical_path"],
                     "dest": item["dest_path"], "action": actual_mode})

    if downgrade_report_lines:
        report_body = (
            "The following files were requested as real MOVES but have known "
            "dependents, so they were auto-downgraded to shortcuts instead. "
            "To actually relocate them, update the referencing config(s) first, "
            "then re-request the move:\n\n" + "\n\n".join(downgrade_report_lines)
        )
        conn.execute(
            """INSERT INTO proposals (description, project_id, severity, status)
               VALUES (?, ?, 'decision', 'pending');""",
            (report_body, proposal["project_id"]),
        )
        conn.commit()

    blocked = [p for p in plan if p["action"] == "blocked"]
    movable = [p for p in plan if p["action"] in ("move", "shortcut", "quarantine")]

    return {
        "status": "planned",
        "proposal_id": proposal_id,
        "total_items": len(plan),
        "blocked_count": len(blocked),
        "blocked": blocked,
        "to_apply": movable,
        "downgraded_count": len(downgrade_report_lines),
        "note": "PREVIEW ONLY. Nothing on disk has changed. Call execute_apply(plan) to proceed.",
    }


# ---------------------------------------------------------------------
# EXECUTE: the real filesystem mutation, one item at a time, journaled
# ---------------------------------------------------------------------

def _create_shortcut(source: Path, dest: Path):
    """Windows directory junction / symlink. Original file untouched."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if platform.system() == "Windows":
        if source.is_dir():
            os.system(f'mklink /J "{dest}" "{source}"')
        else:
            os.system(f'mklink "{dest}" "{source}"')
    else:
        os.symlink(source, dest)


def _remove_shortcut(dest: Path):
    """Undo helper for a shortcut. Windows junctions report is_dir()=True
    but are not real directories -- rmdir on a junction removes just the
    link, never touching the real target's contents. Plain symlinks
    (non-Windows, or file-level Windows symlinks) use unlink instead."""
    if dest.is_symlink():
        dest.unlink()
    elif dest.is_dir():
        os.rmdir(dest)


def execute_apply(conn, plan: dict, tier: int = 3, verbose: bool = True) -> dict:
    """
    Step 2-4 of the ritual, run per item: Transaction -> real filesystem
    action -> Verification. Circuit breaker checked ONCE against the
    whole batch before any item executes. Kill switch checked again
    inside journal.begin_transaction per item (not bypassable).
    """
    to_apply = plan.get("to_apply", [])
    if not to_apply:
        return {"status": "no_items", "message": "Nothing in this plan is eligible to apply."}

    total_scope = conn.execute("SELECT COUNT(*) as c FROM files WHERE status='present';").fetchone()["c"]
    try:
        check_operation_magnitude(len(to_apply), total_items_in_scope=total_scope,
                                    operation_label="apply")
    except OperationTooLarge as e:
        return {"status": "blocked_by_circuit_breaker", "reason": str(e)}

    applied, failed = [], []

    for entry in to_apply:
        item = conn.execute("SELECT * FROM proposal_items WHERE id = ?;", (entry["item_id"],)).fetchone()
        source = Path(item["canonical_path"])
        dest = Path(item["dest_path"]) if item["dest_path"] else None
        action = entry["action"]

        preview = journal.preview_operation(
            conn, action_type=f"file_{action}", tier=tier, target_path=str(source),
            planned_changes={"dest": str(dest) if dest else "(quarantine -- destination assigned at apply time)"},
        )

        try:
            op_id = journal.begin_transaction(
                conn, preview, previous_state={"path": str(source), "existed": source.exists()},
            )
        except journal.ExecutionDisabled as e:
            return {"status": "blocked_by_kill_switch", "reason": str(e),
                    "applied_before_block": applied, "failed": failed}

        try:
            if action == "shortcut":
                _create_shortcut(source, dest)
                verified = dest.exists() and source.exists()
            elif action == "move":
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source), str(dest))
                conn.execute("UPDATE files SET canonical_path = ? WHERE canonical_path = ?;",
                             (str(dest), str(source)))
                verified = dest.exists() and not source.exists()
            else:  # quarantine
                q_result = quarantine.quarantine_item(conn, str(source), op_id)
                if q_result["status"] != "quarantined":
                    raise RuntimeError(q_result.get("reason", "quarantine failed"))
                dest = Path(q_result["quarantined_path"])
                conn.execute(
                    "UPDATE proposal_items SET dest_path = ? WHERE id = ?;",
                    (str(dest), item["id"]),
                )
                verified = dest.exists() and not source.exists()

            journal.complete_operation(conn, op_id, new_state={"path": str(dest)}, verified=verified)
            conn.execute(
                "UPDATE proposal_items SET status='applied', resolved_mode=?, action_log_id=?, resolved_at=datetime('now') WHERE id=?;",
                (action, op_id, item["id"]),
            )
            conn.commit()
            applied.append({"path": str(source), "dest": str(dest), "action": action, "op_id": op_id})
            if verbose:
                print(f"[APPLIED] {action}: {source} -> {dest}")

        except Exception as e:
            conn.execute(
                "UPDATE proposal_items SET status='skipped', block_reason=? WHERE id=?;",
                (f"{type(e).__name__}: {e}", item["id"]),
            )
            conn.commit()
            failed.append({"path": str(source), "reason": str(e)})
            if verbose:
                print(f"[FAILED] {action}: {source} -- {e}")

    return {
        "status": "complete",
        "applied_count": len(applied),
        "failed_count": len(failed),
        "applied": applied,
        "failed": failed,
    }


# ---------------------------------------------------------------------
# UNDO: Step 5 of the ritual, for actions this module performed
# ---------------------------------------------------------------------

def undo_apply(conn, op_id: int) -> dict:
    """
    Reverses a single apply action_log row by consulting how it was
    RECORDED, not by re-inspecting the current filesystem -- the
    action_log row is the source of truth for what happened.
    """
    row = conn.execute("SELECT * FROM action_log WHERE id = ?;", (op_id,)).fetchone()
    if row is None:
        return {"status": "failed", "reason": "not_found"}

    action = row["action_type"]  # 'file_move' or 'file_shortcut'

    def _reverse(previous_state: dict):
        import json as _json
        new_state = _json.loads(row["new_state"])
        original_path = Path(previous_state["path"])
        current_path = Path(new_state["path"])

        if action == "file_shortcut":
            _remove_shortcut(current_path)
        elif action == "file_move":
            if not current_path.exists():
                raise FileNotFoundError(f"Cannot undo move: {current_path} no longer exists.")
            original_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(current_path), str(original_path))
            conn.execute("UPDATE files SET canonical_path = ? WHERE canonical_path = ?;",
                         (str(original_path), str(current_path)))
            conn.commit()
        elif action == "file_quarantine":
            result = quarantine.restore_from_quarantine(str(current_path))
            if result["status"] != "restored":
                raise RuntimeError(f"Cannot undo quarantine: {result.get('reason', 'unknown error')}")

    return journal.undo_operation(conn, op_id, _reverse)
