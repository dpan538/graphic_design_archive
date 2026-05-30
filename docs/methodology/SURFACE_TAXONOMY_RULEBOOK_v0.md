# Surface Taxonomy Rulebook v0

Date: 2026-05-30

Source report:

- `Surface Taxonomy Rulebook for a Rights-Aware Graphic Design History Archive.docx`

## Purpose

This document defines which archive surfaces the system generates.

The project should use a small set of stable surface families. It should not make every movement, theme, or folder a bespoke page. Surface choice is determined by record state, completeness, content volume, rights/image state, and publication mode.

## Surface Families

1. Navigation surfaces
2. Record surfaces
3. Appendix and evidence surfaces
4. Registration and orientation surfaces
5. Search and excerpt surfaces

## Required Public Surface Types

| Surface | Purpose | Public? | Generated from | Chronological? | IMG |
|---|---|---:|---|---:|---|
| Archive box overview | Global entry to the archive box and four folder types. | Yes | folder counts, global stats | No | IMG04/N/A |
| Folder cover | Overview for one Region/Theme/Medium/Movement folder. | Yes | folder aggregation | No | IMG04/N/A |
| Folder index | Chronological listing of all folder members. | Yes | folder membership rows | Yes | Member-specific |
| Main loose-leaf sheet | Primary public record surface above completeness threshold. | Yes | source/entity/surface data | Yes | IMG00-IMG04 |
| Continuation sheet | Overflow page attached to a main sheet. | Yes | parent sheet data | Inherits parent | Usually IMG04 |
| Text-only sheet | Main sheet variant for bibliographic/text/authority records. | Yes | source/entity data | Yes | IMG04 |
| Image-rights placeholder sheet | Main sheet variant with empty image frame. | Yes | source/entity data | Yes | IMG00 |
| Group / compound sheet | One intellectual unit made from related records. | Yes | grouped source records/cards | Yes | IMG00-IMG04 |
| Card | Compact record below main sheet threshold. | Yes | candidate/source data | Yes | IMG00-IMG04 |
| Fallback stub | Minimal citable public anchor. | Yes | fallback/source stub data | Yes if dated | IMG04 or IMG00 |
| Unassigned research item | Visible research-needed item. | Yes | unassigned candidate/source row | Yes if dated | IMG00-IMG04 |
| Proposed cell item | Public proposal for a missing folder/cell. | Yes | proposed cell data | Usually | IMG04 |
| Source dossier | Evidence bundle when source trail is complex. | Public summary | source relations | Inherits parent | IMG00-IMG04 |
| Citation appendix | Structured citation list. | Yes | citations | Inherits parent | IMG04 |
| Relation appendix | Expanded relation table. | Yes | relation assertions | Inherits parent | IMG04 |
| Rights appendix | Expanded rights evidence and decision note. | Public summary | rights review | Inherits parent | IMG04 |
| Registration card | Classification/filing log. | Yes or internal summary | assignment/review events | Event order | IMG04 |
| Bookmark / reading guide | Explains archive states and reading rules. | Yes | authored notes | No | IMG04 |
| Search result strip | Compact search result. | Yes | search index | Relevance, optional date | Mini state badge |
| Chronological divider | Separates years/decades within folder. | Yes | folder index buckets | Yes | N/A |

## MVP Surface Set

For the first usable frontend, generate:

- Archive box overview
- Four folder-type entry views: Region, Theme, Medium, Movement
- Folder cover
- Folder index
- Main loose-leaf sheet
- Continuation/text sheet
- Card
- Fallback stub
- Unassigned research item
- Proposed cell item
- Rights stamp/rights summary module
- Search placeholder and search result strip placeholder

Appendix surfaces may initially be rendered as tabs/sections inside main sheet pages, then split into separate routes later.

## Later Surface Set

Add later:

- Source dossier
- Citation appendix
- Relation appendix
- Rights appendix
- Registration card
- Bookmark/reading guide library
- Printable/PDF sheet exports
- Release manifest
- Public changelog/tombstone page

## Surface Eligibility

| Record condition | Surface |
|---|---|
| Completeness >= 60 and gates pass | Main sheet |
| Completeness >= 60, no image frame by nature | Text-only sheet |
| Completeness >= 60, image risky | Image-rights placeholder sheet |
| Several weak records form one intellectual unit | Group / compound sheet |
| 45-59 completeness | Card |
| 25-44 completeness | Fallback stub |
| Valid but cannot be assigned responsibly | Unassigned research item |
| Repeated cluster suggests missing folder/cell | Proposed cell item |
| Long source trail or relation density | Appendix/dossier |

## Folder Behavior

The four public folder types are:

- Region
- Theme
- Medium
- Movement

Folder behavior:

- Folders are aggregation/filter views.
- Folders do not own records.
- Folders do not change record layout.
- A record may appear in multiple folders.
- Folder color belongs to folder type, not record content.
- Every folder index is chronologically sorted by default.
- Folder members may include main sheets, cards, fallback stubs, proposed cell items, and unassigned items.

## Chronology Rules

Default order inside every folder:

1. exact date;
2. date range start;
3. approximate date;
4. contextual date;
5. source/capture date if no historical date exists;
6. undated group.

Chronological dividers should be navigation devices, not historical containers.

## Search Behavior

Search should include:

- main sheets;
- cards;
- fallback stubs;
- proposed cell items;
- unassigned items;
- folder covers;
- source registry entries;
- citation/source records.

Search result rank should prefer:

1. published main sheets;
2. cards;
3. folder covers;
4. proposed cell items;
5. fallback stubs;
6. unassigned research items;
7. appendices.

WebLLM search is a later layer. The surface taxonomy should work without it.

## Public vs Internal

Public-facing:

- archive box overview;
- folder covers/indexes;
- sheets;
- cards;
- fallback stubs;
- proposed cell items;
- unassigned research items;
- public rights/citation summaries.

Internal or partially public:

- raw captures;
- source review notes;
- full rights/legal notes;
- parser logs;
- assignment confidence internals;
- build manifests;
- release checksums.

## Output Formats

| Surface | HTML route | JSON payload | CSV table | Printable |
|---|---:|---:|---:|---:|
| Archive box overview | Yes | Yes | No | Optional |
| Folder cover/index | Yes | Yes | Yes | Optional |
| Main sheet | Yes | Yes | No | Yes later |
| Card | Yes/inline | Yes | Yes | Optional |
| Fallback stub | Yes/inline | Yes | Yes | Optional |
| Proposed/unassigned item | Yes/inline | Yes | Yes | Optional |
| Appendix | Yes | Yes | No | Yes later |
| Registration card | Yes | Yes | Yes | Optional |
| Search result strip | Inline | Yes | No | No |

## Anti-Patterns

- Creating bespoke layouts per movement.
- Turning folder color into record decoration.
- Treating timeline as a top-level container.
- Hiding incomplete records.
- Hiding rights behind a collapsed footer.
- Making a gallery wall.
- Letting source image availability decide publication state.
- Making every appendix a separate record type.
