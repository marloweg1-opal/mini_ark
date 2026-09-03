# Moonstone Congruence + Dormancy Intelligence -- Handoff Brief

**Status: FUTURE BUILD. Not started as of this writing.** Saved here as a
handoff brief for a future session, per the same "sticky note, not an
active build task" discipline used for the manifestation model in
R_DRIVE_DOCTRINE.md Section 14.

---

## Claude's evidence-gap notes (read before starting)

Several evidence sources this brief calls for do not exist in Mini ARK
yet -- not a small gap, a structural one. Before building anything here,
resolve these, or scope the first increment to avoid needing them:

- **`last_executed_at`** -- Mini ARK has never tracked script execution.
  It knows files exist; it has no concept of a script having *run*.
- **`last_referenced_at`** / "configuration explicitly points to the
  object" -- exists narrowly via `file_dependents` (manually registered
  only, see core/apply.py from the Rainmeter/CareBloomOS work). No
  general config/manifest scanner exists.
- **Automation congruence** (Section 13 below) -- scheduled tasks,
  startup entries, watchers -- zero visibility today. Mini ARK only
  ever looks at files.
- **Functional redundancy** (Section 10, "two duplicate finders...
  requires semantic/code-level analysis") -- needs actual code
  comprehension, not file metadata. A materially harder problem than
  anything built in Mini ARK so far.

The brief itself (Section 6-7) is explicit that filesystem timestamps
alone are weak evidence. Building "dormancy detection" using *only*
what Mini ARK currently has would mean either quietly degrading to
that exact weak signal, or inventing signals that don't really exist.
Neither is honest, and would violate the document's own stated
philosophy (Section 21: "Perceive without possessing").

**A genuinely buildable first increment, when this gets picked up:**
- The five-class lifecycle model (Section 4), extending `core/classify.py`
  -- reusing the existing Confirmed/Strongly_inferred/Tentative/Unknown
  tiers already built and tested.
- A participation model built honestly from real data: `modified_at`,
  `last_seen_at`, hash-based identical-duplicate detection, and real
  `file_dependents` where registered -- each finding explicitly
  labeled with which evidence tier is MISSING (execution history,
  config references), never silently omitted.
- Identical-duplicate vs. everything else in Section 10 (version
  variant, superseded, and functional redundancy all need signals
  that don't exist yet).
- Structured JSON findings per Section 19, entirely read-only --
  findings only, no auto-generated proposals, consistent with every
  other module in this codebase (organizer.py, pruning.py never
  mutate; only apply.py does, and only after explicit approval).

---

## Original handoff brief follows, unedited

### Mission

Build the **Moonstone Congruence intelligence layer** for Mini ARK.

This system should detect:

* dormancy
* redundancy
* residue
* supersession
* misplaced content
* orphaned content
* unusual automation
* lifecycle inconsistencies

without treating age, inactivity, duplication, or unusual placement as automatic evidence that something should be deleted.

Moonstone's purpose is not cleanup.

Moonstone's purpose is:

# **discernment before intervention.**

Her governing question is:

> **Given what this thing is, what would continued participation in HEXSEED reasonably look like?**

---

# 1. Existing Architecture

Mini ARK already provides a shared execution and safety layer.

Current capabilities exposed through `ark.py` include:

* filesystem scanning
* inventory/classification
* duplicate checking
* duplicate resolution
* case-drift diagnosis
* case-drift resolution
* proposals
* per-item review
* approval
* preview
* apply
* protected/reserved paths
* dependency tracking
* undo
* kill switch
* reporting

Do not build a second execution framework.

Moonstone should produce **findings and proposals** that can eventually flow into the existing Mini ARK review/approval machinery.

The current CLI is the implementation baseline.

---

# 2. Carestone Labor Boundary

## Moonstone = Congruence

Moonstone determines:

* whether something belongs
* whether something is still participating
* whether something has drifted
* whether multiple things appear to occupy the same role
* whether something is superseded
* whether system state matches reality
* whether hidden automation is behaving as expected

Moonstone does **not** primarily maintain the contents of an already-correct folder.

That belongs to Cloverstone.

## Cloverstone = Care

Once something is confirmed to belong in a location, Cloverstone owns:

* local structure
* naming
* maintenance
* repair
* upkeep
* dependency care
* approved pruning
* organization within that location

Canonical handoff:

> **Moonstone decides whether something belongs.
> Cloverstone tends it once it gets there.**

Do not create duplicate maintenance behavior inside Moonstone.

---

# 3. Moonstone Observes Everything

Moonstone may observe and classify all scanned content.

However:

# **Not everything is eligible for the same dormancy logic.**

Age must never be treated as a universal cleanup criterion.

Example:

A character reference PNG untouched for 14 months may still be perfectly valid.

A one-off PowerShell migration script untouched for 14 months may legitimately deserve review.

These are not equivalent kinds of silence.

---

# 4. Required Eligibility Classes

Every relevant object should be assigned one of the following broad lifecycle classes before dormancy conclusions are generated.

## A. PROTECTED / CANONICAL

Examples:

* canonical project documentation
* lore source material
* legal records
* agreements
* irreplaceable reference material
* approved master assets
* source-of-truth configuration
* explicitly protected/reserved files

Behavior:

* age alone must never trigger cleanup
* lack of recent access is expected
* redundancy may still be reported
* placement drift may still be reported
* corruption/broken-reference findings may still be reported
* destructive recommendations require exceptional confidence and explicit review

Default recommendation:

`KEEP`

or:

`REVIEW ONLY`

---

## B. PROJECT MATERIAL

Examples:

* PNG assets
* wallpapers
* concept art
* character sheets
* project documents
* design references
* working source files
* project exports
* project-specific media

Behavior:

Age is **weak evidence**.

Prioritize:

* project ownership
* references
* supersession
* duplication
* canonical status
* placement
* version relationships
* whether the file is clearly temporary or generated residue

A project asset unused for 180 days should not automatically become a dormancy candidate.

Possible statuses:

* ACTIVE PROJECT MATERIAL
* INACTIVE REFERENCE
* SUPERSEDED
* DUPLICATE
* MISPLACED
* ARCHIVAL CANDIDATE
* UNKNOWN

---

## C. OPERATIONAL INFRASTRUCTURE

Examples:

* Python scripts
* PowerShell scripts
* Lua helpers
* executables
* utilities
* scheduled tasks
* startup items
* automation helpers
* maintenance tooling
* conversion tools
* watchers
* one-off migration scripts

Behavior:

Dormancy is much more meaningful.

A long period without execution or reference may justify review.

Possible statuses:

* ACTIVE
* INFREQUENT BUT VALID
* DORMANT
* SUPERSEDED
* ORPHANED
* REDUNDANT
* MISCONFIGURED
* UNKNOWN

This is the strongest initial target for Moonstone dormancy analysis.

---

## D. TRANSIENT / RESIDUE

Examples:

* temporary exports
* staging files
* abandoned installer packages
* cache-like artifacts
* failed conversion leftovers
* duplicate downloads
* temporary unpack directories
* clearly generated intermediates
* abandoned scratch output

Behavior:

Dormancy is **strong evidence**.

These may use shorter thresholds than operational infrastructure.

Still:

Do not auto-delete.

Generate review candidates.

Possible recommendation:

* quarantine
* archive
* remove after approval
* keep
* ignore

---

## E. UNKNOWN

If Moonstone cannot confidently determine what something is:

# do not invent a lifecycle judgment.

Return:

`UNKNOWN / CLASSIFICATION REQUIRED`

Unknown is a valid outcome.

The system should prefer uncertainty over confident nonsense.

---

# 5. Last Participation Model

Do not implement dormancy using a single field called:

`last_used`

Instead create a composite concept:

# `last_participation_at`

This should represent the strongest credible evidence that the object meaningfully participated in HEXSEED.

Preserve the underlying evidence separately.

Where available, track:

```text
last_accessed_at
last_modified_at
last_executed_at
last_referenced_at
last_seen_at
```

Also track:

```text
last_participation_at
participation_basis
participation_confidence
dormancy_days
```

Example:

```text
Last Participation: 117 days ago
Basis: last successful script execution
Last Modified: 143 days ago
Last Referenced: no known references
Confidence: Strong
Status: Dormant Review
```

---

# 6. Do Not Trust Filesystem Last Access Alone

Filesystem access time must not be treated as authoritative evidence of user activity.

Reasons include:

* operating systems may suppress or delay access-time updates
* indexing can touch files
* antivirus can touch files
* scanners can touch files
* backup tools can touch files
* merely reading metadata may affect evidence depending on platform/configuration

Therefore:

# `last_accessed_at` is one signal, not the verdict.

Prefer stronger participation evidence when available.

---

# 7. Participation Evidence Hierarchy

Suggested relative strength:

## Strong evidence

* known execution
* known program launch
* known script invocation
* active dependency/reference
* configuration explicitly points to the object
* successful task execution using the object

## Moderate evidence

* recent meaningful modification
* project manifest reference
* active shortcut/reference
* known application association
* version metadata indicating current use

## Weak evidence

* filesystem access time
* scan observation
* directory listing
* indexing activity

The final confidence level should reflect evidence quality.

---

# 8. Dormancy Thresholds

Thresholds should be configurable.

Suggested starting defaults only:

## Operational infrastructure

`90 days`

## Transient/residue

Possible shorter review threshold:

`30-60 days`

## Project material

Do not apply a simple automatic dormancy threshold.

Project material should require additional contextual evidence.

## Protected/canonical

No age-based dormancy recommendation.

These defaults must not become hard-coded truth.

---

# 9. Dormancy Is Not a Verdict

Moonstone should never report:

> "This hasn't been used in 90 days. Delete it."

Instead:

> "I have found no evidence this has participated in HEXSEED for 117 days."

Then provide:

* what it is
* where it is
* what evidence exists
* what evidence is missing
* known dependents
* known references
* possible replacement/superseding item
* lifecycle classification
* confidence
* recommended review action

---

# 10. Redundancy Intelligence

Redundancy analysis should distinguish different phenomena.

Do not flatten all duplication into:

`DUPLICATE`

Differentiate at least:

## IDENTICAL DUPLICATE

Same content/hash.

Possible recommendation:

Review consolidation.

---

## VERSION VARIANT

Related files but materially different.

Examples:

* `_v01`
* `_v02`
* `final`
* `final_final`
* working iterations

Do not auto-remove.

Try to identify likely version lineage.

---

## SUPERSEDED

Strong evidence that a newer implementation replaced an older one.

Possible evidence:

* newer script imports/replaces old script
* old utility no longer referenced
* explicit migration comments
* known replacement path
* version chronology
* active config references only new implementation

Recommendation:

Review archival/quarantine.

---

## FUNCTIONAL REDUNDANCY

Different files/scripts implement substantially the same function.

This requires semantic/code-level analysis.

Examples:

* two PNG converters
* two duplicate finders
* two path-normalization scripts
* old and new scanners

Do not automatically choose a winner.

Report:

* overlap
* meaningful differences
* dependencies
* active references
* relative recency
* likely canonical candidate
* confidence

---

## INTENTIONAL DUPLICATION

Some duplicates are legitimate.

Examples:

* backups
* templates
* mirrored deployment copies
* canonical exports
* application-required copies

Moonstone should be capable of saying:

`Duplicate detected, but likely intentional.`

---

# 11. Project Asset Discernment

Project assets require special restraint.

For assets, ask:

1. Does it belong to a known project?
2. Is it located inside that project's accepted structure?
3. Is it referenced by a project file, configuration, documentation, or implementation?
4. Is it canonical?
5. Is there a newer apparent successor?
6. Is it identical to another file?
7. Is it clearly temporary output?
8. Is it part of an intentional archive?
9. Is it being kept as historical/reference material?

Only then determine whether review is justified.

Example:

```text
heartstone_character_sheet_v01.png
Last Participation: 286 days
Project: CareBloomOS
Classification: Project Material
Newer version detected: v04
Referenced by active configuration: No
Canonical status: No
Recommendation: Review as superseded project material
Confidence: Strong
```

Versus:

```text
moonstone_original_reference.png
Last Participation: 412 days
Project: CareBloomOS
Classification: Protected / Canonical Reference
Canonical reference: Yes
Recommendation: Keep
Dormancy review: Not applicable
```

---

# 12. Placement Congruence

Moonstone should eventually detect cross-project placement issues.

Example:

```text
R:\WelfareWitchcraft\Assets\cloverstone_badge.png
```

If classification strongly identifies this as CareBloomOS material:

Return:

```text
Finding: Placement Drift
Current ecosystem: Welfare Witchcraft
Likely ecosystem: CareBloomOS
Confidence: Strong
Recommended action: Review Route
```

Do not move automatically.

After approved routing, Cloverstone may handle the final local naming and placement.

---

# 13. Automation Congruence

Moonstone should be capable of reasoning about hidden operational behavior.

Relevant targets may include:

* PowerShell scripts
* scheduled tasks
* startup entries
* watchers
* background helpers
* repeated execution
* scripts firing unexpectedly
* scripts running from surprising paths
* orphaned scheduled tasks
* automation pointing at missing resources

Possible findings:

* EXPECTED
* UNEXPECTED
* ORPHANED
* DUPLICATE AUTOMATION
* STALE AUTOMATION
* PATH DRIFT
* REQUIRES REVIEW

Do not terminate processes or disable automation automatically.

Observation first.

---

# 14. Dependency Awareness

Before recommending archival, quarantine, relocation, or removal:

Check known dependencies wherever possible.

Mini ARK already contains dependency registration/scanning concepts.

Use that existing architecture rather than inventing a parallel system.

An object with active dependents should not receive a casual cleanup recommendation.

Possible status:

`DORMANT APPEARANCE / ACTIVE DEPENDENCY`

That distinction matters.

---

# 15. Confidence Model

Every significant Moonstone finding should have a confidence level.

Suggested values:

```text
Confirmed
Strongly_Inferred
Tentative
Unknown
```

This aligns well with Mini ARK's existing classification language.

Do not convert weak evidence into confident statements.

---

# 16. Risk Model

Suggested risk levels:

```text
informational
low
moderate
high
critical
```

Risk should describe consequence of acting incorrectly, not how spooky the finding looks.

A 300-day-old canonical asset may be:

`informational`

A dormant scheduled task pointing to an unexpected executable may be:

`high`

---

# 17. Recommended Actions

Moonstone may recommend actions such as:

```text
KEEP
IGNORE
REVIEW
COMPARE
ROUTE
ARCHIVE
QUARANTINE
INVESTIGATE
RECLASSIFY
CLEANSE
```

`CLEANSE` is CareBloom-facing language.

Internally it must resolve to an explicit concrete filesystem/system operation.

Never allow poetic language to conceal what the computer will actually do.

Example:

```text
UI action: Cleanse
Actual proposed operation: quarantine 4 files
Execution: requires explicit approval
Undo: available
```

---

# 18. No Surprise Cleanup

Moonstone must remain review-first.

Never automatically:

* delete
* uninstall
* move
* rename
* disable
* terminate
* quarantine
* merge conflicting files
* resolve version conflicts
* purge dormant material

Detection produces findings.

Findings may produce proposals.

Proposals require review.

---

# 19. Structured Result Contract

Design Moonstone findings so Codex can later wire them into Hex Drive without scraping terminal prose.

Prefer structured JSON or equivalent.

Suggested shape:

```json
{
  "owner": "moonstone",
  "domain": "congruence",
  "finding_type": "dormancy",
  "subject_type": "script",
  "path": "...",
  "classification": "operational_infrastructure",
  "status": "dormant_review",
  "last_participation_at": "...",
  "participation_basis": "...",
  "dormancy_days": 117,
  "confidence": "Strongly_Inferred",
  "risk": "low",
  "references": [],
  "dependents": [],
  "superseded_by": null,
  "reason": "...",
  "recommended_action": "REVIEW",
  "approval_required": true,
  "preview_available": true,
  "undo_available": true
}
```

Exact schema may evolve.

Keep field names predictable.

---

# 20. Hex Drive Presentation Needs

The future Moonstone Hex Drive UI will likely group findings into five sectors:

## Placement Drift

Does this belong here?

## Identity Drift

Does recorded state match reality?

## Redundancy

Why are there multiple versions/instances of this?

## Dormancy / Residue

Does this still participate?

## Automation Congruence

Is hidden behavior operating as intended?

Design outputs so they can be sorted naturally into these categories.

---

# 21. Moonstone Behavior Philosophy

Moonstone is not the computer janitor.

She is the system's **discernment layer**.

She notices:

* drift
* absence
* contradiction
* residue
* forgotten systems
* unexpected relationships
* things no longer participating
* things occupying spaces they no longer belong in

But observation does not grant permission to control.

Her behavior should embody:

> **Perceive without possessing.
> Prepare without panicking.
> Protect without controlling.**

Moonstone's wider CareBloom canon explicitly treats her as the hidden-care counterpart: she detects unseen systems and prepares for harm without turning perception into omnipotent responsibility.

---

# 22. Important Behavioral Examples

## Example A: Old project asset

A PNG has not been opened in 250 days.

It is still stored correctly inside CareBloomOS.

It has no obvious replacement.

Result:

```text
Classification: Project Material
Dormancy: Not actionable
Status: Inactive Reference
Recommendation: Keep
```

Do not bother the user merely because it is old.

---

## Example B: Old script

A PowerShell converter has not executed in 180 days.

No config references it.

A newer Python implementation performs the same function.

Result:

```text
Classification: Operational Infrastructure
Finding: Dormancy + Functional Redundancy
Superseded candidate detected
Confidence: Strong
Recommendation: Review for quarantine
```

---

## Example C: Empty folder

An empty project folder exists as scaffolding for future assets.

Result:

Moonstone may observe it.

But the lifecycle decision primarily belongs to Cloverstone's Empty Growth workflow.

Do not treat emptiness as Moonstone corruption.

---

## Example D: Misplaced asset

CareBloom asset inside Welfare Witchcraft.

Result:

```text
Finding: Placement Drift
Confidence: Strong
Recommendation: Review Route
```

After approved relocation:

handoff to Cloverstone.

---

## Example E: Old canonical document

Canonical dossier untouched for 500 days.

Result:

```text
Classification: Protected / Canonical
Dormancy evaluation: Exempt
Recommendation: Keep
```

Age is irrelevant.

---

## Example F: Scheduled task

A scheduled task still executes weekly but points to a nonexistent script.

Result:

```text
Finding: Automation Congruence Failure
Status: Orphaned Automation
Risk: Moderate
Recommendation: Investigate
```

It is not dormant.

It is active and wrong.

That distinction is precisely why Moonstone exists.

---

# 23. Deliverables

Please produce:

## A. Dormancy engine

Implement classification-aware dormancy analysis.

## B. Participation model

Implement or scaffold:

* last participation
* evidence provenance
* confidence
* dormancy age

## C. Redundancy intelligence

Differentiate:

* identical duplicate
* version variant
* superseded
* functional redundancy
* intentional duplication

## D. Lifecycle classification

Implement the five lifecycle classes:

* protected/canonical
* project material
* operational infrastructure
* transient/residue
* unknown

## E. Structured findings

Produce deterministic machine-readable output suitable for Mini ARK and future Rainmeter/CareBloomOS consumption.

## F. Tests

Include cases proving that:

* old asset != automatic dormancy problem
* old script may become dormancy review
* canonical material is protected
* unknown content remains unknown
* dependent content is not casually removed
* duplicate != automatically redundant
* superseded != automatically deleted
* misplaced content generates route proposal
* active-but-broken automation is not mistaken for dormant
* no destructive action occurs without approval

## G. Integration notes for Codex

Document:

* modules created
* interfaces exposed
* database/schema changes
* configuration options
* thresholds
* commands/functions Codex should call
* output schema
* known limitations
* remaining implementation gaps

Codex will later perform the wider script census and connect these capabilities to Moonstone Hex Drive and Cloverstone Script Garden.

Make the handoff easy to consume.

---

# 24. Final Governing Rule

Moonstone does not ask:

> **"How old is this?"**

She asks:

# **"What is this, what role is it supposed to play, and is there evidence it still participates in that role?"**

Only after answering those questions may age become meaningful.

Build the system accordingly.
