# Mini ARK Operator Handbook

This handbook is for you, the primary architect and operator.

Mini ARK is a local-first tool you can operate directly. This handbook translates its command surface into plain operating language. The guardrails are part of the architecture you directed: human review, visible reports, dry runs, approval gates, quarantine before deletion, and local control.

## The Short Version

Mini ARK is built to:

- see what is on a drive or inside a project area
- classify messy folders into likely meanings
- generate reports before taking action
- create proposals before moving anything
- copy and verify files before cleanup
- quarantine instead of permanently deleting
- preserve Project ARK scope while keeping modules like CareBloomOS contained

Mini ARK should not silently reorganize your machine. That is an intentional design constraint.

## Naming Status

Mini ARK remains the active implementation name.

Journey is the emerging product/system identity, not an active rename.

Do not rename `C:\mini_ark`, `ark.py`, `ark.cmd`, config keys, scripts, Rainmeter paths, or service references unless a deliberate migration has been approved.

Use Navigator > Manage > Naming Status when you need the current boundary returned inside the UI.

Current completion direction is governed by:

```text
C:\mini_ark\docs\CASUAL_CONGRUENCY_MVP_HANDOFF.md
```

The key order is foundation first: repair green/read-only reliability, establish capability and operation contracts, reconcile existing scripts/capabilities, then build green-check and congruency-scan.

Current icon boundary:

```text
Mini ARK active implementation icon -> C:\HEXSEED\10_ASSETS\HEXSEED_ICONS\ICO\mini_ark.ico
Journey future identity icon        -> C:\HEXSEED\10_ASSETS\HEXSEED_ICONS\ICO\journey.ico
```

`journey.ico` is held for the future identity. It should not replace the Mini ARK icon until the Journey migration is deliberately approved.

## HEXSEED Expression Framework

CareBloom is not the base ontology of HEXSEED.

CareBloom is the first mature expression profile.

The underlying structure is:

```text
functional kernel -> expression profile -> profile-specific translation
```

Not:

```text
Carestone -> reskin
```

The current neutral kernels are:

- `INTEGRATE`
- `SUSTAIN`
- `PERCEIVE`
- `MAINTAIN`
- `REGULATE`
- `ROUTE`
- `SYNCHRONIZE`

CareBloom translates those kernels into Carestones. Pokemon, Magical, Zodiac, Power Rangers, and future expressions may translate the same kernels into their own objects, roles, visual language, workflows, sounds, and interface metaphors.

Use Navigator > Manage > Expression Framework when you need the kernel/profile map returned inside the UI.

Selected foundation icon:

```text
C:\HEXSEED\10_ASSETS\HEXSEED_ICONS\ICO\HEXSEED_v4.ico
```

That is the current canonical HEXSEED icon unless you explicitly change it.

Selected CareBloomOS application icon:

```text
C:\HEXSEED\10_ASSETS\HEXSEED_ICONS\ICO\cAREBLOOM_BABY.png
```

Windows/application icon artifact:

```text
C:\HEXSEED\10_ASSETS\HEXSEED_ICONS\ICO\cAREBLOOM_BABY.ico
```

There is one CareBloomOS application icon. The bloom-within-bloom mark is the locked choice.

CareBloomOS icon audition:

```text
cAREBLOOM_BABY.png = selected CareBloomOS source art
cAREBLOOM_BABY.ico = selected CareBloomOS Windows/application icon
CareBloomOS.ico = nursery asset
CareBloomOS_v1.ico = nursery asset
CareBloomOS_v2.ico = nursery asset
```

Hold the nursery assets briefly for genuine reuse opportunities. Do not build a permanent hierarchy around them.

Canonical CareBloom stone icons are also mapped:

```text
moonstone    -> C:\HEXSEED\10_ASSETS\HEXSEED_ICONS\ICO\moonstone.ico
cloverstone  -> C:\HEXSEED\10_ASSETS\HEXSEED_ICONS\ICO\cloverstone.ico
heartstone   -> C:\HEXSEED\10_ASSETS\HEXSEED_ICONS\ICO\heartstone.ico
cloudstone   -> C:\HEXSEED\10_ASSETS\HEXSEED_ICONS\ICO\cloudstone.ico
wishstone    -> C:\HEXSEED\10_ASSETS\HEXSEED_ICONS\ICO\wishstone.ico
musicstone   -> C:\HEXSEED\10_ASSETS\HEXSEED_ICONS\ICO\musicstone.ico
```

To preview applying these to matching folders:

```powershell
powershell -ExecutionPolicy Bypass -File C:\mini_ark\work\Apply-StoneFolderIcons.ps1 -Root C:\SomeRoot -Recurse
```

To apply after review:

```powershell
powershell -ExecutionPolicy Bypass -File C:\mini_ark\work\Apply-StoneFolderIcons.ps1 -Root C:\SomeRoot -Recurse -Execute
```

## CareBloom Boundary

CareBloom is the expression of the computer experience.

Mini ARK is not CareBloom.

CareBloom can change the entire look and feel of HEXSEED, including stones appearing through another manifestation language. In a Pokemon-like manifestation, for example, Wishstone might appear as Thunderstone and Cloverstone might appear as Leafstone.

Those are surface aliases, not backend identity replacements.

Mini ARK, eventually Journey, remains the connective orchestration layer that lets the different stone functions operate together. Do not identify Mini ARK by whichever stone or manifestation language is currently most visible.

Mini ARK's visible surfaces should still match the tone HEXSEED is wearing. If HEXSEED is currently CareBloom, magical transformation anime, Pokemon-like, professor, cybernetic, or anything else, Navigator can harmonize with that expression through style, icons, motion, and flavor language.

That is expression sync, not identity replacement. The interface can wear the outfit while keeping familiar controls and stable system meaning.

## Where It Lives

```text
C:\mini_ark
```

Always start from there:

```powershell
cd C:\mini_ark
```

Use:

```powershell
.\ark.cmd
```

Do not use bare `ark.py` in PowerShell. The wrapper knows where the correct Python runtime is.

## Operating Doctrine

Mini ARK makes power visible before it becomes action. The command surface is easiest to operate in three tiers.

### Green: Look Only

These are safe to run whenever you want:

```powershell
.\ark.cmd doctor
.\ark.cmd brief
.\ark.cmd kill-status
.\ark.cmd list-reservations
.\ark.cmd status R:\
.\ark.cmd inventory --under R:\
.\ark.cmd diagnose --under R:\
.\ark.cmd placement "R:\Downloads2"
.\ark.cmd report R:\
.\ark.cmd r-hierarchy-scan --root R:\
```

They inspect, summarize, classify, or write reports. They do not move your files.

Use `placement` when the question is not "what is this?" but "does this belong here?"

Examples:

```powershell
.\ark.cmd placement "R:\Downloads2"
.\ark.cmd placement "C:\Users\Junior\Documents\Rainmeter\Skins\CareBloom\Images\moonstone.png"
.\ark.cmd placement "C:\Temp\carebloom_moonstone_badge.png"
```

The command returns current placement, likely canonical placement, confidence, reason, and recommended action. It never moves the file.

### Yellow: Plan Or Stage

These create plans, maps, or copied staging trees:

```powershell
.\consolidate_carebloom_assets.ps1
.\map_carebloomos_archive.ps1
.\migrate_r_user_profiles.ps1
.\ark.cmd propose-organization R:\
.\ark.cmd propose-media-organization R:\
.\ark.cmd find-empty R:\
```

These are still review-first. They may create local reports or copied staging output, but they should not remove originals.

### Red: Change Originals

These can alter original locations or live references:

```powershell
.\ark.cmd approve PROPOSAL_ID
.\ark.cmd apply PROPOSAL_ID
.\ark.cmd undo OP_ID
.\consolidate_carebloom_assets.ps1 -Execute -UpdateRefs
.\cleanup_r_user_profiles.ps1 -Execute -RemoveEmptyDirs
```

Run red commands only after a dry run or preview makes sense to you.

## Emergency Stop

If you want Mini ARK mutation commands blocked, create this file:

```text
C:\mini_ark\ARK_EXECUTION_DISABLED.flag
```

Check it with:

```powershell
.\ark.cmd kill-status
```

Remove the flag only when you intentionally want changes available again.

## Daily Check-In

When you are unsure where things stand, run:

```powershell
cd C:\mini_ark
.\ark.cmd doctor
.\ark.cmd brief
.\ark.cmd kill-status
```

What you are looking for:

- `doctor`: Mini ARK itself is healthy.
- `brief`: pending proposals, open loops, unreconciled events.
- `kill-status`: whether mutation commands are blocked.

If those three look sane, you are oriented.

## Open The Cockpit

Run:

```powershell
powershell -ExecutionPolicy Bypass -File C:\mini_ark\start_mini_ark.ps1
```

Then open the local URL it prints, usually:

```text
http://127.0.0.1:8788/
```

The cockpit is a control panel with copy buttons for common commands.

## mini_ark Navigator

The Navigator is the everyday control surface.

It answers two questions:

- What can Mini ARK do?
- Take me there.

The default view exposes four actions:

- `Find`: search memory/context and functionality together.
- `Launch`: open tools and workflows.
- `Guide`: task-based help that ends in an action.
- `Manage`: lower-frequency admin, tests, logs, Git, config, and docs.

Every guide entry should tell you:

- what it does
- what it touches
- how to launch it

Use the search field for words like:

```text
duplicates
migration
canon
diagnostics
CareBloom
```

Use `Ctrl + Alt + A` while the Navigator page is focused to jump back to search.

## Wishstone Asset Pipeline

Wishstone is mini_ark's asset intake and routing capability.

The everyday rule:

```text
External source files are copied into intake. They are not moved unless you approve an export/apply step.
```

The project-native folders are:

```text
C:\mini_ark\asset_pipeline\inbox
C:\mini_ark\asset_pipeline\outbox
C:\mini_ark\asset_pipeline\approved
C:\mini_ark\asset_pipeline\library
C:\mini_ark\asset_pipeline\recipes
C:\mini_ark\asset_pipeline\logs
```

Use Navigator > Tools > Wishstone Intake for the normal flow. It copies dropped, selected, or path-based source sheets into `asset_pipeline\inbox`, writes generated jobs to `asset_pipeline\outbox`, and exports only approved results to `approved\` and optionally `library\`.

Use Navigator > Manage > Wishstone Doctrine when you want the source policy, folder map, and approval boundaries returned inside the Navigator.

Wishstone intake is token-aware. Incoming items should either arrive with a token or receive a provisional token at reception. Routing follows token identity.

Asset sheet names are expected to carry intent. A name like `carebloom_orb_icon_sheet_4x7.png` or `hexseed_professor_badge_sheet.png` should be treated as project/capability token evidence before weaker inference.

## Common Recipes

### I Want To Know What Mini ARK Thinks

```powershell
cd C:\mini_ark
.\ark.cmd brief
```

Use this before deciding what to do next.

### I Want To Scan Or Classify R:

```powershell
cd C:\mini_ark
.\ark.cmd inventory --under R:\
.\ark.cmd r-hierarchy-scan --root R:\
```

This gives you organization pressure without moving anything.

### I Want A Suggested Folder Hierarchy

```powershell
cd C:\mini_ark
.\ark.cmd r-hierarchy-scan --root R:\
```

Current suggested long-term shape:

```text
R:\Projects
R:\Projects\CareBloomOS
R:\RuneScript\_ProfileMigration_Staging_Clean
R:\Media
R:\Library
R:\System_Records
R:\In_Transit
R:\In_Transit\En_Route
R:\_ark_quarantine
```

`R:\RuneScript` is a legacy wrapper pending reconciliation, not the canonical RuneScript root.

### I Want To Handle CareBloomOS Assets

Plan first:

```powershell
cd C:\mini_ark
.\consolidate_carebloom_assets.ps1
```

Copy and verify:

```powershell
.\consolidate_carebloom_assets.ps1 -Execute
```

Do not use this without review:

```powershell
.\consolidate_carebloom_assets.ps1 -Execute -UpdateRefs
```

`-UpdateRefs` edits detected Rainmeter or Wallpaper text references. That is useful, but it is a red command.

### I Want To Archive-Map CareBloomOS

Map only:

```powershell
cd C:\mini_ark
.\map_carebloomos_archive.ps1
```

Stage copied files:

```powershell
.\map_carebloomos_archive.ps1 -Execute
```

This creates:

```text
R:\Projects\CareBloomOS
```

Important: deletion-prep means review queue, not deletion.

### I Want To Clean Old R: Profile Folders

Map and stage profile assets:

```powershell
cd C:\mini_ark
.\migrate_r_user_profiles.ps1
.\migrate_r_user_profiles.ps1 -Execute
```

Preview cleanup:

```powershell
.\cleanup_r_user_profiles.ps1
```

Move verified originals into quarantine:

```powershell
.\cleanup_r_user_profiles.ps1 -Execute -RemoveEmptyDirs
```

This does not permanently delete files. It moves verified originals to:

```text
R:\_ark_quarantine
```

## Understanding Reports

Mini ARK writes reports in two main places:

```text
C:\mini_ark\docs
R:\...\00_MANIFESTS
```

Use Markdown files for reading.

Use JSON or CSV files when you need exact itemized data.

Generated reports are local working artifacts. They are normally not pushed to GitHub.

## What Happened Recently

Current notable completed work:

- CareBloomOS assets were previously staged into `R:\RuneScript\Projects\CareBloomOS`; current doctrine treats that as legacy-wrapper material and routes canonical CareBloomOS project material toward `R:\Projects\CareBloomOS`.
- Older non-dependent CareBloomOS assets were staged into deletion-review buckets.
- R: user-profile assets were cleaned into `R:\RuneScript\_ProfileMigration_Staging_Clean`.
- Verified old profile-source originals were moved into `R:\_ark_quarantine`.
- GitHub archive is live at `https://github.com/marloweg1-opal/mini_ark`.

## What GitHub Is For

GitHub is not the live ledger.

GitHub should contain:

- source code
- docs
- scripts
- tests
- examples that are safe to publish

GitHub should not contain:

- `ark.sqlite`
- generated scan maps
- cleanup reports
- local logs
- private handoffs
- private conversation fixtures
- backup zips
- machine-local `config.json`

Update GitHub only for durable milestones:

- new command
- new workflow
- major handbook update
- schema change
- safety rule change
- release-worthy bug fix

Do not update GitHub every time you run a scan.

## How To Ask Mini ARK For Help

Use this shape:

```text
Mini ARK, dry-run this first:
<what folder or workflow>
Show me what would move, what would be skipped, what would be deleted, and where the report is.
```

Or:

```text
Mini ARK, run a green check:
doctor, brief, kill-status, and current R: hierarchy scan.
```

Or:

```text
Mini ARK, where does this belong?
<path>
```

Or:

```text
Mini ARK, explain this report in plain English:
<report path>
```

## What Not To Do Casually

Do not casually run:

```powershell
.\ark.cmd apply PROPOSAL_ID
.\consolidate_carebloom_assets.ps1 -Execute -UpdateRefs
.\cleanup_r_user_profiles.ps1 -Execute -RemoveEmptyDirs
```

Run previews first.

Do not delete quarantine folders just because they look redundant. Quarantine is the rollback shelf.

Do not treat `R:\Users` residue as ordinary project material. Much of it is Windows profile machinery.

## Glossary

`Project ARK`: the parent project and operating context.

`Mini ARK`: the local tool/cockpit/steward that helps inspect, classify, plan, stage, and safely apply changes.

`CareBloomOS`: a flagship subsystem inside ARK, not the whole project.

`Ledger`: Mini ARK's local SQLite memory of scans, proposals, reservations, and operations.

`Proposal`: a suggested action. It is not an action yet.

`Preview`: a dry run of what an action would do.

`Stage`: copy files into a planned destination and verify them.

`Quarantine`: a reversible holding area for things moved out of the way.

`Deletion-prep`: a review bucket. It does not mean deletion happened.

## Operating Rule

When you need orientation, run green commands first.

When the output matches your intent, run yellow commands.

When a red command is needed, get a dry-run summary first.

That is the intended operating sequence.
