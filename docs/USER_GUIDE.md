# Mini ARK User Guide

Mini ARK lives at:

```text
C:\mini_ark
```

Its job is to help Project ARK observe, understand, report, propose, and carefully apply changes. It is not meant to silently reorganize your machine.

## Start Mini ARK

Run:

```powershell
powershell -ExecutionPolicy Bypass -File C:\mini_ark\start_mini_ark.ps1
```

The script prints a local URL, usually:

```text
http://127.0.0.1:8787/
```

Open that URL in a browser.

If the local server is not needed, open this file directly:

```text
C:\mini_ark\index.html
```

## Daily Controls

Use these first:

```powershell
cd C:\mini_ark
.\ark.cmd doctor
.\ark.cmd brief
.\ark.cmd kill-status
```

In an Administrator PowerShell window, use `.\ark.cmd` rather than `ark.py` or `python ark.py`. The wrapper points to the installed Python runtime directly.

What they mean:

- `doctor`: checks whether Mini ARK itself is healthy.
- `brief`: shows current ledger pressure, open loops, and pending proposals.
- `kill-status`: confirms whether mutation commands are blocked.

## Read-Only Work

These commands observe and report:

```powershell
.\ark.cmd status R:\
.\ark.cmd inventory --under R:\
.\ark.cmd report R:\
.\ark.cmd diagnose --under R:\
```

Use read-only commands freely. They may update Mini ARK's own ledger or reports, but they should not move, rename, quarantine, or delete project files.

## Proposal Work

These commands create proposed actions, not file changes:

```powershell
.\ark.cmd propose-organization R:\
.\ark.cmd propose-media-organization R:\
.\ark.cmd find-empty R:\
```

After a proposal exists:

```powershell
.\ark.cmd brief
.\ark.cmd list-items PROPOSAL_ID
.\ark.cmd skip-item ITEM_ID
```

Review before approval. Skip anything that should stay put.

## Approval-Gated Work

These commands can lead to file operations:

```powershell
.\ark.cmd approve PROPOSAL_ID
.\ark.cmd apply PROPOSAL_ID --preview
.\ark.cmd apply PROPOSAL_ID
.\ark.cmd undo OP_ID
```

Rule of thumb:

1. Run `list-items`.
2. Skip questionable items.
3. Run `apply --preview`.
4. Only then run real `apply`.

## Emergency Stop

Create this file to block mutation commands:

```text
C:\mini_ark\ARK_EXECUTION_DISABLED.flag
```

Remove it only when you intentionally want mutation commands available again.

## Project Scope

Project ARK is the parent system.

Mini ARK is the cockpit and stewarding engine.

CareBloomOS is a flagship subsystem inside ARK, not the parent identity.

Other modules can include Ark OS, HEXSEED, Welfare Witchcraft, media operations, and future persona systems.

## Current Known State

As of the current startup pass:

- Mini ARK home exists at `C:\mini_ark`.
- Ledger exists at `C:\mini_ark\ark.sqlite`.
- Schema is readable at version 1.
- Doctor reports 8 scans in history.
- Doctor warning: 6 handoffs await review.
- Brief reports 8 pending proposals.
- Kill switch is not set.

## What To Do Next

1. Review handoffs.
2. Keep CareBloomOS contained as one module lane.
3. Generate an ARK-first status report.
4. Preview proposals before any apply.
5. Prepare GitHub archival only after the docs, safety rules, and ignore policy are clean.

## One-Step Architecture Prep

Use this instead of running the reservation and protected-item cleanup commands one at a time:

```powershell
cd C:\mini_ark
.\prep_architecture_correction.ps1
```

That is dry-run mode.

To actually update Mini ARK's ledger so protected proposal items are marked skipped:

```powershell
.\prep_architecture_correction.ps1 -Execute
```

This only updates Mini ARK's ledger. It does not move, delete, quarantine, or shortcut files.

## One-Step CareBloom Consolidation MVP

Create a consolidation plan:

```powershell
cd C:\mini_ark
.\consolidate_carebloom_assets.ps1
```

Run a small copy-first test:

```powershell
.\consolidate_carebloom_assets.ps1 -Execute -Limit 25
```

Run full copy-first consolidation:

```powershell
.\consolidate_carebloom_assets.ps1 -Execute
```

Run full copy-first consolidation and update known text references after copied files verify:

```powershell
.\consolidate_carebloom_assets.ps1 -Execute -UpdateRefs
```

CareBloom consolidation does not stop Rainmeter or Wallpaper Engine. MVP execution copies first, verifies copied size, updates only known text references when requested, and leaves originals in place.

Reference updates are the approval point. They edit detected Rainmeter/Wallpaper text files after the copies verify. Do not use `-UpdateRefs` until the generated plan's dependency reference section looks right.

## One-Step CareBloomOS Archive Map

Create a map only:

```powershell
cd C:\mini_ark
.\map_carebloomos_archive.ps1
```

Stage the mapped files into the RuneScript CareBloomOS archive structure:

```powershell
.\map_carebloomos_archive.ps1 -Execute
```

Default target:

```text
R:\RuneScript\Projects\CareBloomOS
```

Default buckets:

- `00_MANIFESTS`: generated JSON, CSV, and Markdown reports.
- `01_ACTIVE_RECENT_NONDEPENDENT`: non-dependent files changed within the last 60 days.
- `02_DEPENDENCY_HOLD`: files with detected Rainmeter/Wallpaper or text references.
- `90_ARCHIVE_PREP_DELETION_CANDIDATES_OLDER_THAN_60_DAYS`: non-dependent files older than 60 days, staged for deletion review.

This operation copies and verifies. It does not delete originals, stop Rainmeter, stop Wallpaper Engine, or rewrite live paths.

Most recent full run:

- Target: `R:\RuneScript\Projects\CareBloomOS`
- Assets staged: 5957
- Failed: 0
- Dependency holds: 79
- Active recent non-dependent: 760
- Deletion-review candidates: 5118
- Files deleted: 0
- Map: `R:\RuneScript\Projects\CareBloomOS\00_MANIFESTS\CAREBLOOM_ARCHIVE_MAP_2026-09-03_052038.json`
- Stage result: `R:\RuneScript\Projects\CareBloomOS\00_MANIFESTS\CAREBLOOM_ARCHIVE_STAGE_RESULT_2026-09-03_052051.json`

## One-Step R: User Profile Migration

Create a cleaned map and R: hierarchy report:

```powershell
cd C:\mini_ark
.\migrate_r_user_profiles.ps1
```

Stage cleaned user-profile assets by copy/verify:

```powershell
.\migrate_r_user_profiles.ps1 -Execute
```

Default source roots:

- `R:\Users`
- `R:\Junior`
- `R:\Downloads`

Default target:

```text
R:\RuneScript\_ProfileMigration_Staging_Clean
```

Profile migration skips Windows profile machinery by default: `Default`, `Default User`, `defaultuser*`, `All Users`, `AppData`, and known system/link folders. That keeps the migration focused on actual user files, documents, media, reference material, and project-like assets.

Most recent cleaned staging run:

- Map: `C:\mini_ark\docs\R_PROFILE_MIGRATION_MAP_2026-09-03_100041.json`
- Stage result: `R:\RuneScript\_ProfileMigration_Staging_Clean\00_MANIFESTS\R_PROFILE_MIGRATION_STAGE_RESULT_2026-09-03_100145.json`
- Hierarchy report: `C:\mini_ark\docs\R_HIERARCHY_SCAN_2026-09-03_100405.md`
- Items mapped: 5108
- Copied/verified: 5103
- Failed: 5
- Files deleted: 0

The 5 failures are unavailable OneDrive cloud placeholders. Start/sync OneDrive and rerun the same plan if those files matter.

## Update Rhythm

Do not create new archive snapshots for routine local state changes.

Create a durable update only when one of these changes happens:

- major command or control surface update
- scope expansion
- new tool or module type
- schema change
- safety rule change
- release-worthy bug fix
- substantial handbook change
