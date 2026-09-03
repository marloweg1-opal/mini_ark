# GitHub Archival Prep

## Goal

Prepare Mini ARK for a clean future GitHub archive without accidentally publishing local state, bulky ledgers, generated caches, or private handoff material.

No repository initialization or remote push is authorized by this document.

## Recommended Repository Contents

Include:

- `ark.py`
- `core\*.py`
- `db\database.py`
- `db\schema.sql`
- `scanner\*.py`
- `tests\*.py`
- `tests\fixtures\*.json` after privacy review
- `docs\USER_GUIDE.md`
- `docs\R_DRIVE_DOCTRINE.md`
- `docs\SCOPE_AND_PROJECT_BLEED_AUDIT.md`
- `docs\GITHUB_ARCHIVAL_PREP.md`
- `index.html`
- `start_mini_ark.ps1`
- `consolidate_carebloom_assets.ps1`
- `map_carebloomos_archive.ps1`
- `migrate_r_user_profiles.ps1`
- `prep_architecture_correction.ps1`
- `config.example.json`

Exclude by default:

- `ark.sqlite`
- `ark_PRE_*.sqlite`
- `*.zip`
- `__pycache__\`
- `*.pyc`
- `logs\`
- `inventory_report.md`
- `handoffs_inbox\*.review.json` until each file is reviewed for privacy and scope
- local runtime files

## Proposed Version Policy

Use archival updates only for major changes:

- new command surface
- schema change
- new safety control
- new module type
- new ingestion path
- significant scope expansion
- substantial user guide update
- new consolidation workflow
- new archive-map workflow
- new profile-migration workflow
- release-worthy bug fix

Avoid archival updates for:

- one-off local reports
- regenerated scan output
- pycache changes
- local database changes
- temporary handoff files
- backups

## Pre-Archive Checklist

1. Create `.gitignore`.
2. Create `config.example.json` without machine-private absolute paths.
3. Decide whether handoff fixtures are safe to include.
4. Run standard-library tests.
5. Run `python ark.py doctor`.
6. Generate a short release note.
7. Only then initialize Git or connect GitHub, with explicit user approval.

## Proposed `.gitignore`

```gitignore
__pycache__/
*.pyc
*.pyo
.pytest_cache/

ark.sqlite
ark_PRE_*.sqlite
*.sqlite-journal
*.sqlite-wal
*.sqlite-shm

logs/
*.log
inventory_report.md

*.zip
*.7z
*.rar

handoffs_inbox/*.review.json
ARK_EXECUTION_DISABLED.flag
```

## Release Note Template

```text
Mini ARK vX.Y.Z

Status:
- 

Major changes:
- 

Safety notes:
- 

Validation:
- 

Not included:
- Local SQLite ledgers
- Runtime logs
- Unreviewed handoff packets
- Generated CareBloomOS staging manifests unless explicitly selected for release notes
```
