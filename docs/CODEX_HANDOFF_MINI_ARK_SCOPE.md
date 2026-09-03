# Codex Handoff: Mini ARK Scope Correction

## Current Task

Bring Mini ARK up and running from its real home:

```text
C:\mini_ark
```

The user corrected project drift: this work is about Project ARK and Mini ARK. CareBloomOS is a flagship ARK module, not the enclosing project.

## Current Verified State

- `C:\mini_ark` exists.
- `ark.py` is the main CLI.
- `config.json` points to `C:\mini_ark\ark.sqlite`.
- `python ark.py doctor` runs.
- Doctor result: ledger exists, schema columns are current, schema v1 is readable, 8 scans exist, canonical path uniqueness is enforced.
- Doctor warning: 6 handoffs require review.
- `python ark.py brief` runs when allowed to write to the Mini ARK ledger.
- Brief result: 457644 unreconciled events, 0 open loops, 8 pending proposals.
- `python ark.py kill-status` reports the kill switch is not set.
- `pytest` is not installed.
- `python -m unittest discover -s tests -v` runs 22 tests; 21 pass and 1 errors because the test writes to `C:\Users\Junior\Downloads\CareBloom_Codex_Intake\conversation_ingest_test_review.json`, which is blocked in the current sandbox.

## Files Added This Turn

- `C:\mini_ark\index.html`
- `C:\mini_ark\start_mini_ark.ps1`
- `C:\mini_ark\docs\USER_GUIDE.md`
- `C:\mini_ark\docs\SCOPE_AND_PROJECT_BLEED_AUDIT.md`
- `C:\mini_ark\docs\CODEX_HANDOFF_MINI_ARK_SCOPE.md`
- `C:\mini_ark\docs\GITHUB_ARCHIVAL_PREP.md`
- `C:\mini_ark\docs\MINI_ARK_STATUS_2026-09-02.md`
- `C:\mini_ark\.gitignore`
- `C:\mini_ark\config.example.json`

## Immediate Next Steps

1. Run `C:\mini_ark\start_mini_ark.ps1` with permission to write its log.
2. Open the printed local URL.
3. Add an `ark.py cockpit` command so the CLI can print launch instructions.
4. Review the 6 handoff files in `C:\mini_ark\handoffs_inbox`.
5. Refresh ARK handoff language so future sessions start from Mini ARK stabilization.
6. Prepare GitHub archival with `.gitignore` before repository initialization.

## Validation Completed

- `python ark.py cockpit`: pass.
- `python ark.py doctor`: pass with one expected warning for 6 handoffs awaiting review.
- `python ark.py brief`: pass.
- `python -m unittest discover -s tests -v`: 22 tests pass.
- `http://127.0.0.1:8788/`: returned HTTP 200.

## Scope Rules For Next Agent

- Do not make CareBloomOS the parent project.
- Do not apply proposals without explicit user approval.
- Do not create backup chains.
- Do not initialize Git or push to GitHub without explicit user approval.
- Treat SQLite databases, pycache, zips, logs, and local runtime artifacts as archival exclusions unless the user explicitly says otherwise.
- Major updates and scope expansions should create clear release notes. Minor doc edits do not need ceremony.

## Suggested Next Command

```powershell
cd C:\mini_ark
powershell -ExecutionPolicy Bypass -File .\start_mini_ark.ps1
```

## CareBloom Consolidation MVP Added

New files/commands:

- `C:\mini_ark\core\carebloom_consolidation.py`
- `C:\mini_ark\consolidate_carebloom_assets.ps1`
- `C:\mini_ark\map_carebloomos_archive.ps1`
- `C:\mini_ark\migrate_r_user_profiles.ps1`
- `.\ark.cmd carebloom-consolidate`
- `.\ark.cmd carebloom-archive-map`
- `.\ark.cmd profile-migration-map`
- `.\ark.cmd r-hierarchy-scan`

Design:

- Plan first by default.
- Copy first on execute.
- Verify copied file size.
- Optionally update known text references with `-UpdateRefs` / `--update-refs`.
- Leave originals in place during MVP.
- Do not stop Rainmeter or Wallpaper Engine.

Recommended first run:

```powershell
cd C:\mini_ark
.\consolidate_carebloom_assets.ps1
```

Recommended first execute test:

```powershell
.\consolidate_carebloom_assets.ps1 -Execute -Limit 25
```

## CareBloomOS Archive Map MVP Added

New command:

```powershell
cd C:\mini_ark
.\map_carebloomos_archive.ps1 -Execute
```

Target structure:

```text
R:\RuneScript\Projects\CareBloomOS
```

Full staging completed on 2026-09-03:

- Assets mapped/staged: 5957
- Failed: 0
- Dependency holds: 79
- Active recent non-dependent: 760
- Deletion-review candidates older than 60 days: 5118
- Files deleted: 0
- Map: `R:\RuneScript\Projects\CareBloomOS\00_MANIFESTS\CAREBLOOM_ARCHIVE_MAP_2026-09-03_052038.json`
- Stage result: `R:\RuneScript\Projects\CareBloomOS\00_MANIFESTS\CAREBLOOM_ARCHIVE_STAGE_RESULT_2026-09-03_052051.json`

Safety rule: deletion-review staging is not deletion authorization. Do not delete originals unless the user gives a separate explicit approval after manifest review.

## R: User Profile Migration MVP Added

New command:

```powershell
cd C:\mini_ark
.\migrate_r_user_profiles.ps1 -Execute
```

Cleaned staging target:

```text
R:\RuneScript\_ProfileMigration_Staging_Clean
```

Full cleaned staging completed on 2026-09-03:

- Items mapped: 5108
- Copied/verified: 5103
- Failed: 5
- Files deleted: 0
- Map: `C:\mini_ark\docs\R_PROFILE_MIGRATION_MAP_2026-09-03_100041.json`
- Stage result: `R:\RuneScript\_ProfileMigration_Staging_Clean\00_MANIFESTS\R_PROFILE_MIGRATION_STAGE_RESULT_2026-09-03_100145.json`
- R: hierarchy report: `C:\mini_ark\docs\R_HIERARCHY_SCAN_2026-09-03_100405.md`

The first unrestricted profile pass copied 124294 files and had 12759 failures because it included Windows `AppData`/system profile cache residue. It is superseded by the cleaned pass. Use the cleaned staging root for review.

Safety rule: do not remove `R:\Users`, `R:\Junior`, or `R:\Downloads` contents until the cleaned staging result is reviewed and OneDrive placeholder failures are either synced or intentionally skipped.

Approved cleanup completed after review:

- Cleanup report: `C:\mini_ark\docs\R_PROFILE_CLEANUP_2026-09-03_115901.json`
- Quarantine root: `R:\_ark_quarantine\R_Profile_Source_Removals_2026-09-03_115901`
- Planned moves: 4999
- Moved to quarantine: 4987
- Skipped: 109
- Failed: 12
- Files permanently deleted: 0

The remaining `R:\Users` population is mostly Windows/profile residue. Do not delete it without a separate explicit approval for system/profile residue cleanup.
