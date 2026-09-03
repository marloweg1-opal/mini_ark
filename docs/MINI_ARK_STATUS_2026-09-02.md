# Mini ARK Status - 2026-09-02

## Summary

Mini ARK is up and running from:

```text
C:\mini_ark
```

Local cockpit URL from the verified run:

```text
http://127.0.0.1:8788/
```

## Verified Working

- `python ark.py cockpit`
- `python ark.py doctor`
- `python ark.py brief`
- `python ark.py kill-status`
- `python -m unittest discover -s tests -v`
- local HTTP serving for `index.html`

## Test Result

Standard-library test suite:

```text
Ran 22 tests
OK
```

The earlier failing test was caused by a hard-coded Downloads output path. It now writes to the system temp directory.

## Doctor Result

Healthy:

- Ledger file exists.
- Schema columns are up to date.
- Schema version readable: v1.
- Scan history present: 8 scans.
- `files.canonical_path` uniqueness is enforced on disk.
- Open loops: 0.

Needs review:

- Handoffs awaiting review: 6.

## Brief Result

- Unreconciled events: 457644.
- Open loops: 0.
- Pending proposals: 8.

Pending proposal types:

- Video project-portal reference.
- Archives project-portal reference.
- Code project-portal reference.
- Data project-portal reference.
- Documents project-portal reference.
- Images project-portal reference.
- Design project-portal reference.
- Empty-folder quarantine proposal.

No proposal has been applied in this pass.

## Scope Correction

Project ARK is the parent.

Mini ARK is the cockpit and stewardship engine.

CareBloomOS is a flagship subsystem within ARK, not the parent project identity.

## Files Updated Or Added

- `C:\mini_ark\index.html`
- `C:\mini_ark\start_mini_ark.ps1`
- `C:\mini_ark\ark.py`
- `C:\mini_ark\.gitignore`
- `C:\mini_ark\config.example.json`
- `C:\mini_ark\tests\test_conversation_ingest.py`
- `C:\mini_ark\docs\USER_GUIDE.md`
- `C:\mini_ark\docs\SCOPE_AND_PROJECT_BLEED_AUDIT.md`
- `C:\mini_ark\docs\CODEX_HANDOFF_MINI_ARK_SCOPE.md`
- `C:\mini_ark\docs\GITHUB_ARCHIVAL_PREP.md`
- `C:\mini_ark\docs\MINI_ARK_STATUS_2026-09-02.md`

## Next Work

1. Review and classify handoff inbox files.
2. Refresh ARK handoff language so Project ARK and Mini ARK stay the starting point.
3. Preview pending proposals only; do not apply without explicit approval.
4. Prepare GitHub archival after privacy review and repository approval.

## 2026-09-03 Update

CareBloom consolidation MVP is implemented.

- Command: `.\consolidate_carebloom_assets.ps1`
- CLI: `.\ark.cmd carebloom-consolidate`
- Full corrected plan: `C:\mini_ark\docs\CAREBLOOM_CONSOLIDATION_PLAN_2026-09-03_042934.json`
- Full corrected result: `C:\mini_ark\docs\CAREBLOOM_CONSOLIDATION_RESULT_2026-09-03_042934.json`
- Assets verified/copied: 5957
- Failed: 0
- Dependency-bearing assets in corrected plan: 79
- Exact dependency references in corrected plan: 144
- Originals left in place: yes
- Rainmeter stopped: no
- Wallpaper Engine stopped: no

Reference updates are implemented but not run. They require explicit approval through `-UpdateRefs`.

## 2026-09-03 CareBloomOS Archive Map Update

CareBloomOS archive-map MVP is implemented and fully staged.

- Command: `.\map_carebloomos_archive.ps1`
- CLI: `.\ark.cmd carebloom-archive-map`
- Target: `R:\RuneScript\Projects\CareBloomOS`
- Full map: `R:\RuneScript\Projects\CareBloomOS\00_MANIFESTS\CAREBLOOM_ARCHIVE_MAP_2026-09-03_052038.json`
- Full stage result: `R:\RuneScript\Projects\CareBloomOS\00_MANIFESTS\CAREBLOOM_ARCHIVE_STAGE_RESULT_2026-09-03_052051.json`
- Assets staged/copied: 5957
- Failed: 0
- Dependency holds: 79
- Active recent non-dependent: 760
- Deletion-review candidates older than 60 days: 5118
- Files deleted: 0

Deletion-review candidates are staged copies only. No original file deletion is authorized or performed by this MVP.

## 2026-09-03 R: Profile Migration Update

R: user-profile migration MVP is implemented and cleaned staging completed.

- Command: `.\migrate_r_user_profiles.ps1`
- CLI: `.\ark.cmd profile-migration-map`
- Hierarchy CLI: `.\ark.cmd r-hierarchy-scan`
- Target: `R:\RuneScript\_ProfileMigration_Staging_Clean`
- Map: `C:\mini_ark\docs\R_PROFILE_MIGRATION_MAP_2026-09-03_100041.json`
- Stage result: `R:\RuneScript\_ProfileMigration_Staging_Clean\00_MANIFESTS\R_PROFILE_MIGRATION_STAGE_RESULT_2026-09-03_100145.json`
- R: hierarchy report: `C:\mini_ark\docs\R_HIERARCHY_SCAN_2026-09-03_100405.md`
- Items mapped: 5108
- Copied/verified: 5103
- Failed: 5
- Files deleted: 0

The 5 failures are unavailable OneDrive placeholder files. No profile roots were removed.

## 2026-09-03 R: Profile Cleanup Update

Approved reversible profile-source cleanup completed.

- Command: `.\cleanup_r_user_profiles.ps1 -Execute -RemoveEmptyDirs`
- Cleanup report: `C:\mini_ark\docs\R_PROFILE_CLEANUP_2026-09-03_115901.json`
- Quarantine root: `R:\_ark_quarantine\R_Profile_Source_Removals_2026-09-03_115901`
- Planned moves: 4999
- Moved to quarantine: 4987
- Skipped: 109
- Failed: 12
- Files permanently deleted: 0

Remaining profile-source state:

- `R:\Junior`: one `desktop.ini` residue file under `Documents`.
- `R:\Downloads`: one `desktop.ini` residue file.
- `R:\Users`: Windows/profile residue remains, including default profiles, AppData/system cache material, profile metadata, unavailable OneDrive placeholders, and access-denied public desktop shortcuts.
