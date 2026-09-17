# Corestone Token Registry

Corestone tokens are stable identity packets.

The canonical system token is:

```text
corestone
```

`opalstone` is valid identity language, but it resolves to `corestone` for architectural, infrastructural, operational, and registry-related work.

```text
opalstone -> corestone
```

In plain language: Opalstone is the person/identity. Corestone is the capacity/role that identity is serving inside the system.

A token can be:

- a system identity, like `corestone`
- a stone identity, like `wishstone`, `cloverstone`, `moonstone`, or `heartstone`
- a project identity, like `carebloomos`
- a customization layer, such as an icon, accent color, wallpaper, surface label, or manifestation profile
- a routing handle, such as the canonical place a project lives or the inbox/outbox a workflow uses
- a capability boundary, such as "Wishstone owns acquisition and asset routing"

The point is not to make the user memorize names. The point is to let Corestone resolve plain language and old names into stable behavior.

For example:

```text
mini_ark
mini ark
opalstone
```

all resolve to:

```text
corestone
```

and:

```text
asset ark
wishstone intake
```

resolve to:

```text
wishstone
```

## Reception Rule

Everything that enters Mini ARK should be token-aware.

An incoming item either:

- carries an existing token, or
- receives a provisional token at reception.

Token evidence may come from:

- source document name
- filename
- folder context
- manifest
- metadata
- known project route
- user-provided family or label
- prior registry knowledge
- conversation context

Source document name and filename are often deliberate operator intent, not incidental trivia. If a source asset sheet is named for `carebloom`, `hexseed`, `moonstone`, `cloverstone`, `wishstone`, or another known project/capability, treat that as primary token evidence before falling back to weaker inference.

If the evidence is weak, the token should be provisional and reviewable.

Do not treat an item as meaningfully anonymous just because its token is not obvious on first contact.

The practical rule:

```text
reception -> token recognition/provisional token -> routing/placement
```

Routing follows identity. It does not replace identity.

## What Tokens Are Not

Tokens are not just decorative labels.

An icon can belong to a token, but the token itself is the whole identity contract: aliases, capability ownership, routes, safety rules, and visual hints.

## First Registry

The first machine-readable registry lives at:

```text
C:\mini_ark\config\project_tokens.json
```

The command surface is:

```text
.\ark.cmd tokens
.\ark.cmd tokens wishstone
.\ark.cmd tokens mini_ark
.\ark.cmd tokens carebloom
.\ark.cmd routes
```

The Navigator surface is:

```text
Manage -> Token Registry
```

## Doctrine Locked Here

The registry starts with the current Corestone doctrine:

- never delete a folder solely because it is empty
- detect and propose first
- execute only through approved, reversible operations
- preserve source provenance when grouping or routing assets
- continuously pursue user computer congruence by the least disruptive path available

## Routes And Representations

A route is a canonical place Corestone can reason about operationally.

Examples:

```text
C:\mini_ark\asset_pipeline\inbox
R:\Projects\CareBloomOS
R:\Media\CareBloomOS
```

A representation is a useful view of something. It may be a shortcut, project portal, manifest, Navigator surface, or visual layer.

Representations are allowed to help the user find and work with things. They should not silently become the source of truth.

The locked rule is:

```text
Canonical roots are the source of truth.
Representations are useful views, shortcuts, manifests, or surfaces.
```

The placement rule is:

```text
Files live in their natural canonical home first.
Specificity is added through representations.
```

That means a file should usually go where it naturally belongs by type, source, project, or operational role. Then Corestone can add more specific meaning through shortcuts, manifests, tags, library indexes, project views, or Navigator surfaces.

So a CareBloomOS media asset can physically live in a media-root or canonical project-root while still appearing in the relevant carestone view. The view is the access layer; the canonical route remains the source of truth.

## Ambient Congruence

Corestone/HEXSEED should not ask whether the user wants their computer and files organized. The answer is yes.

That does not mean "always mutate everything."

The default behavior is continuous stewardship with graduated autonomy:

```text
ALWAYS OBSERVE
    -> safe + reversible + high confidence + low cost?
        -> auto-apply quietly
        -> receipt + rollback path
    -> ambiguous / destructive / expensive / disruptive?
        -> defer or ask
```

Corestone is always aware, not always busy.

Resource doctrine:

```text
foreground user activity -> protect responsiveness first
heavy compute active -> throttle or sleep
idle / low pressure -> expand housekeeping
urgent integrity issue -> interrupt only when necessary
```

Auto-apply examples:

- deterministic naming normalization
- index and manifest updates
- verified routing with unambiguous destinations
- broken-reference repair where the destination is unambiguous
- non-destructive organizational maintenance
- report generation
- safe metadata normalization

Do not auto-apply:

- deletion
- folder deletion
- ambiguous rename
- semantic merges
- system or app-managed path changes
- destructive dedupe
- high-cost scans during active workload
- changes with unclear ownership or destination

Actual mutations still require the safer path:

```text
proposal -> approval -> receipt -> rollback path
```

So Cloverstone can keep date indexes, naming previews, drift signals, and taxonomy hints warming in the background. It should not turn every one of those into a new button unless the user needs a manual override or inspection surface.

Prompts are for real judgment, not routine housekeeping.

## Cloverstone Naming Doctrine

Cloverstone names according to identity, not merely whatever metadata happens to be available.

The filename rule is:

```text
what_it_is -> useful context -> distinguishing identity -> yyyy-mm-dd
```

Dates are optional. Use a date in the filename only when chronology helps identify, sort, or distinguish the resource: photos, reports, exports, receipts, builds, scans, snapshots, and similar time-bound artifacts.

Dates that are merely acquisition facts belong in provenance:

```text
ruby_3.4.5_installer.exe
downloaded: 2026-09-09
source: ruby-lang.org
```

Do not name software/packages by download date unless the date is part of the artifact identity.

Date safety:

```text
YYYY-MM-DD -> accepted canonical filename date
unambiguous DD-MM-YYYY or MM-DD-YYYY -> normalized to YYYY-MM-DD
ambiguous DD/MM/YYYY vs MM/DD/YYYY -> metadata evidence only
downloaded/created/modified dates -> provenance unless semantically meaningful
```

Filename tokens should earn their place. If removing a token would not make the resource appreciably harder to identify, find, sort, or distinguish, that token probably belongs in metadata instead.

Cloverstone also protects against:

- reserved Windows stems such as `con`, `prn`, `aux`, `nul`, `com1`, and `lpt1`
- illegal filename characters
- temporary or partial-download files
- path length pressure
- alias leakage, by emitting canonical tokens such as `carebloomos`
- project-token sprawl, by moving extra associations into representations/provenance
