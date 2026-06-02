# Archive Production Rulebook v0

Date: 2026-05-30

Source reports:

- `Archive Production Rulebook for a Rights-Aware Research Gateway to Modern Graphic Design History.docx`
- `Surface Taxonomy Rulebook for a Rights-Aware Graphic Design History Archive.docx`
- `Rights-Aware Archive Box Interface Framework for Modern Graphic Design History.docx`

## Purpose

This rulebook defines how captured material becomes part of the archive system.

The project is not a course, gallery, textbook, or local image repository. It is a rights-aware archive index and research framework. It captures source evidence, preserves provenance, assigns image states, places records into folder aggregations, and generates archive surfaces only when enough information exists.

## Governing Rules

1. Index and link rather than possess.
2. Preserve raw source payloads before normalization.
3. Treat captured rows as production candidates, not final evidence.
4. Keep source metadata, normalized metadata, rights decisions, and classification decisions separate.
5. Make fallback, proposed, and unassigned states visible rather than hiding them.
6. Time is a sorting axis, not a container.
7. Folder type never changes record layout.
8. Image state controls image presence, not page size.

## Production Workflow

```text
capture batch
-> preserve raw source payload
-> create capture row
-> candidate pool
-> duplicate / source-locator check
-> IMG00-IMG04 evaluation
-> folder/cell assignment
-> source review
-> rights review
-> completeness scoring
-> source record draft
-> normalized entity / relation creation
-> publication eligibility gate
-> generated surface
```

## Record States

| State | Meaning | Public visibility |
|---|---|---|
| Raw capture | Unreviewed source payload, response, headers, request, query, and parser context. | No |
| Capture row | Parsed production candidate derived from raw capture. | Usually no, but searchable internally |
| Candidate pool item | Capture row awaiting assignment/review. | No |
| Source record draft | Candidate with stable source locator, citation seed, provisional type, and provisional IMG state. | Sometimes, marked as candidate |
| Source record | Reviewed source-level record with citation, source link, rights note, and provenance. | Yes if eligible |
| Normalized entity | Local assertion layer for person, institution, object, place, movement, medium, text, or theme. | Yes if supported |
| Main sheet | Published record surface above completeness threshold. | Yes |
| Card | Public compact record below main sheet threshold but still useful. | Yes |
| Fallback stub | Minimal public anchor for incomplete but historically relevant material. | Yes |
| Proposed cell item | Evidence that a new Region/Theme/Medium/Movement folder may be needed. | Yes, marked proposed |
| Unassigned research item | Valid or promising row that cannot yet be responsibly placed. | Yes |
| Deprecated row | Retained tombstone for superseded, merged, withdrawn, or erroneous records. | Usually yes |

## Promotion Rules

| Transition | Allow when | Block when |
|---|---|---|
| Raw capture -> capture row | Payload is preserved and at least one candidate resource can be parsed. | No stored payload, no source context, parser detached from raw evidence. |
| Capture row -> source record draft | Stable landing page or item URL, provider/source identifier or reliable local key, recognizable label, raw pointer. | Search snippet only, unstable locator, unresolved duplicate, navigation shell. |
| Source record draft -> source record | Source review confirms object/resource, citation is complete, rights disposition exists, provenance is traceable. | Rights unknown, source ambiguity unresolved, provider attribution missing, citation insufficient. |
| Source record -> main sheet | Completeness score >= 75, source-reading gate passes, and all essential gates pass. | Essential identity/source/rights gates fail, or the record is only metadata/table evidence. |
| Candidate/draft -> card | Enough identity/date/source exists for folder placement, but main sheet threshold is not met. | Too little evidence to cite or sort. |
| Candidate/draft -> fallback stub | Historically relevant, citable, but cannot support card or sheet. | No resolvable source/citation and no defensible label. |
| Candidate/draft -> proposed cell | Repeated evidence reveals a framework gap and existing cells would distort the material. | Based on one vague record or duplicates an existing cell. |
| Source record -> unassigned item | Source is valid but no responsible cell placement exists. | Team is forcing it into a famous movement to avoid emptiness. |
| Any state -> deprecated | Superseded, merged, withdrawn, or materially wrong. | Silent overwrite or deletion. |

## IMG Decision Matrix

| IMG | Assign when | User must see |
|---|---|---|
| IMG00 | Image frame is useful, but image display is too risky or unsupported. Default for unresolved image rights. | Empty image frame, source link, reason image is not shown, rights note. |
| IMG01 | Controlled thumbnail is plausible under source-specific constraints. | Thumbnail, source credit, thumbnail-specific note, review status. |
| IMG02 | Source-hosted viewer, IIIF, or embed is available without local copying. | Source-hosted label, required credit/rights text, source context link. |
| IMG03 | Explicit open/reusable image evidence exists, such as CC0, Public Domain Mark, or provider open-access statement tied to the image. | Exact rights basis, source link, access date, attribution caveats. |
| IMG04 | No image frame should be shown because the surface is textual, bibliographic, authority-like, or appendix-like. | Citation, source link, authority links where relevant. |

Image state is independent of sheet tier, image size, and folder type.

## Folder and Cell Assignment

The project has four primary public folder types:

- Region
- Theme
- Medium
- Movement

Folders are aggregation views. They do not own records and do not alter record layout.

Assignment should begin with low-interpretation anchors:

- date/date span;
- place/region;
- language/script;
- object/resource type;
- medium/technology;
- provider/source;
- bibliographic/resource class.

Then add interpretive placements:

| Assignment type | Meaning | Use rule |
|---|---|---|
| Exact match | Source or scholarship explicitly supports the placement. | Use when source names the movement/theme/region/medium or a reliable reference supports it. |
| Contextual match | Record belongs near the cell but is not proof of membership. | Mark visibly; do not collapse into exact membership. |
| Proposed cell | Repeated evidence suggests a missing folder/cell. | Requires examples, scope note, date span, and review. |
| Unassigned | Source is valid but cannot yet be placed responsibly. | Keep visible as research-needed. |

## Completeness Gate

A main sheet requires:

- stable identity;
- source URL or source locator;
- source/provider name;
- title or label;
- date or date_text;
- record family/category;
- rights state;
- IMG state;
- at least one folder assignment or proposed/unassigned state;
- citation seed or full citation.
- enough captured source-reading material to make the page readable as an
  archive record, not only as a table.

Recommended score:

| Area | Points |
|---|---:|
| Identity: title, internal ID, source ID, record type | 20 |
| Source and citation: source URL, provider, access date, citation | 20 |
| Date and place | 15 |
| People / institution | 10 |
| Classification: folder memberships, medium, theme, movement, region | 15 |
| Rights and IMG state | 10 |
| Description / notes | 10 |

## Reading Gate

The six specification tables are the evidence layer. They must not become the
whole public page.

Use these thresholds for publication:

| Reading evidence | Surface outcome |
|---|---|
| 180+ characters of captured description, source notes, subjects, or contextual text | Main sheet eligible if other gates pass. |
| 80-179 characters plus strong image/source evidence | Main sheet eligible but flagged as thin text. |
| Less than 80 characters and no contextual source | Card, compound child, fallback stub, or internal capture row. |
| Textual/bibliographic/contextual source with strong citation | `IMG04` text sheet. |

`IMG04` should mean a real text/authority/bibliographic page, not a failed image
parse. If the source describes a visual object but the image cannot be displayed,
use `IMG00` and render an empty image frame with a rights/source explanation.

Extended rule:

- image state, parser status, and text eligibility are separate decisions;
- a visual source with parser failure remains internally diagnosable and should
  not be silently converted to `IMG04`;
- `IMG04` is only for genuinely text, authority, bibliographic, appendix, or
  context-led pages;
- editor-authored summaries, context notes, folder introductions, classification
  rationales, uncertainty notes, and empty-frame notes may be added, but they
  must point back to source evidence;
- self-made or generated substitute images should not stand in for missing
  archival images.

See `IMAGE_AND_TEXT_ENRICHMENT_RULES_v0.md` for the current operational version
of these rules.

Surface outcome:

- `75-100`: main sheet if source-reading evidence and all gates pass.
- `55-74`: support packet: appendix + text-page treatment, not a full main
  sheet. These records may later upgrade after description, rights, relation,
  or source evidence improves.
- `40-54`: merge candidate / support packet. Prefer attaching to a stronger
  main sheet, compound group, source dossier, or folder-level text packet
  instead of making it stand alone.
- `20-39`: card.
- `<20`: bookmark candidate or internal-only capture row.

The threshold is intentionally stricter than the first visual-verification
pass. A strong image does not by itself make a main sheet. Thin visual records
can remain visible as support packets, but their research value must be carried
by text pages, appendices, group context, or source-return evidence.

## Compound Sheets

Use a compound sheet when several weak records belong together more truthfully than they stand alone:

- poster series;
- periodical issue plus pages;
- exhibition or event group;
- source collection;
- design system/manual section;
- multiple fallback rows about the same object or movement gap.

Compound main sheet contains shared identity, shared source logic, chronological span, and child card/appendix entries.

## Review Gates

| Gate | Can script assist? | Human review required? |
|---|---|---|
| Source fetch and raw preservation | Yes | Only on source pattern changes |
| Field parsing | Yes | For ambiguous fields |
| IMG candidate detection | Yes | For IMG01/02/03 promotion |
| Source review | Partially | Yes for new provider/source pattern |
| Rights review | Partially | Yes for unclear, restricted, or non-open cases |
| Cell assignment | Suggest only | Yes for interpretive placement |
| Proposed cell acceptance | No | Yes |
| Main sheet eligibility | Yes | Yes before publication |

## Public Display Rules

- Main sheets, cards, fallback stubs, proposed cell items, and unassigned items can appear in folders.
- Folder interiors are sorted chronologically by default.
- Undated records appear in an `undated / date under review` group.
- Fallback and unassigned items must not disappear, because weak archival visibility is part of the project’s research integrity.
- Users must see source return links and rights state on every public surface.

## Anti-Patterns

- Treating capture rows as published archive evidence.
- Making time into a container rather than a sorting axis.
- Making folder type alter record layout.
- Hiding incomplete records.
- Promoting image display because an image URL exists.
- Collapsing contextual match into exact historical membership.
- Creating a proposed cell from a single weak row.
- Deleting or silently overwriting deprecated records.
