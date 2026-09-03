#!/usr/bin/env python3
"""
Mini ARK CLI

Coherent command surface per spec Section 19. Internal modules may be
many; this file is the one place a human types commands.

Usage:
    python ark.py bootstrap
    python ark.py scan <path>
    python ark.py doctor
    python ark.py brief
"""

import argparse
import json
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent))
from db.database import get_connection, initialize_schema, migrate_schema, get_schema_version, record_source
from scanner.scanner import scan_path
from core.journal import check_kill_switch, ExecutionDisabled, undo_operation, KILL_SWITCH_FLAG
from core.graduation import check_phase2_scanner, print_graduation_report
from core.reports import generate_scan_report, write_report
from core.organizer import analyze_and_propose, analyze_media_and_propose
from core import apply as apply_mod
from core import pruning
from core import reconcile as reconcile_mod
from core import dedupe
from core import casefix
from core import classify
from core import conversation_ingest
from core import renaming
from core import carebloom_consolidation
from core import profile_migration

CONFIG_PATH = Path(__file__).parent / "config.json"
DEFAULT_CONFIG = {
    "db_path": str(Path(__file__).parent / "ark.sqlite"),
    "approved_scan_paths": [],
}


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, encoding="utf-8") as f:
            cfg = json.load(f)
    else:
        cfg = DEFAULT_CONFIG.copy()

    # A relative db_path (e.g. from an older config.json, or written by
    # an earlier version of this file) must resolve against ark.py's OWN
    # directory, never against whatever directory the user happens to be
    # standing in -- otherwise 'cd C:\' before running any command
    # silently breaks the ledger lookup with a confusing sqlite error
    # instead of just finding the ledger regardless of cwd.
    db_path = Path(cfg.get("db_path", DEFAULT_CONFIG["db_path"]))
    if not db_path.is_absolute():
        db_path = (CONFIG_PATH.parent / db_path).resolve()
    cfg["db_path"] = str(db_path)
    return cfg


def save_config(cfg: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def cmd_bootstrap(args):
    print("[STARTING] Mini ARK bootstrap")
    cfg = load_config()
    if not CONFIG_PATH.exists():
        save_config(cfg)
        print(f"[SUCCESS] Created config: {CONFIG_PATH}")
    else:
        print(f"[SUCCESS] Config already exists: {CONFIG_PATH}")

    conn = get_connection(cfg["db_path"])
    initialize_schema(conn)
    version = get_schema_version(conn)
    print(f"[SUCCESS] Ledger ready: {cfg['db_path']} (schema v{version})")
    conn.close()
    print("[SUCCESS] Bootstrap complete. Nothing was scanned or modified outside the ledger itself.")


def cmd_scan(args):
    cfg = load_config()
    conn = get_connection(cfg["db_path"])
    initialize_schema(conn)

    source_id = record_source(conn, kind="filesystem_scan", label=f"manual scan of {args.path}")
    result = scan_path(conn, args.path, source_id, resume=args.resume)
    conn.close()

    if result.get("status") != "complete":
        sys.exit(1)


def cmd_doctor(args):
    print("[STARTING] Mini ARK doctor")
    cfg = load_config()

    checks = []

    db_exists = Path(cfg["db_path"]).exists()
    checks.append(("Ledger file exists", db_exists))

    if db_exists:
        conn = get_connection(cfg["db_path"])

        migrated = migrate_schema(conn)
        if migrated:
            checks.append((f"Schema retrofitted -- added missing column(s): {', '.join(migrated)}", True))
        else:
            checks.append(("Schema columns up to date", True))

        version = get_schema_version(conn)
        checks.append((f"Schema version readable (v{version})", version > 0))

        scan_count = conn.execute("SELECT COUNT(*) as c FROM scans;").fetchone()["c"]
        checks.append((f"Scan history present ({scan_count} scans)", True))

        unique_ok = reconcile_mod.check_canonical_path_unique(conn)
        checks.append(("files.canonical_path UNIQUE constraint enforced on disk", unique_ok))

        flagged = conn.execute(
            "SELECT COUNT(*) as c FROM handoffs WHERE requires_review = 1;"
        ).fetchone()["c"]
        checks.append((f"Handoffs awaiting review: {flagged}", flagged == 0))

        open_loops = conn.execute(
            "SELECT COUNT(*) as c FROM open_loops WHERE status = 'open';"
        ).fetchone()["c"]
        checks.append((f"Open loops: {open_loops}", True))

        conn.close()

    all_ok = True
    for label, ok in checks:
        mark = "[OK]" if ok else "[WARNING]"
        if not ok:
            all_ok = False
        print(f"  {mark} {label}")

    if all_ok:
        print("[SUCCESS] Doctor: no issues found")
    else:
        print("[WARNING] Doctor: issues found above")


def cmd_inventory(args):
    cfg = load_config()
    conn = get_connection(cfg["db_path"])
    initialize_schema(conn)

    print(f"[STARTING] Classifying files"
          + (f" under {args.under}" if args.under else " (all)")
          + " -- read-only, no proposals or moves")
    result = classify.classify_all(conn, root_path=args.under)

    if result["total_files"] == 0:
        print("\nNo files found. Has this path been scanned yet?")
        conn.close()
        return

    print(f"\nTotal files classified: {result['total_files']}")

    by_confidence = {"Confirmed": 0, "Strongly_inferred": 0, "Tentative": 0, "Unknown": 0}
    for (bucket, confidence), data in result["buckets"].items():
        by_confidence[confidence] += data["count"]

    print(f"\nBy confidence:")
    for tier in ["Confirmed", "Strongly_inferred", "Tentative", "Unknown"]:
        pct = (by_confidence[tier] / result["total_files"] * 100) if result["total_files"] else 0
        print(f"  {tier:18s} {by_confidence[tier]:>8d}  ({pct:.1f}%)")

    print(f"\nBy proposed bucket:")
    for (bucket, confidence), data in sorted(result["buckets"].items(), key=lambda x: -x[1]["count"]):
        print(f"  [{confidence:18s}] {bucket:35s} {data['count']}")

    # Write the full report to a file too, since this is genuinely
    # meant to be reviewed, not just glanced at in a terminal.
    report_lines = [
        f"# Mini ARK Inventory Report",
        f"",
        f"Root: {args.under or '(all)'}",
        f"Total files classified: {result['total_files']}",
        f"",
        f"## By confidence",
        f"",
    ]
    for tier in ["Confirmed", "Strongly_inferred", "Tentative", "Unknown"]:
        pct = (by_confidence[tier] / result["total_files"] * 100) if result["total_files"] else 0
        report_lines.append(f"- **{tier}**: {by_confidence[tier]} ({pct:.1f}%)")

    report_lines.append(f"\n## By proposed bucket\n")
    for (bucket, confidence), data in sorted(result["buckets"].items(), key=lambda x: -x[1]["count"]):
        report_lines.append(f"### [{confidence}] {bucket} -- {data['count']} file(s)\n")
        for ex in data["examples"]:
            report_lines.append(f"- `{ex}`")
        report_lines.append("")

    report_path = Path(cfg["db_path"]).parent / "inventory_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print(f"\nFull report written to: {report_path}")

    conn.close()


def cmd_resolve_case_drift(args):
    cfg = load_config()
    conn = get_connection(cfg["db_path"])
    initialize_schema(conn)

    dry_run = not args.execute
    print(f"[STARTING] Resolving case-only path drift"
          + (f" under {args.under}" if args.under else " (all)")
          + (" -- DRY RUN, no changes will be made" if dry_run else " -- EXECUTING"))
    result = casefix.resolve_case_drift(conn, root_path=args.under, dry_run=dry_run)

    if result["status"] == "refused":
        print(f"\n[REFUSED] {result['reason']}")
        sys.exit(1)
    elif result["status"] == "no_data":
        print(f"\n{result['message']}")
    elif result["status"] == "blocked_by_kill_switch":
        print(f"\n[BLOCKED] {result['reason']}")
        sys.exit(1)
    elif result["status"] == "dry_run_complete":
        print(f"\nWould remove {result['would_delete_count']} stale 'missing' row(s):")
        for ex in result["examples"]:
            print(f"  {ex}")
        print(f"\nRe-run with --execute to actually clean these up.")
    else:
        print(f"\n[SUCCESS] Removed {result['deleted_count']} stale 'missing' row(s).")
        print(f"  OP-{result['op_id']:06d} -- undo-able with 'python ark.py undo {result['op_id']}'")

    conn.close()


def cmd_resolve_duplicates(args):
    cfg = load_config()
    conn = get_connection(cfg["db_path"])
    initialize_schema(conn)

    dry_run = not args.execute
    print(f"[STARTING] Resolving duplicate canonical_path rows"
          + (f" under {args.under}" if args.under else " (all)")
          + (" -- DRY RUN, no changes will be made" if dry_run else " -- EXECUTING"))
    result = dedupe.resolve_duplicate_rows(conn, root_path=args.under, dry_run=dry_run)

    if result["status"] == "blocked_by_kill_switch":
        print(f"[BLOCKED] {result['reason']}")
        sys.exit(1)
        return

    print(f"\nDuplicate groups found: {result['groups_found']}")
    print(f"  Safe to auto-resolve (identical hash+size): {result['resolved_count']}")
    print(f"  Conflicts (disagree on content -- needs manual review): {result['conflict_count']}")

    if result["conflicts"]:
        print(f"\nCONFLICTS -- not touched, review manually:")
        for c in result["conflicts"][:20]:
            print(f"  {c['path']}  (row ids: {c['row_ids']}) -- {c['reason']}")

    if dry_run and result["resolved"]:
        print(f"\nExamples of what --execute would do:")
        for r in result["resolved"][:10]:
            print(f"  {r['path']}  ({r['row_count']} rows -> 1, status would become {r['would_keep_status']})")
        print(f"\nRe-run with --execute to actually apply this.")
    elif result["resolved"]:
        print(f"\nResolved (see action_log for op_ids, undo-able individually):")
        for r in result["resolved"][:10]:
            print(f"  OP-{r['op_id']:06d}  {r['path']}  ({r['row_count']} rows -> 1, status={r['final_status']})")

    conn.close()


def cmd_propose_rename(args):
    cfg = load_config()
    conn = get_connection(cfg["db_path"])
    initialize_schema(conn)

    if args.list_file:
        with open(args.list_file, "r", encoding="utf-8") as f:
            file_paths = [line.strip() for line in f if line.strip()]
    else:
        file_paths = args.files

    if not file_paths:
        print("[FAILED] No files given -- pass paths directly or use --list-file")
        sys.exit(1)
        return

    result = renaming.propose_rename_sequence(
        conn, file_paths, args.template,
        start_index=args.start, pad_width=args.pad, dest_dir=args.dest_dir,
    )

    print(f"[SUCCESS] Rename plan built: {result['item_count']} file(s)")
    for item in result["plan"][:15]:
        print(f"  {item['source']}")
        print(f"    -> {item['dest']}")
    if result["item_count"] > 15:
        print(f"  ... and {result['item_count'] - 15} more")

    print(f"\nProposal #{result['proposal_id']} created.")
    print(f"  Review:  python ark.py list-items {result['proposal_id']}")
    print(f"  Then:    python ark.py approve {result['proposal_id']}")
    print(f"           python ark.py apply {result['proposal_id']} --preview")
    conn.close()


def cmd_status(args):
    cfg = load_config()
    if not Path(cfg["db_path"]).exists():
        print("[FAILED] No ledger found yet. Run 'ark bootstrap' first.")
        return
    conn = get_connection(cfg["db_path"])
    initialize_schema(conn)

    root = str(args.path)
    print(f"MINI ARK STATUS — {root}\n")

    scans = conn.execute(
        """SELECT id, root_path, started_at, completed_at, status,
                  files_scanned, files_added, files_changed, files_missing,
                  interrupted_at
           FROM scans WHERE root_path LIKE ? ORDER BY started_at DESC LIMIT 5;""",
        (root + "%",),
    ).fetchall()

    if not scans:
        print(f"No scans recorded under this path yet. Mini ARK knows nothing about it.")
        print(f"  Run: python ark.py scan \"{root}\"")
        conn.close()
        return

    print(f"Scan history ({len(scans)} shown, most recent first):")
    for s in scans:
        if s["status"] == "complete":
            print(f"  [{s['status']:11s}] {s['started_at']}  "
                  f"scanned={s['files_scanned']} added={s['files_added']} "
                  f"changed={s['files_changed']} missing={s['files_missing']}")
        elif s["status"] == "interrupted":
            print(f"  [{s['status']:11s}] {s['started_at']}  "
                  f"stopped at {s['files_scanned']} files -- resume with:")
            print(f"      python ark.py scan \"{s['root_path']}\" --resume")
        else:
            print(f"  [{s['status']:11s}] {s['started_at']}  files_scanned={s['files_scanned']}")

    latest = scans[0]
    file_counts = conn.execute(
        """SELECT status, COUNT(*) as c FROM files
           WHERE canonical_path LIKE ? GROUP BY status;""",
        (root + "%",),
    ).fetchall()
    print(f"\nFiles known under this path (as of the ledger's last scan):")
    if not file_counts:
        print("  none")
    for row in file_counts:
        print(f"  {row['status']}: {row['c']}")

    pending = conn.execute(
        """SELECT COUNT(*) as c FROM proposals
           WHERE status='pending' AND batch_key LIKE ?;""",
        ("%" + root + "%",),
    ).fetchone()["c"]
    approved = conn.execute(
        """SELECT COUNT(*) as c FROM proposals
           WHERE status='approved' AND batch_key LIKE ?;""",
        ("%" + root + "%",),
    ).fetchone()["c"]
    print(f"\nProposals touching this path: {pending} pending, {approved} approved (not yet applied)")

    reservations = conn.execute(
        "SELECT path_prefix, reason FROM protected_paths WHERE path_prefix LIKE ?;",
        (root + "%",),
    ).fetchall()
    print(f"\nReservations under this path: {len(reservations)}")
    for r in reservations:
        print(f"  - {r['path_prefix']}  ({r['reason']})")

    if latest["status"] == "interrupted":
        print(f"\n[NOTE] Most recent scan of this exact root was interrupted and never completed.")
        print(f"  The counts above reflect only what was durably committed before it stopped.")

    conn.close()


def cmd_brief(args):
    cfg = load_config()
    if not Path(cfg["db_path"]).exists():
        print("[FAILED] No ledger found yet. Run 'ark bootstrap' first.")
        return

    conn = get_connection(cfg["db_path"])
    initialize_schema(conn)

    print("MINI ARK BRIEF\n")

    raw_events = conn.execute(
        "SELECT COUNT(*) as c FROM events WHERE status='raw';"
    ).fetchone()["c"]
    print(f"Unreconciled events: {raw_events}")

    open_loops = conn.execute(
        "SELECT description FROM open_loops WHERE status='open' ORDER BY created_at DESC LIMIT 10;"
    ).fetchall()
    print(f"\nOpen loops ({len(open_loops)} shown, most recent first):")
    for row in open_loops:
        print(f"  - {row['description']}")

    pending_proposals = conn.execute(
        "SELECT id, description FROM proposals WHERE status='pending' ORDER BY id;"
    ).fetchall()
    print(f"\nPending proposals: {len(pending_proposals)}")
    for row in pending_proposals:
        print(f"  #{row['id']}: {row['description']}")

    conn.close()


def cmd_check_duplicates(args):
    cfg = load_config()
    conn = get_connection(cfg["db_path"])
    initialize_schema(conn)

    print(f"[STARTING] Checking for duplicate canonical_path rows"
          + (f" under {args.under}" if args.under else " (all)"))
    result = reconcile_mod.find_duplicate_canonical_paths(conn, root_path=args.under)

    print(f"\nUNIQUE constraint actually enforced on canonical_path: {result['unique_constraint_enforced']}")
    if not result["unique_constraint_enforced"]:
        print("  This table predates the UNIQUE constraint in schema.sql -- nothing has")
        print("  ever stopped duplicate rows for the same path from being inserted.")
    print(f"\nDuplicate canonical_path values found: {result['duplicate_path_count']}")
    for ex in result["examples"]:
        print(f"  {ex['path']}")
        print(f"    {ex['row_count']} rows -- statuses: {ex['statuses']} -- row ids: {ex['row_ids']}")

    conn.close()


def cmd_diagnose(args):
    cfg = load_config()
    conn = get_connection(cfg["db_path"])
    initialize_schema(conn)

    print(f"[STARTING] Diagnosing 'missing' files"
          + (f" under {args.under}" if args.under else " (all)")
          + " -- read-only, changes nothing")
    result = reconcile_mod.analyze_symmetry(conn, root_path=args.under)

    print(f"\nTotal missing: {result['total_missing']}")
    print(f"  Case-only path drift (same file, wrong 'missing' status): {result['case_only_count']}")
    print(f"  Genuine moves (same file, real new location):            {result['real_move_count']}")
    print(f"  Unmatched (no hash match -- actually gone, or unrehashed): {result['unmatched_count']}")
    print(f"\nVerdict: {result['verdict']}")

    if result["case_only_examples"]:
        print(f"\nExamples of case-only drift:")
        for ex in result["case_only_examples"]:
            print(f"  missing: {ex['missing_as_recorded']}")
            print(f"  present: {ex['present_as_recorded']}")
    if result["real_move_examples"]:
        print(f"\nExamples of genuine moves:")
        for ex in result["real_move_examples"]:
            print(f"  {ex['old_path']}")
            print(f"    -> {ex['new_path']}")
    if result["unmatched_examples"]:
        print(f"\nExamples of unmatched (no pairing possible):")
        for ex in result["unmatched_examples"]:
            print(f"  {ex['path']}  ({ex['reason']})")

    conn.close()


def cmd_ingest(args):
    cfg = load_config()
    conn = get_connection(cfg["db_path"])
    initialize_schema(conn)

    print("[STARTING] Conversation ingestion gateway v0.1")
    print("  Preserving raw input, extracting review candidates, no canonical promotion.")
    result = conversation_ingest.ingest_conversation(
        conn,
        args.input,
        output_path=args.output,
        platform=args.platform,
        source_container=args.source_container,
    )
    conn.close()

    print("[SUCCESS] Review JSON written.")
    print(f"  Output: {result['output_path']}")
    print(f"  Source row: {result['source_id']}")
    print(f"  Handoff row: {result['handoff_id']}")
    print(f"  Candidates: {result['candidate_count']} "
          f"(PMM={result['pmm_count']}, PWM={result['pwm_count']})")
    print("  No proposals, open loops, decisions, or accepted state were created.")


def cmd_reconcile(args):
    print("[STARTING] Reconciliation")
    print("[WARNING] Not yet implemented -- Phase 5 of the build order.")
    print("  This will process raw events into proposed/accepted state.")


def cmd_find_empty(args):
    cfg = load_config()
    conn = get_connection(cfg["db_path"])
    initialize_schema(conn)

    print(f"[STARTING] Searching {args.path} for folders that lead to nothing "
          f"(read-only -- nothing will be deleted)")
    result = pruning.propose_prune(conn, args.path)

    if result["status"] == "no_data":
        print(f"[SUCCESS] {result['message']}")
    else:
        print(f"[SUCCESS] Found {result['empty_folders_found']} dead-end folder(s).")
        for c in result["candidates"]:
            extra = f" ({c['nested_empty_subfolders']} empty subfolder(s) nested inside)" if c["nested_empty_subfolders"] else ""
            print(f"    - {c['path']}{extra}")
        print(f"\n  Proposal #{result['proposal_id']} created ({result['empty_folders_found']} item(s)).")
        print(f"  Review:  python ark.py list-items {result['proposal_id']}")
        print(f"  Skip one you want kept:  python ark.py skip-item <item_id>")
        print(f"  Then:    python ark.py approve {result['proposal_id']}")
        print(f"           python ark.py apply {result['proposal_id']} --preview")

    conn.close()


def cmd_list_items(args):
    cfg = load_config()
    conn = get_connection(cfg["db_path"])
    initialize_schema(conn)
    items = apply_mod.list_proposal_items(conn, args.proposal_id)
    if not items:
        print(f"[WARNING] No proposal_items found for proposal {args.proposal_id}")
    else:
        print(f"Items for proposal {args.proposal_id}:")
        for i in items:
            line = f"  #{i['id']}  [{i['status']:8s}]  {i['requested_mode']:10s}  {i['canonical_path']}"
            if i["block_reason"]:
                line += f"  ({i['block_reason']})"
            print(line)
    conn.close()


def cmd_skip_item(args):
    cfg = load_config()
    conn = get_connection(cfg["db_path"])
    initialize_schema(conn)
    result = apply_mod.skip_item(conn, args.item_id, reason=args.reason or "user declined")
    if result["status"] == "skipped":
        print(f"[SUCCESS] Item {args.item_id} skipped -- apply will never act on it.")
    else:
        print(f"[FAILED] {result['reason']}")
        sys.exit(1)
    conn.close()


def cmd_skip_protected_items(args):
    cfg = load_config()
    conn = get_connection(cfg["db_path"])
    initialize_schema(conn)

    if args.proposal_id is None:
        rows = conn.execute(
            """SELECT proposal_items.id, proposal_items.proposal_id, proposal_items.canonical_path
               FROM proposal_items
               JOIN proposals ON proposals.id = proposal_items.proposal_id
               WHERE proposal_items.status = 'pending'
                 AND proposals.status = 'pending'
               ORDER BY proposal_items.proposal_id, proposal_items.id;"""
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT id, proposal_id, canonical_path
               FROM proposal_items
               WHERE status = 'pending' AND proposal_id = ?
               ORDER BY id;""",
            (args.proposal_id,),
        ).fetchall()

    protected = []
    for row in rows:
        reason = apply_mod.is_protected(conn, row["canonical_path"])
        if reason:
            protected.append((row, reason))

    scope = f"proposal {args.proposal_id}" if args.proposal_id is not None else "all pending proposals"
    print(f"Protected pending items in {scope}: {len(protected)}")

    for row, reason in protected[:args.limit]:
        print(f"  #{row['id']} proposal {row['proposal_id']}  {row['canonical_path']}")
        print(f"      {reason}")

    if len(protected) > args.limit:
        print(f"  ... {len(protected) - args.limit} more not shown; use --limit to show more.")

    if not args.execute:
        print("\nDry run only. To mark these items skipped:")
        if args.proposal_id is None:
            print("  .\\ark.cmd skip-protected-items --execute")
        else:
            print(f"  .\\ark.cmd skip-protected-items {args.proposal_id} --execute")
        conn.close()
        return

    for row, reason in protected:
        conn.execute(
            """UPDATE proposal_items
               SET status='skipped',
                   block_reason=?,
                   resolved_at=datetime('now')
               WHERE id=?;""",
            (f"Protected/reserved path: {reason}", row["id"]),
        )
    conn.commit()
    print(f"\n[SUCCESS] Skipped {len(protected)} protected item(s).")

    conn.close()


def cmd_close_empty_proposals(args):
    cfg = load_config()
    conn = get_connection(cfg["db_path"])
    initialize_schema(conn)

    rows = conn.execute(
        """SELECT proposals.id, proposals.description
           FROM proposals
           WHERE proposals.status = 'pending'
             AND NOT EXISTS (
               SELECT 1 FROM proposal_items
               WHERE proposal_items.proposal_id = proposals.id
                 AND proposal_items.status = 'pending'
             )
           ORDER BY proposals.id;"""
    ).fetchall()

    print(f"Pending proposals with no pending items: {len(rows)}")
    for row in rows:
        print(f"  #{row['id']}: {row['description'][:160]}")

    if not args.execute:
        print("\nDry run only. To close these proposal headers:")
        print("  .\\ark.cmd close-empty-proposals --execute")
        conn.close()
        return

    conn.execute(
        """UPDATE proposals
           SET status='rejected',
               resolved_at=datetime('now')
           WHERE status='pending'
             AND NOT EXISTS (
               SELECT 1 FROM proposal_items
               WHERE proposal_items.proposal_id = proposals.id
                 AND proposal_items.status = 'pending'
             );"""
    )
    conn.commit()
    print(f"\n[SUCCESS] Closed {len(rows)} proposal header(s) with no pending items.")
    conn.close()


def cmd_reserve(args):
    cfg = load_config()
    conn = get_connection(cfg["db_path"])
    initialize_schema(conn)
    apply_mod.add_reservation(conn, args.path, reason=args.reason)
    print(f"[SUCCESS] Reserved: {args.path}")
    print(f"  Off-limits to find-empty and apply (move/shortcut/quarantine), including everything nested under it.")
    conn.close()


def cmd_unreserve(args):
    cfg = load_config()
    conn = get_connection(cfg["db_path"])
    initialize_schema(conn)
    result = apply_mod.remove_reservation(conn, args.path)
    if result["status"] == "removed":
        print(f"[SUCCESS] Un-reserved: {args.path}")
    elif result["status"] == "not_found":
        print(f"[WARNING] No reservation found for exactly: {args.path}")
    else:
        print(f"[FAILED] {result['reason']}")
        sys.exit(1)
    conn.close()


def cmd_list_reservations(args):
    cfg = load_config()
    conn = get_connection(cfg["db_path"])
    initialize_schema(conn)
    rows = apply_mod.list_reservations(conn)
    print(f"Protected / reserved paths ({len(rows)}):")
    for r in rows:
        print(f"  [{r['category']:22s}] {r['path_prefix']}  -- {r['reason']}")
    conn.close()


def cmd_approve(args):
    cfg = load_config()
    conn = get_connection(cfg["db_path"])
    initialize_schema(conn)
    row = conn.execute("SELECT * FROM proposals WHERE id = ?;", (args.proposal_id,)).fetchone()
    if row is None:
        print(f"[FAILED] No proposal with id {args.proposal_id}")
        sys.exit(1)
        return
    conn.execute("UPDATE proposals SET status='approved', resolved_at=datetime('now') WHERE id=?;",
                 (args.proposal_id,))
    conn.commit()
    print(f"[SUCCESS] Proposal {args.proposal_id} approved.")
    print(f"  {row['description'][:200]}")
    print(f"\n  Next: python ark.py apply {args.proposal_id}   (plan first with --preview)")
    conn.close()


def cmd_set_item_mode(args):
    cfg = load_config()
    conn = get_connection(cfg["db_path"])
    initialize_schema(conn)
    row = conn.execute("SELECT * FROM proposal_items WHERE id = ?;", (args.item_id,)).fetchone()
    if row is None:
        print(f"[FAILED] No proposal_item with id {args.item_id}")
        sys.exit(1)
        return
    conn.execute("UPDATE proposal_items SET requested_mode=? WHERE id=?;", (args.mode, args.item_id))
    conn.commit()
    print(f"[SUCCESS] Item {args.item_id} ({row['canonical_path']}) requested_mode -> {args.mode}")
    conn.close()


def cmd_apply(args):
    cfg = load_config()
    conn = get_connection(cfg["db_path"])
    initialize_schema(conn)

    print(f"[STARTING] Planning apply for proposal {args.proposal_id}")
    try:
        plan = apply_mod.plan_apply(conn, args.proposal_id)
    except apply_mod.ProposalNotApproved as e:
        print(f"[FAILED] {e}")
        print(f"  Approve first: python ark.py approve {args.proposal_id}")
        sys.exit(1)
        return

    if plan["status"] != "planned":
        print(f"[FAILED] {plan.get('reason', plan)}")
        sys.exit(1)
        return

    print(f"[SUCCESS] Plan built.")
    print(f"  Total items:        {plan['total_items']}")
    print(f"  Blocked (protected): {plan['blocked_count']}")
    for b in plan["blocked"]:
        print(f"    - {b['path']}: {b['reason']}")
    print(f"  Downgraded to shortcut (dependents found): {plan['downgraded_count']}")
    print(f"  Eligible to apply:  {len(plan['to_apply'])}")

    if args.preview:
        print(f"\n  [PREVIEW ONLY] Nothing has been changed. Re-run without --preview to execute.")
        conn.close()
        return

    if not plan["to_apply"]:
        print(f"\n  Nothing eligible to apply.")
        conn.close()
        return

    print(f"\n[STARTING] Executing {len(plan['to_apply'])} item(s)")
    result = apply_mod.execute_apply(conn, plan)

    if result["status"] == "blocked_by_circuit_breaker":
        print(f"[BLOCKED] {result['reason']}")
        sys.exit(1)
    elif result["status"] == "blocked_by_kill_switch":
        print(f"[BLOCKED] {result['reason']}")
        sys.exit(1)
    else:
        print(f"[SUCCESS] Applied: {result['applied_count']}  Failed: {result['failed_count']}")
        for f in result["failed"]:
            print(f"    [FAILED] {f['path']}: {f['reason']}")

    conn.close()


def cmd_register_dependent(args):
    cfg = load_config()
    conn = get_connection(cfg["db_path"])
    initialize_schema(conn)
    dep_id = apply_mod.register_dependent(
        conn, args.path, args.program,
        reference_location=args.location, reference_context=args.context,
    )
    print(f"[SUCCESS] Registered dependent #{dep_id}: {args.program} depends on {args.path}")
    conn.close()


def cmd_scan_dependents(args):
    cfg = load_config()
    conn = get_connection(cfg["db_path"])
    initialize_schema(conn)

    candidates = conn.execute(
        "SELECT canonical_path FROM files WHERE canonical_path LIKE ? AND status='present';",
        (str(args.under) + "%",),
    ).fetchall()
    candidate_paths = [r["canonical_path"] for r in candidates]

    result = apply_mod.scan_config_for_dependents(conn, args.config, args.program, candidate_paths)
    if result["status"] != "scanned":
        print(f"[FAILED] {result['reason']}")
        sys.exit(1)
        return

    print(f"[SUCCESS] Scanned {args.config}")
    print(f"  Dependents found: {len(result['dependents_found'])}")
    for d in result["dependents_found"]:
        print(f"    line {d['line']}: {d['path']}")
    conn.close()


def cmd_undo(args):
    cfg = load_config()
    conn = get_connection(cfg["db_path"])
    initialize_schema(conn)

    row = conn.execute("SELECT action_type FROM action_log WHERE id = ?;", (args.op_id,)).fetchone()
    if row is None:
        print(f"[FAILED] No such operation: OP-{args.op_id:06d}")
        sys.exit(1)
        return

    try:
        if row["action_type"] in ("file_move", "file_shortcut", "file_quarantine"):
            result = apply_mod.undo_apply(conn, args.op_id)
        elif row["action_type"] == "dedupe_row_merge":
            result = dedupe.undo_dedupe(conn, args.op_id)
        elif row["action_type"] == "case_drift_cleanup":
            result = casefix.undo_case_drift_cleanup(conn, args.op_id)
        else:
            def _no_op_undo(previous_state):
                # Pre-apply-era ops (or anything not a real filesystem
                # action) have nothing to reverse on disk.
                print("  (no filesystem action to reverse for this op type)")
            result = undo_operation(conn, args.op_id, _no_op_undo)
    except ExecutionDisabled as e:
        print(str(e))
        sys.exit(1)
        return
    conn.close()


def cmd_graduate(args):
    cfg = load_config()
    conn = get_connection(cfg["db_path"])
    initialize_schema(conn)

    if args.phase == 2:
        report = check_phase2_scanner(conn, args.test_root)
        print_graduation_report(report)
    else:
        print(f"[WARNING] No graduation checklist implemented for phase {args.phase} yet.")

    conn.close()


def cmd_kill_status(args):
    if KILL_SWITCH_FLAG.exists():
        print(f"[BLOCKED] Kill switch is ACTIVE: {KILL_SWITCH_FLAG}")
        print("  Mini ARK may observe/report but cannot execute mutations.")
        print("  Delete this file manually to resume.")
    else:
        print(f"[OK] Kill switch is not set. Mutations are permitted (subject to permission tiers).")
        print(f"  To engage emergency stop: touch \"{KILL_SWITCH_FLAG}\"")


def cmd_cockpit(args):
    root = Path(__file__).parent
    start_script = root / "start_mini_ark.ps1"
    index = root / "index.html"

    print("MINI ARK COCKPIT\n")
    print(f"Home:       {root}")
    print(f"Dashboard:  {index}")
    print("")
    print("Start local cockpit:")
    print(f"  powershell -ExecutionPolicy Bypass -File \"{start_script}\"")
    print("")
    print("Core checks:")
    print("  .\\ark.cmd doctor")
    print("  .\\ark.cmd brief")
    print("  .\\ark.cmd kill-status")
    print("")
    print("Read-only status:")
    print("  .\\ark.cmd status R:\\")
    print("  .\\ark.cmd inventory --under R:\\")
    print("")
    print("Guide:")
    print(f"  {root / 'docs' / 'USER_GUIDE.md'}")


def cmd_report(args):
    cfg = load_config()
    conn = get_connection(cfg["db_path"])
    initialize_schema(conn)

    if args.output:
        path = write_report(conn, args.path, args.output)
        print(f"[SUCCESS] Report written: {path}")
    else:
        print(generate_scan_report(conn, args.path))

    conn.close()


def cmd_propose_organization(args):
    cfg = load_config()
    conn = get_connection(cfg["db_path"])
    initialize_schema(conn)

    print(f"[STARTING] Analyzing {args.path} for organization proposals "
          f"(read-only -- nothing will be moved)")
    result = analyze_and_propose(conn, args.path)

    if result["status"] == "no_data":
        print(f"[WARNING] {result['message']}")
    else:
        print(f"[SUCCESS] Analysis complete.")
        print(f"  Files analyzed: {result['total_files_analyzed']}")
        for category, count in result["categories_found"].items():
            print(f"    {category}: {count}")
        if result["uncategorized_count"]:
            print(f"    Uncategorized: {result['uncategorized_count']}")
        print(f"  Proposals written: {result['proposals_written']}")
        print(f"  {result['note']}")
        print(f"\n  Review with: python ark.py brief")

    conn.close()


def cmd_propose_media_organization(args):
    cfg = load_config()
    conn = get_connection(cfg["db_path"])
    initialize_schema(conn)

    excludes = args.exclude or []
    ffprobe_path = cfg.get("ffprobe_path", "ffprobe")

    print(f"[STARTING] Analyzing {args.path} for media organization "
          f"(read-only -- nothing will be moved)")
    if excludes:
        print(f"  Excluding folders: {', '.join(excludes)}")

    result = analyze_media_and_propose(conn, args.path, exclude_folders=excludes,
                                        ffprobe_path=ffprobe_path)

    if result["status"] == "no_data":
        print(f"[WARNING] {result['message']}")
    else:
        print(f"[SUCCESS] Analysis complete.")
        print(f"  Total files scanned:     {result['total_files_scanned']}")
        print(f"  Excluded by folder rule: {result['excluded_by_folder_rule']}")
        print(f"  Images:                  {result['images_found']}")
        print(f"  Videos by duration:")
        for bucket, count in result["videos_by_duration"].items():
            print(f"    {bucket}: {count}")
        if result["unprobeable_videos"]:
            print(f"  [WARNING] Unprobeable videos: {result['unprobeable_videos']}")
        print(f"  Other files ignored:     {result['other_files_ignored']}")
        print(f"  Proposals written:       {result['proposals_written']}")
        print(f"  {result['note']}")
        print(f"\n  Review with: python ark.py brief")

    conn.close()


def cmd_carebloom_consolidate(args):
    canonical_root = args.canonical_root
    docs_root = str(Path(__file__).parent / "docs")
    source_roots = args.source_root or carebloom_consolidation.DEFAULT_SOURCE_ROOTS
    dependency_roots = args.dependency_root or carebloom_consolidation.DEFAULT_DEPENDENCY_ROOTS

    if args.plan:
        plan_path = args.plan
    else:
        print("[STARTING] Building CareBloom consolidation plan")
        print("  Policy: copy first, verify, update refs only when requested, leave originals in place.")
        plan = carebloom_consolidation.build_plan(
            source_roots=source_roots,
            dependency_roots=dependency_roots,
            canonical_root=canonical_root,
            docs_root=docs_root,
            limit=args.limit,
        )
        plan_path = plan["json_path"]
        print(f"[SUCCESS] Plan written: {plan['markdown_path']}")
        print(f"  JSON: {plan['json_path']}")
        print(f"  Assets: {plan['asset_count']}")
        print(f"  Assets with dependency refs: {plan['dependent_asset_count']}")
        print(f"  Dependency refs: {plan['dependency_reference_count']}")

    if not args.execute:
        print("")
        print("Plan only. To execute copy-first consolidation:")
        print(f"  .\\ark.cmd carebloom-consolidate --plan \"{plan_path}\" --execute")
        print("")
        print("To also update known text references after verified copies:")
        print(f"  .\\ark.cmd carebloom-consolidate --plan \"{plan_path}\" --execute --update-refs")
        return

    print("[STARTING] Executing CareBloom consolidation")
    result = carebloom_consolidation.execute_plan(plan_path, update_refs=args.update_refs)
    print(f"[SUCCESS] Result written: {result['result_path']}")
    print(f"  Copied: {result['copied_count']}")
    print(f"  Reference updates: {result['reference_update_count']}")
    print(f"  Failed: {result['failed_count']}")
    print("  Originals left in place: yes")
    if result["failed"]:
        print("  Failures:")
        for failure in result["failed"][:20]:
            print(f"    - {failure['source']}: {failure['reason']}")


def cmd_carebloom_archive_map(args):
    docs_root = str(Path(__file__).parent / "docs")
    source_roots = args.source_root or carebloom_consolidation.DEFAULT_SOURCE_ROOTS
    dependency_roots = args.dependency_root or carebloom_consolidation.DEFAULT_DEPENDENCY_ROOTS

    if args.plan:
        plan_path = args.plan
    else:
        print("[STARTING] Building CareBloomOS archive/deletion-prep map")
        print("  Policy: copy first, dependency hold, deletion-prep only, originals stay in place.")
        plan = carebloom_consolidation.build_archive_map(
            source_roots=source_roots,
            dependency_roots=dependency_roots,
            target_root=args.target_root,
            docs_root=docs_root,
            older_than_days=args.older_than_days,
            limit=args.limit,
        )
        plan_path = plan["json_path"]
        print(f"[SUCCESS] Map written: {plan['markdown_path']}")
        print(f"  JSON: {plan['json_path']}")
        print(f"  CSV: {plan['csv_path']}")
        print(f"  Assets mapped: {plan['asset_count']}")
        print(f"  Dependency hold: {plan['dependent_hold_count']}")
        print(f"  Active recent non-dependent: {plan['active_recent_nondependent_count']}")
        print(f"  Deletion-prep candidates: {plan['deletion_prep_count']}")

    if not args.execute:
        print("")
        print("Map only. To stage the mapped structure with copied files:")
        print(f"  .\\ark.cmd carebloom-archive-map --plan \"{plan_path}\" --execute")
        return

    print("[STARTING] Staging CareBloomOS archive structure")
    result = carebloom_consolidation.execute_archive_map(plan_path)
    print(f"[SUCCESS] Result written: {result['result_path']}")
    print(f"  Target root: {result['target_root']}")
    print(f"  Copied/verified: {result['copied_count']}")
    print(f"  Failed: {result['failed_count']}")
    print(f"  Deletion-prep candidates staged: {result['deletion_prep_count']}")
    print(f"  Dependency hold staged: {result['dependent_hold_count']}")
    print("  Originals left in place: yes")
    print("  Files deleted: 0")
    if result["failed"]:
        print("  Failures:")
        for failure in result["failed"][:20]:
            print(f"    - {failure['source']}: {failure['reason']}")


def cmd_profile_migration_map(args):
    docs_root = str(Path(__file__).parent / "docs")
    profile_roots = args.profile_root or profile_migration.DEFAULT_PROFILE_ROOTS

    if args.plan:
        plan_path = args.plan
    else:
        print("[STARTING] Building R: user-profile migration map")
        print("  Policy: copy first, verify, classify profile contents, originals stay in place.")
        plan = profile_migration.build_profile_migration_map(
            profile_roots=profile_roots,
            target_root=args.target_root,
            docs_root=docs_root,
            limit=args.limit,
        )
        plan_path = plan["json_path"]
        print(f"[SUCCESS] Map written: {plan['markdown_path']}")
        print(f"  JSON: {plan['json_path']}")
        print(f"  CSV: {plan['csv_path']}")
        print(f"  Items mapped: {plan['item_count']}")
        print(f"  Total bytes: {plan['total_bytes']}")
        print("  Destination buckets:")
        for bucket, summary in sorted(plan["bucket_summary"].items()):
            print(f"    {bucket}: {summary['count']} files")

    if not args.execute:
        print("")
        print("Map only. To stage copied files:")
        print(f"  .\\ark.cmd profile-migration-map --plan \"{plan_path}\" --execute")
        return

    print("[STARTING] Staging R: user-profile migration copies")
    result = profile_migration.execute_profile_migration_map(plan_path)
    print(f"[SUCCESS] Result written: {result['result_path']}")
    print(f"  Target root: {result['target_root']}")
    print(f"  Copied/verified: {result['copied_count']}")
    print(f"  Failed: {result['failed_count']}")
    print(f"  Files deleted: {result['files_deleted']}")
    print("")
    print("No profile roots removed. Review staged copies before any cleanup approval.")
    if result["failed"]:
        print("  Failures:")
        for failure in result["failed"][:20]:
            print(f"    - {failure['source']}: {failure['reason']}")


def cmd_r_hierarchy_scan(args):
    docs_root = str(Path(__file__).parent / "docs")
    print("[STARTING] Scanning R: top-level hierarchy")
    report = profile_migration.scan_r_hierarchy(
        root_path=args.root,
        docs_root=docs_root,
        max_depth=args.max_depth,
    )
    print(f"[SUCCESS] Hierarchy report written: {report['markdown_path']}")
    print(f"  JSON: {report['json_path']}")
    print(f"  Top-level entries: {report['entry_count']}")
    print("")
    print("Suggested hierarchy:")
    for item in report["suggested_hierarchy"]:
        print(f"  {item}")


def main():
    parser = argparse.ArgumentParser(prog="ark", description="Mini ARK")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("bootstrap", aliases=["boot"], help="Initialize config and ledger").set_defaults(func=cmd_bootstrap)

    scan_p = sub.add_parser("scan", aliases=["sc"], help="Read-only filesystem scan")
    scan_p.add_argument("path", help="Path to scan")
    scan_p.add_argument("--resume", action="store_true",
                         help="Resume a previously interrupted scan of this same path")
    scan_p.set_defaults(func=cmd_scan)

    sub.add_parser("doctor", aliases=["dr"], help="Health check").set_defaults(func=cmd_doctor)
    status_p = sub.add_parser("status", aliases=["st"], help="Show everything the ledger knows about a specific path: scan history, file counts, pending proposals, reservations")
    status_p.add_argument("path")
    status_p.set_defaults(func=cmd_status)

    sub.add_parser("brief", aliases=["br"], help="Summarize current state").set_defaults(func=cmd_brief)
    sub.add_parser("cockpit", aliases=["cp"], help="Show Mini ARK cockpit launch commands").set_defaults(func=cmd_cockpit)
    checkdupe_p = sub.add_parser("check-duplicates", aliases=["dupes"], help="Fast check: does 'files' actually enforce UNIQUE on canonical_path, and are there duplicate rows right now?")
    checkdupe_p.add_argument("--under", default=None)
    checkdupe_p.set_defaults(func=cmd_check_duplicates)

    resolve_p = sub.add_parser("resolve-duplicates", aliases=["rdup"], help="Consolidate duplicate canonical_path rows (dry-run by default). Never touches real files.")
    resolve_p.add_argument("--under", default=None)
    resolve_p.add_argument("--execute", action="store_true", help="Actually merge rows. Without this, only reports what would happen.")
    resolve_p.set_defaults(func=cmd_resolve_duplicates)

    casedrift_p = sub.add_parser("resolve-case-drift", aliases=["rcd"], help="Remove stale 'missing' rows confirmed by diagnose as case-only path drift (dry-run by default). Never touches real files.")
    casedrift_p.add_argument("--under", default=None)
    casedrift_p.add_argument("--execute", action="store_true")
    casedrift_p.set_defaults(func=cmd_resolve_case_drift)

    inventory_p = sub.add_parser("inventory", aliases=["inv"], help="Classify files against the R: doctrine map, with confidence tiers. Read-only -- writes a report, no proposals, no moves.")
    inventory_p.add_argument("--under", default=None)
    inventory_p.set_defaults(func=cmd_inventory)

    rename_p = sub.add_parser("propose-rename", aliases=["pren"], help="Propose a batch rename: ordered file list + template with {n} auto-increment")
    rename_p.add_argument("files", nargs="*", help="File paths to rename, in order")
    rename_p.add_argument("--list-file", default=None, help="Text file, one path per line, instead of passing paths directly")
    rename_p.add_argument("--template", required=True, help="e.g. 'heartstone_care_rail_v{n}' -- extension is preserved automatically")
    rename_p.add_argument("--start", type=int, default=1)
    rename_p.add_argument("--pad", type=int, default=2, help="Zero-pad width, e.g. 2 -> v01, v02...")
    rename_p.add_argument("--dest-dir", default=None, help="Rename into this folder instead of in-place")
    rename_p.set_defaults(func=cmd_propose_rename)

    diagnose_p = sub.add_parser("diagnose", aliases=["dx"], help="Read-only: distinguish case-only path drift from genuine moves among 'missing' files")
    diagnose_p.add_argument("--under", default=None, help="Scope to files under this root (e.g. R:\\)")
    diagnose_p.set_defaults(func=cmd_diagnose)

    ingest_p = sub.add_parser("ingest", help="Ingest one normalized conversation into review JSON")
    ingest_p.add_argument("input", help="Normalized conversation JSON file")
    ingest_p.add_argument("--platform", default=None, help="Source platform, e.g. ChatGPT")
    ingest_p.add_argument("--source-container", default=None, help="Original container/project metadata")
    ingest_p.add_argument("--output", default=None, help="Review JSON output path")
    ingest_p.set_defaults(func=cmd_ingest)
    sub.add_parser("reconcile", help="[stub] Reconcile raw events").set_defaults(func=cmd_reconcile)

    approve_p = sub.add_parser("approve", aliases=["appr"], help="Approve a pending proposal so it becomes eligible for apply")
    approve_p.add_argument("proposal_id", type=int)
    approve_p.set_defaults(func=cmd_approve)

    find_empty_p = sub.add_parser("find-empty", aliases=["fe"], help="Search for folders that lead to nothing and propose quarantining them")
    find_empty_p.add_argument("path", help="Root path to search")
    find_empty_p.set_defaults(func=cmd_find_empty)

    list_items_p = sub.add_parser("list-items", aliases=["li"], help="Show the itemized per-file list for a proposal")
    list_items_p.add_argument("proposal_id", type=int)
    list_items_p.set_defaults(func=cmd_list_items)

    skip_p = sub.add_parser("skip-item", aliases=["si"], help="Exclude a single proposal_item from apply, without affecting siblings")
    skip_p.add_argument("item_id", type=int)
    skip_p.add_argument("--reason", default=None)
    skip_p.set_defaults(func=cmd_skip_item)

    skip_protected_p = sub.add_parser("skip-protected-items", aliases=["spi"], help="Dry-run or skip pending proposal items that are now protected/reserved")
    skip_protected_p.add_argument("proposal_id", nargs="?", type=int, help="Optional proposal to limit the check")
    skip_protected_p.add_argument("--execute", action="store_true", help="Actually mark protected pending items as skipped")
    skip_protected_p.add_argument("--limit", type=int, default=40, help="Maximum protected items to print")
    skip_protected_p.set_defaults(func=cmd_skip_protected_items)

    close_empty_p = sub.add_parser("close-empty-proposals", aliases=["cep"], help="Dry-run or close pending proposal headers that have no pending items left")
    close_empty_p.add_argument("--execute", action="store_true", help="Actually close empty pending proposal headers")
    close_empty_p.set_defaults(func=cmd_close_empty_proposals)

    reserve_p = sub.add_parser("reserve", aliases=["res"], help="Mark a folder (and everything nested under it) off-limits to Mini ARK")
    reserve_p.add_argument("path", help="Folder to reserve -- e.g. scaffolding built ahead of being populated")
    reserve_p.add_argument("--reason", default=None)
    reserve_p.set_defaults(func=cmd_reserve)

    unreserve_p = sub.add_parser("unreserve", aliases=["unres"], help="Remove a reservation (cannot remove the hardcoded system floor)")
    unreserve_p.add_argument("path")
    unreserve_p.set_defaults(func=cmd_unreserve)

    sub.add_parser("list-reservations", aliases=["lr"], help="Show all protected/reserved paths").set_defaults(func=cmd_list_reservations)

    item_p = sub.add_parser("set-item-mode", aliases=["sim"], help="Override a single proposal_item's mode ('move', 'shortcut', or 'quarantine')")
    item_p.add_argument("item_id", type=int)
    item_p.add_argument("mode", choices=["move", "shortcut", "quarantine"])
    item_p.set_defaults(func=cmd_set_item_mode)

    apply_p = sub.add_parser("apply", aliases=["ap"], help="Plan and execute an approved proposal's file operations")
    apply_p.add_argument("proposal_id", type=int)
    apply_p.add_argument("--preview", action="store_true",
                          help="Build and print the plan only; make no filesystem changes")
    apply_p.set_defaults(func=cmd_apply)

    dep_p = sub.add_parser("register-dependent", aliases=["regdep"], help="Manually declare a program depends on a path")
    dep_p.add_argument("path", help="Canonical path being depended on")
    dep_p.add_argument("program", help="Program name, e.g. Rainmeter")
    dep_p.add_argument("--location", default=None, help="Config file where the reference lives")
    dep_p.add_argument("--context", default=None, help="The actual line/snippet referencing it")
    dep_p.set_defaults(func=cmd_register_dependent)

    scandep_p = sub.add_parser("scan-dependents", aliases=["scandep"], help="Scan a text config file for references to known files")
    scandep_p.add_argument("config", help="Path to the config file to scan (e.g. a Rainmeter .ini)")
    scandep_p.add_argument("program", help="Program name this config belongs to")
    scandep_p.add_argument("--under", required=True, help="Only check candidate files under this root")
    scandep_p.set_defaults(func=cmd_scan_dependents)

    undo_p = sub.add_parser("undo", aliases=["u"], help="Reverse a completed operation")
    undo_p.add_argument("op_id", type=int, help="Operation ID number")
    undo_p.set_defaults(func=cmd_undo)

    grad_p = sub.add_parser("graduate", aliases=["grad"], help="Run graduation checklist for a phase")
    grad_p.add_argument("phase", type=int, help="Phase number to check")
    grad_p.add_argument("--test-root", default=None, help="Test directory (phase 2 only)")
    grad_p.set_defaults(func=cmd_graduate)

    sub.add_parser("kill-status", aliases=["ks"], help="Check emergency stop status").set_defaults(func=cmd_kill_status)

    report_p = sub.add_parser("report", aliases=["rep"], help="Generate a Markdown report of the ledger's current state")
    report_p.add_argument("path", help="Root path to scope the report to")
    report_p.add_argument("--output", default=None, help="File to write the report to (prints to console if omitted)")
    report_p.set_defaults(func=cmd_report)

    propose_p = sub.add_parser("propose-organization", aliases=["porg"],
                                help="Analyze scanned files and PROPOSE a folder structure (never moves anything)")
    propose_p.add_argument("path", help="Root path to analyze (must already be scanned)")
    propose_p.set_defaults(func=cmd_propose_organization)

    media_p = sub.add_parser("propose-media-organization", aliases=["pmedia"],
                              help="PROPOSE image/video split with videos bucketed by real duration (never moves anything)")
    media_p.add_argument("path", help="Root path to analyze (must already be scanned)")
    media_p.add_argument("--exclude", action="append", default=[],
                          help="Folder name to skip entirely, e.g. --exclude \"all stars\" (repeatable)")
    media_p.set_defaults(func=cmd_propose_media_organization)

    carebloom_p = sub.add_parser("carebloom-consolidate", aliases=["cbc"],
                                  help="Plan or execute copy-first CareBloom asset consolidation without stopping Rainmeter/Wallpaper")
    carebloom_p.add_argument("--canonical-root", default=r"R:\Projects\CareBloomOS\99_Consolidated_Assets",
                             help="Destination root for consolidated CareBloom assets")
    carebloom_p.add_argument("--source-root", action="append", default=None,
                             help="CareBloom source root to scan; repeatable. Defaults to known roots.")
    carebloom_p.add_argument("--dependency-root", action="append", default=None,
                             help="Text config/runtime root to scan for source references; repeatable.")
    carebloom_p.add_argument("--limit", type=int, default=None,
                             help="Limit assets for a small MVP test plan")
    carebloom_p.add_argument("--plan", default=None,
                             help="Existing JSON plan to execute")
    carebloom_p.add_argument("--execute", action="store_true",
                             help="Execute copy-first consolidation from the generated or supplied plan")
    carebloom_p.add_argument("--update-refs", action="store_true",
                             help="After verified copies, update known text references to copied locations")
    carebloom_p.set_defaults(func=cmd_carebloom_consolidate)

    cb_archive_p = sub.add_parser("carebloom-archive-map", aliases=["cbam"],
                                  help="Map/stage CareBloomOS assets into RuneScript project architecture and deletion-prep buckets")
    cb_archive_p.add_argument("--target-root", default=r"R:\RuneScript\Projects\CareBloomOS",
                              help="Target RuneScript project architecture root")
    cb_archive_p.add_argument("--source-root", action="append", default=None,
                              help="CareBloom source root to map; repeatable. Defaults to known roots.")
    cb_archive_p.add_argument("--dependency-root", action="append", default=None,
                              help="Text config/runtime root to scan for dependencies; repeatable.")
    cb_archive_p.add_argument("--older-than-days", type=int, default=60,
                              help="Non-dependent assets older than this are staged as deletion-prep candidates")
    cb_archive_p.add_argument("--limit", type=int, default=None,
                              help="Limit assets for a small MVP test map")
    cb_archive_p.add_argument("--plan", default=None,
                              help="Existing JSON map to execute")
    cb_archive_p.add_argument("--execute", action="store_true",
                              help="Stage mapped files by copying/verifying into the target architecture")
    cb_archive_p.set_defaults(func=cmd_carebloom_archive_map)

    profile_p = sub.add_parser("profile-migration-map", aliases=["pmm"],
                               help="Map/stage old R: user-profile contents into classified ARK destinations")
    profile_p.add_argument("--target-root", default=profile_migration.DEFAULT_TARGET_ROOT,
                           help="Staging root for migrated profile contents")
    profile_p.add_argument("--profile-root", action="append", default=None,
                           help="Profile-shaped source root to map; repeatable. Defaults to R:\\Users, R:\\Junior, R:\\Downloads.")
    profile_p.add_argument("--limit", type=int, default=None,
                           help="Limit items for a small MVP test map")
    profile_p.add_argument("--plan", default=None,
                           help="Existing JSON map to execute")
    profile_p.add_argument("--execute", action="store_true",
                           help="Stage mapped profile files by copying/verifying into the target structure")
    profile_p.set_defaults(func=cmd_profile_migration_map)

    hierarchy_p = sub.add_parser("r-hierarchy-scan", aliases=["rhs"],
                                 help="Scan R: top-level folders and suggest an ARK organization hierarchy")
    hierarchy_p.add_argument("--root", default=profile_migration.DEFAULT_SCAN_ROOT,
                             help="Root to scan, default R:")
    hierarchy_p.add_argument("--max-depth", type=int, default=2,
                             help="Depth-limited count below each top-level folder")
    hierarchy_p.set_defaults(func=cmd_r_hierarchy_scan)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    # Standing rule: no process ends in silence. Whatever happens inside
    # the command -- success, a caught failure, or an uncaught exception
    # -- this banner fires as the very last thing printed, so the shell
    # prompt reappearing is never the only signal that something finished.
    start = time.time()
    exit_code = 0
    try:
        args.func(args)
    except SystemExit as e:
        exit_code = e.code if isinstance(e.code, int) else 1
    except Exception as e:
        print(f"\n[FAILED] Unhandled error in '{args.command}': {type(e).__name__}: {e}")
        exit_code = 1
    finally:
        elapsed = round(time.time() - start, 1)
        status = "DONE" if exit_code == 0 else f"DONE (exit code {exit_code})"
        print(f"\n=== ark {args.command}: {status} — {elapsed}s ===")

    if exit_code != 0:
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
